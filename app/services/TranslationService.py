import os
import whisper
from googletrans import Translator
from app.utils.functions import (
    extract_audio,
    transcribe_audio,
    create_srt_content
)

class TranslationService:
    def __init__(self):
        print("Memuat model Whisper... (Mungkin butuh beberapa saat)")
        self.model = whisper.load_model("base")
        self.translator = Translator()
        print("Model Whisper berhasil dimuat.")

    def process_video(self, video_path: str, target_language: str = None) -> dict:
        """
        Mengoordinasikan alur kerja:
        1. Ekstrak audio
        2. Transkripsi
        3. Buat SRT asli
        4. Buat SRT terjemahan
        5. Simpan hasil di folder 'output/'
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

            # 4️⃣ Terjemahan (opsional)
            translated_srt_content = None
            if target_language:
                print(f"Menerjemahkan ke {target_language}...")
                translated_srt_content = create_srt_content(
                    segments=transcription_result['segments'],
                    translator_instance=self.translator,
                    translate_to=target_language
                )

                with open(srt_translated_path, "w", encoding="utf-8") as f:
                    f.write(translated_srt_content)

            # 5️⃣ Kembalikan hasil ke API
            output = {
                "transcript_content": transcription_result['text'],
                "original_srt_content": original_srt_content,
                "translated_srt_content": translated_srt_content,
                "audio_path": audio_path,
                "original_srt_file": srt_original_path,
                "translated_srt_file": srt_translated_path if target_language else None
            }

            print(f"✅ Semua hasil disimpan di folder: {output_dir}")
            return output

        finally:
            # ❌ Tidak menghapus audio_path supaya bisa dicek manual
            pass
