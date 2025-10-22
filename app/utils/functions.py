import shutil
from datetime import timedelta
from fastapi import UploadFile
import moviepy as mp
import os
import time
import cloudinary
import cloudinary.uploader
from typing import Optional

# Konfigurasi Cloudinary
def configure_cloudinary(cloud_name: str, api_key: str, api_secret: str):
    """
    Konfigurasi Cloudinary dengan credentials Anda.
    Panggil fungsi ini di awal aplikasi (main.py atau startup).
    """
    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
        secure=True
    )
    print("Cloudinary berhasil dikonfigurasi!")


def upload_to_cloudinary(file_path: str, resource_type: str = "auto", 
                         folder: str = "videos") -> Optional[dict]:
    """
    Upload file ke Cloudinary.
    
    Args:
        file_path: Path file lokal yang akan diupload
        resource_type: Tipe resource ('video', 'audio', 'image', 'raw', 'auto')
        folder: Folder di Cloudinary untuk menyimpan file
    
    Returns:
        Dictionary berisi informasi upload (url, public_id, dll) atau None jika gagal
    """
    if not os.path.exists(file_path):
        print(f"Error: File tidak ditemukan: {file_path}")
        return None
    
    try:
        print(f"Uploading {file_path} ke Cloudinary...")
        
        # Upload file
        result = cloudinary.uploader.upload(
            file_path,
            resource_type=resource_type,
            folder=folder,
            use_filename=True,
            unique_filename=True,
            overwrite=False
        )
        
        print(f"Upload berhasil! URL: {result.get('secure_url')}")
        return result
        
    except Exception as e:
        print(f"Error saat upload ke Cloudinary: {e}")
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
        
    except Exception as e:
        print(f"Error saat transkripsi: {e}")
        return None


def _translate_text(translator, text: str, target_language: str, max_retries: int = 3) -> str:
    # Validasi input
    if not text or not text.strip():
        return text
    
    if not target_language:
        return text

    
    for attempt in range(max_retries):
        try:
            translation = translator.translate(text.strip(), dest=target_language)
            
            if translation and translation.text:
                return translation.text
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
    Returns: String konten SRT atau None jika gagal.
    """
    # Validasi input
    if not segments:
        print("Error: Tidak ada segmen untuk dibuat SRT.")
        return None
    
    # Validasi translator jika perlu terjemahan
    if translate_to and not translator_instance:
        print("Warning: Diminta terjemahan tapi translator_instance tidak tersedia.")
        translate_to = None
    
    srt_lines = []
    
    try:
        for i, segment in enumerate(segments, 1):
            # Validasi struktur segment
            if not isinstance(segment, dict):
                print(f"Warning: Segment {i} bukan dictionary, dilewati.")
                continue
            
            if 'start' not in segment or 'end' not in segment or 'text' not in segment:
                print(f"Warning: Segment {i} tidak lengkap, dilewati.")
                continue
            
            start_time = _format_time(segment['start'])
            end_time = _format_time(segment['end'])
            text = segment['text'].strip()
            
            # Skip jika teks kosong
            if not text:
                print(f"Warning: Segment {i} memiliki teks kosong, dilewati.")
                continue

            # Terjemahkan jika diminta
            if translate_to and translator_instance:
                text = _translate_text(translator_instance, text, translate_to)

            # Tambahkan ke SRT
            srt_lines.append(str(i))
            srt_lines.append(f"{start_time} --> {end_time}")
            srt_lines.append(text)
            srt_lines.append("")  # Baris kosong sebagai pemisah

        if not srt_lines:
            print("Error: Tidak ada konten SRT yang valid.")
            return None
        
        result = "\n".join(srt_lines)
        print(f"Konten SRT berhasil dibuat. Total {len(segments)} segmen.")
        return result
        
    except Exception as e:
        print(f"Error saat membuat konten SRT: {e}")
        return None