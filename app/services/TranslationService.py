import os
import whisper
from googletrans import Translator
from app.utils.functions import (
    extract_audio,
    transcribe_audio,
    create_srt_content,
    upload_to_cloudinary,
    configure_cloudinary
)

class TranslationService:
    def __init__(self):
        print("Memuat model Whisper... (Mungkin butuh beberapa saat)")
        self.model = whisper.load_model("base")
        self.translator = Translator()
        
        # Konfigurasi Cloudinary
        configure_cloudinary(
            cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
            api_key=os.getenv("CLOUDINARY_API_KEY"),
            api_secret=os.getenv("CLOUDINARY_API_SECRET")
        )
        print("Model Whisper berhasil dimuat.")

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
            # 🎥 Upload video ke Cloudinary
            print("Mengupload video ke Cloudinary...")
            video_upload_result = upload_to_cloudinary(
                file_path=video_path,
                resource_type="video",
                folder="videos"
            )
            
            video_url = None
            if video_upload_result:
                video_url = video_upload_result.get('secure_url')
                print(f"Video berhasil diupload: {video_url}")
            else:
                print("Warning: Gagal mengupload video ke Cloudinary")

            # 1️⃣ Ekstrak audio dari video ke folder output
            extract_audio(video_path, audio_path)

            # 2️⃣ Transkripsi audio
            transcription_result = transcribe_audio(self.model, audio_path)
            if not transcription_result or 'segments' not in transcription_result:
                print("Transkripsi tidak menghasilkan segmen.")
                return None

            # 3️⃣ Buat konten SRT asli
            original_srt_content = create_srt_content(
                segments=transcription_result['segments'],
                translator_instance=self.translator
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
                print(f"Menerjemahkan ke {target_language}...")
                translated_srt_content = create_srt_content(
                    segments=transcription_result['segments'],
                    translator_instance=self.translator,
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

            # 5️⃣ Kembalikan hasil ke API dengan URL Cloudinary
            output = {
                "transcript_content": transcription_result['text'],
                "original_srt_content": original_srt_content,
                "translated_srt_content": translated_srt_content,
                "audio_path": audio_path,
                "original_srt_file": srt_original_path,
                "translated_srt_file": srt_translated_path if target_language else None,
                # URL Cloudinary
                "video_url": video_url,
                "srt_original_url": srt_original_url,
                "srt_translated_url": srt_translated_url
            }

            print(f"✅ Semua hasil disimpan di folder: {output_dir}")
            print(f"✅ Video dan subtitle tersedia di Cloudinary")
            return output

        finally:
            # ❌ Tidak menghapus audio_path supaya bisa dicek manual
            pass