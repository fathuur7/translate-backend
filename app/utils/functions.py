import shutil
from datetime import timedelta
from fastapi import UploadFile
import moviepy as mp
import os
import time
from typing import Optional, List
import uuid
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

def configure_cloudinary(*args, **kwargs):
    """
    NO-OP replacement for configure_cloudinary.
    Aplikasi awalnya menggunakan Cloudinary; untuk mempercepat dan
    menghindari panggilan jaringan, kita simpan file secara lokal.
    Fungsi ini dipertahankan agar pemanggilan di kode lain tidak gagal.
    """
    print("Cloudinary disabled — using local storage for uploads.")


def upload_to_cloudinary(file_path: str, resource_type: str = "auto", 
                         folder: str = "videos") -> Optional[dict]:
    """
    Replacement for Cloudinary upload: simpan file ke folder lokal
    `app/static/uploads/<folder>/` dan kembalikan struktur mirip hasil
    Cloudinary dengan key 'secure_url'.

    Returns dict atau None jika gagal.
    """
    if not os.path.exists(file_path):
        print(f"Error: File tidak ditemukan: {file_path}")
        return None

    try:
        # Tentukan direktori tujuan di dalam app/static/uploads
        base_static = Path(__file__).resolve().parent / "static" / "uploads"
        target_dir = base_static / folder
        os.makedirs(target_dir, exist_ok=True)

        # Gunakan UUID agar nama unik dan aman
        src_name = Path(file_path).name
        unique_name = f"{uuid.uuid4().hex}_{src_name}"
        dest_path = target_dir / unique_name

        print(f"Saving {file_path} -> {dest_path}")
        shutil.copyfile(file_path, dest_path)

        # Kembalikan URL relatif yang dapat di-mount di FastAPI sebagai /static
        secure_url = f"/static/uploads/{folder}/{unique_name}"
        result = {
            "secure_url": secure_url,
            "public_id": unique_name,
            "original_filename": src_name,
            "local_path": str(dest_path)
        }

        print(f"Saved locally. URL: {secure_url}")
        return result

    except Exception as e:
        print(f"Error saat menyimpan file lokal: {e}")
        return None


def save_upload_file(upload_file: UploadFile, destination: str) -> bool:
    """
    Menyimpan file yang diunggah ke path tujuan.
    Returns: True jika berhasil, False jika gagal.
    """
    try:
        # Pastikan direktori tujuan ada
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        
        with open(destination, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
        
        print(f"File berhasil disimpan ke: {destination}")
        return True
        
    except Exception as e:
        print(f"Error saat menyimpan file: {e}")
        return False
        
    finally:
        upload_file.file.close()


def extract_audio(video_path: str, audio_path: str) -> bool:
    """
    Mengekstrak audio dari video, atau langsung menyalin jika input sudah berupa audio.
    Returns: True jika berhasil, False jika gagal.
    """
    # Validasi file input
    if not os.path.exists(video_path):
        print(f"Error: File tidak ditemukan: {video_path}")
        return False
    
    if os.path.getsize(video_path) == 0:
        print(f"Error: File kosong: {video_path}")
        return False
    
    print(f"Mengekstrak audio dari {video_path}...")
    
    try:
        # Deteksi ekstensi file
        ext = os.path.splitext(video_path)[1].lower()

        # Daftar format audio yang didukung
        audio_formats = [".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".wma"]
        
        if ext in audio_formats:
            print("File sudah berupa audio, langsung digunakan tanpa ekstraksi.")
            shutil.copy(video_path, audio_path)
            
            # Verifikasi file hasil copy
            if not os.path.exists(audio_path):
                print("Error: Gagal menyalin file audio.")
                return False
                
            print(f"File audio berhasil disalin ke: {audio_path}")
            return True

        # Kalau file video → ekstrak audio
        print("Mengekstrak audio dari file video...")
        video = None
        try:
            video = mp.VideoFileClip(video_path)
            
            # Cek apakah video memiliki audio
            if video.audio is None:
                print("Error: Video tidak memiliki track audio.")
                return False
            
            # Ekstrak audio
            video.audio.write_audiofile(
                audio_path, 
                logger=None,
                codec='pcm_s16le',
                fps=16000, 
                nbytes=2,   
                bitrate='16k'
            )
            print(f"Audio berhasil diekstrak ke: {audio_path}")
            return True
            
        finally:
            # Pastikan resource video dibersihkan
            if video is not None:
                video.close()

    except Exception as e:
        print(f"Error saat ekstrak audio: {e}")
        return False


def transcribe_audio(model, audio_path: str) -> dict:
    """
    Mentranskripsi file audio menggunakan model Whisper.
    Returns: Dictionary hasil transkripsi atau None jika gagal.
    """
    # Validasi file audio
    if not os.path.exists(audio_path):
        print(f"Error: File audio tidak ditemukan: {audio_path}")
        return None
    
    if os.path.getsize(audio_path) == 0:
        print(f"Error: File audio kosong: {audio_path}")
        return None
    
    print("Melakukan transkripsi audio...")
    
    try:
        # fp16=False direkomendasikan untuk kompatibilitas CPU
        result = model.transcribe(
            audio_path, 
            fp16=False,
            language=None,  # Auto-detect language
            verbose=False
        )
        
        # Validasi hasil transkripsi
        if not result:
            print("Error: Model tidak mengembalikan hasil.")
            return None
        
        if 'segments' not in result or not result['segments']:
            print("Warning: Transkripsi tidak menghasilkan segmen.")
        
        if 'text' not in result or not result['text'].strip():
            print("Warning: Transkripsi tidak menghasilkan teks.")
        
        print(f"Transkripsi selesai. Ditemukan {len(result.get('segments', []))} segmen.")
        return result
        
    except FileNotFoundError as e:
        print(f"❌ Error: FFmpeg tidak ditemukan!")
        print(f"   Whisper membutuhkan FFmpeg untuk memproses audio.")
        print(f"   Solusi:")
        print(f"   1. Install FFmpeg: https://ffmpeg.org/download.html")
        print(f"   2. Atau gunakan Chocolatey: choco install ffmpeg")
        print(f"   3. Restart terminal setelah install")
        print(f"   Technical error: {e}")
        return None
    except Exception as e:
        print(f"Error saat transkripsi: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return None


# In-memory cache untuk hasil terjemahan (per-segment)
_translation_cache = {}

def _get_text_hash(text: str, target_language: str) -> str:
    """Generate hash untuk cache key."""
    content = f"{text}_{target_language}"
    return hashlib.md5(content.encode()).hexdigest()


def _translate_text(translator, text: str, target_language: str, max_retries: int = 3) -> str:
    """
    Translate single text dengan caching menggunakan deep-translator (Python 3.13 compatible).
    """
    from deep_translator import GoogleTranslator
    
    # Validasi input
    if not text or not text.strip():
        return text
    
    if not target_language:
        return text
    
    # Check cache dulu
    cache_key = _get_text_hash(text, target_language)
    if cache_key in _translation_cache:
        return _translation_cache[cache_key]
    
    # Translate menggunakan deep-translator
    for attempt in range(max_retries):
        try:
            translated = GoogleTranslator(source='auto', target=target_language).translate(text.strip())
            
            if translated:
                # Simpan ke cache
                _translation_cache[cache_key] = translated
                return translated
            else:
                print(f"Warning: Terjemahan kosong untuk '{text[:50]}...'")
                return text
                
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # Exponential backoff: 2s, 4s, 6s
                print(f"Timeout/Error saat menerjemahkan (attempt {attempt+1}/{max_retries}). Retry dalam {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"Error saat menerjemahkan '{text[:50]}...' setelah {max_retries} percobaan: {e}")
                return text  # Return teks asli jika semua retry gagal
    
    return text


def _translate_batch(translator, texts: List[str], target_language: str, max_retries: int = 3) -> List[str]:
    """
    Translate multiple texts sekaligus (batch) untuk mengurangi network overhead.
    Menggunakan deep-translator (Python 3.13 compatible).
    """
    from deep_translator import GoogleTranslator
    
    if not texts or not target_language:
        return texts
    
    # Filter texts yang perlu ditranslate (check cache)
    results = []
    to_translate = []
    indices_to_translate = []
    
    for i, text in enumerate(texts):
        if not text or not text.strip():
            results.append(text)
            continue
        
        cache_key = _get_text_hash(text, target_language)
        if cache_key in _translation_cache:
            results.append(_translation_cache[cache_key])
        else:
            results.append(None)  # Placeholder
            to_translate.append(text.strip())
            indices_to_translate.append(i)
    
    # Jika semua sudah di cache, langsung return
    if not to_translate:
        return results
    
    # Translate batch menggunakan deep-translator (one by one, tapi dengan cache)
    # Note: deep-translator tidak support batch natively, jadi kita process satu-per-satu dengan cache
    for attempt in range(max_retries):
        try:
            print(f"📦 Batch translating {len(to_translate)} texts...")
            translator_instance = GoogleTranslator(source='auto', target=target_language)
            
            # Process each text
            for idx, text in enumerate(to_translate):
                original_idx = indices_to_translate[idx]
                
                try:
                    translated_text = translator_instance.translate(text)
                    if translated_text:
                        results[original_idx] = translated_text
                        # Cache it
                        cache_key = _get_text_hash(text, target_language)
                        _translation_cache[cache_key] = translated_text
                    else:
                        results[original_idx] = text
                except Exception as e:
                    print(f"⚠️  Failed to translate segment {idx}: {e}")
                    results[original_idx] = text
            
            print(f"✅ Batch translation completed!")
            return results
            
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                print(f"⚠️  Batch translation failed (attempt {attempt+1}/{max_retries}). Retry in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"❌ Batch translation failed after {max_retries} attempts: {e}")
                # Fallback: return original texts
                for idx in indices_to_translate:
                    if results[idx] is None:
                        results[idx] = texts[idx]
                return results
    
    return results


def _format_time(seconds: float) -> str:
    """
    Fungsi internal untuk memformat detik menjadi format waktu SRT.
    Format: HH:MM:SS,mmm
    """
    if seconds < 0:
        seconds = 0
    
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds_val = total_seconds % 60
    milliseconds = int((td.total_seconds() - total_seconds) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{seconds_val:02d},{milliseconds:03d}"


def create_srt_content(segments: list, translator_instance=None, translate_to: str = None) -> str:
    """
    Membuat konten file SRT sebagai sebuah string dari segmen transkripsi.
    OPTIMIZED: Menggunakan batch translation untuk performa lebih cepat.
    Uses deep-translator (Python 3.13 compatible).
    Returns: String konten SRT atau None jika gagal.
    """
    # Validasi input
    if not segments:
        print("Error: Tidak ada segmen untuk dibuat SRT.")
        return None
    
    # Note: translator_instance tidak lagi digunakan (deep-translator tidak perlu instance)
    # Translation akan dilakukan langsung di _translate_batch
    
    srt_lines = []
    
    try:
        # Validasi dan extract texts
        valid_segments = []
        for segment in segments:
            if not isinstance(segment, dict):
                continue
            if 'start' not in segment or 'end' not in segment or 'text' not in segment:
                continue
            if not segment['text'].strip():
                continue
            valid_segments.append(segment)
        
        if not valid_segments:
            print("Error: Tidak ada segmen valid.")
            return None
        
        # Jika perlu terjemahan, lakukan batch translation (LEBIH CEPAT!)
        translated_texts = None
        if translate_to:
            print(f"⚡ Using BATCH translation for {len(valid_segments)} segments to '{translate_to}'...")
            original_texts = [seg['text'].strip() for seg in valid_segments]
            start_time = time.time()
            translated_texts = _translate_batch(None, original_texts, translate_to)  # translator_instance not needed
            elapsed = time.time() - start_time
            print(f"✅ Batch translation completed in {elapsed:.2f}s (avg {elapsed/len(valid_segments):.3f}s per segment)")
        
        # Build SRT content
        for i, segment in enumerate(valid_segments, 1):
            start_time_str = _format_time(segment['start'])
            end_time_str = _format_time(segment['end'])
            
            # Gunakan hasil batch translation jika ada
            if translated_texts:
                text = translated_texts[i-1]
            else:
                text = segment['text'].strip()

            # Tambahkan ke SRT
            srt_lines.append(str(i))
            srt_lines.append(f"{start_time_str} --> {end_time_str}")
            srt_lines.append(text)
            srt_lines.append("")  # Baris kosong sebagai pemisah

        if not srt_lines:
            print("Error: Tidak ada konten SRT yang valid.")
            return None
        
        result = "\n".join(srt_lines)
        print(f"✅ Konten SRT berhasil dibuat. Total {len(valid_segments)} segmen.")
        return result
        
    except Exception as e:
        print(f"Error saat membuat konten SRT: {e}")
        return None