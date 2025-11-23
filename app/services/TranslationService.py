import os
from faster_whisper import WhisperModel
from deep_translator import GoogleTranslator
from app.utils.functions import (
    extract_audio,
    transcribe_audio,
    create_srt_content,
    upload_to_cloudinary,
    # configure_cloudinary (disabled)
)
from app.utils.cache_manager import transcription_cache

class TranslationService:
    def __init__(self, whisper_model: str = None):
        """
        Initialize Translation Service using Faster-Whisper.
        
        Args:
            whisper_model: Model size untuk Whisper. Options:
                - "tiny" - Paling cepat, akurasi rendah (~1GB RAM, 32x faster)
                - "base" - Balance speed/accuracy (default)
                - "small" - Lebih akurat, lebih lambat
                - "medium" - High accuracy, slower
                - "large" - Best accuracy, very slow
        """
        # Gunakan environment variable atau default ke "base"
        model_name = whisper_model or os.getenv("WHISPER_MODEL", "base")
        
        print(f"⏳ Memuat model Faster-Whisper '{model_name}'... (Mungkin butuh beberapa saat)")
        
        # cpu_threads=4 untuk optimalisasi CPU
        self.model = WhisperModel(model_name, device="cpu", compute_type="int8", cpu_threads=4)
        
        # deep-translator doesn't need initialization, we'll use it directly in functions
        self.translator = None  # Not needed anymore
        
        # Cloudinary telah dinonaktifkan — upload sekarang disimpan lokal
        print(f"✅ Model Faster-Whisper '{model_name}' berhasil dimuat.")
        
        # Performance hint
        if model_name == "tiny":
            print("💡 Using 'tiny' model - FASTEST transcription, lower accuracy")
        elif model_name == "base":
            print("💡 Using 'base' model - Balanced speed & accuracy")
        elif model_name in ["small", "medium", "large"]:
            print(f"💡 Using '{model_name}' model - Higher accuracy, slower processing")

    def process_video(self, video_path: str, target_language: str = None) -> dict:
        """
        Mengoordinasikan alur kerja:
        1. Upload video ke Cloudinary
        2. Ekstrak audio
        3. Transkripsi
        4. Buat SRT asli
        5. Buat SRT terjemahan
        6. Upload SRT ke Cloudinary
        7. Simpan hasil di folder 'output/'
        """
        # 🗂️ Buat folder output di dalam project (kalau belum ada)
        output_dir = os.path.join(os.getcwd(), "output")
        os.makedirs(output_dir, exist_ok=True)

        # 🔊 Tentukan path audio dan hasil akhir
        filename_no_ext = os.path.splitext(os.path.basename(video_path))[0]
        audio_path = os.path.join(output_dir, f"{filename_no_ext}_audio.wav")
        srt_original_path = os.path.join(output_dir, f"{filename_no_ext}_original.srt")
        srt_translated_path = os.path.join(output_dir, f"{filename_no_ext}_{target_language}.srt")

        try:
            # 🔍 Check cache dulu
            cached_result = transcription_cache.get(video_path, target_language)
            if cached_result:
                print("⚡ Menggunakan hasil dari cache (skip processing)")
                return cached_result
            
            # 🎥 Upload video ke local storage
            print("Menyimpan video ke local storage...")
            video_upload_result = upload_to_cloudinary(
                file_path=video_path,
                resource_type="video",
                folder="videos"
            )
            
            video_url = None
            if video_upload_result:
                video_url = video_upload_result.get('secure_url')
                print(f"Video berhasil disimpan: {video_url}")
            else:
                print("Warning: Gagal menyimpan video")

            # 1️⃣ Ekstrak audio dari video ke folder output
            if not extract_audio(video_path, audio_path):
                print("Error: Gagal mengekstrak audio dari video.")
                return None

            # 2️⃣ Transkripsi audio
            transcription_result = transcribe_audio(self.model, audio_path)
            if not transcription_result or 'segments' not in transcription_result:
                print("Transkripsi tidak menghasilkan segmen.")
                return None

            # 3️⃣ Buat konten SRT asli (tanpa terjemahan)
            original_srt_content = create_srt_content(
                segments=transcription_result['segments'],
                translator_instance=None,  # Tidak perlu translator untuk original
                translate_to=None  # Original language (no translation)
            )

            # Simpan ke file
            with open(srt_original_path, "w", encoding="utf-8") as f:
                f.write(original_srt_content)

            # Upload SRT original ke Cloudinary
            print("Mengupload SRT original ke Cloudinary...")
            srt_original_upload = upload_to_cloudinary(
                file_path=srt_original_path,
                resource_type="raw",
                folder="subtitles"
            )
            
            srt_original_url = None
            if srt_original_upload:
                srt_original_url = srt_original_upload.get('secure_url')
                print(f"SRT original berhasil diupload: {srt_original_url}")

            # 4️⃣ Terjemahan (opsional)
            translated_srt_content = None
            srt_translated_url = None
            
            if target_language:
                print(f"🌐 Menerjemahkan ke bahasa '{target_language}'...")
                translated_srt_content = create_srt_content(
                    segments=transcription_result['segments'],
                    translator_instance=None,  # deep-translator tidak perlu instance
                    translate_to=target_language
                )

                with open(srt_translated_path, "w", encoding="utf-8") as f:
                    f.write(translated_srt_content)

                # Upload SRT terjemahan ke Cloudinary
                print("Mengupload SRT terjemahan ke Cloudinary...")
                srt_translated_upload = upload_to_cloudinary(
                    file_path=srt_translated_path,
                    resource_type="raw",
                    folder="subtitles"
                )
                
                if srt_translated_upload:
                    srt_translated_url = srt_translated_upload.get('secure_url')
                    print(f"SRT terjemahan berhasil diupload: {srt_translated_url}")

            # 5️⃣ Kembalikan hasil ke API
            output = {
                "transcript_content": transcription_result['text'],
                "original_srt_content": original_srt_content,
                "translated_srt_content": translated_srt_content,
                "audio_path": audio_path,
                "original_srt_file": srt_original_path,
                "translated_srt_file": srt_translated_path if target_language else None,
                # URL local storage
                "video_url": video_url,
                "srt_original_url": srt_original_url,
                "srt_translated_url": srt_translated_url
            }

            # 💾 Simpan ke cache untuk request berikutnya
            transcription_cache.set(video_path, output, target_language)

            print(f"✅ Semua hasil disimpan di folder: {output_dir}")
            print(f"✅ Video dan subtitle tersedia di local storage")
            return output

        finally:
            # ❌ Tidak menghapus audio_path supaya bisa dicek manual
            pass