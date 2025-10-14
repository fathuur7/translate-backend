import os
import tempfile
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from app.services.TranslationService import TranslationService
from app.utils.functions import save_upload_file
from app.models.Translation import TranslationResponse

router = APIRouter(
    prefix="/translate-video",
    tags=["Video Translation"]
)

print("Menginisialisasi Translation Service... (Model Whisper akan dimuat)")
translation_service = TranslationService()
print("Service siap. Router siap menerima permintaan.")

@router.post("/", response_model=TranslationResponse)
async def create_video_translation(
    video_file: UploadFile = File(..., description="File video yang akan diproses (MP4, MKV, dll.)."),
    target_language: str = Form('id', description="Kode bahasa target untuk terjemahan (contoh: 'id', 'en', 'ja').")
):
    with tempfile.TemporaryDirectory() as temp_dir:
        video_path = os.path.join(temp_dir, video_file.filename)

        try:
            save_upload_file(video_file, video_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gagal menyimpan file video: {e}")
        
        print(f"Memproses video: {video_file.filename} untuk bahasa: {target_language}")
        
        try:
            results = translation_service.process_video(video_path, target_language)
            
            if not results:
                raise HTTPException(status_code=500, detail="Pemrosesan video gagal. Periksa log server.")

            print(f"Berhasil memproses video: {video_file.filename}")
            
            response_data = TranslationResponse(
                filename=video_file.filename,
                target_language=target_language,
                original_transcript=results.get("transcript_content"),
                original_srt=results.get("original_srt_content"),
                translated_srt=results.get("translated_srt_content")
            )
            
            return JSONResponse(content=jsonable_encoder(response_data))

        except Exception as e:
            print(f"Error saat memproses video: {e}")
            raise HTTPException(status_code=500, detail=f"Terjadi kesalahan internal: {e}")
