import os
import tempfile
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from app.services.TranslationService import TranslationService
from app.utils.functions import save_upload_file
from app.models.Translation import TranslationResponse
from app.utils.job_manager import job_manager, JobStatus

router = APIRouter(
    prefix="/translate-video",
    tags=["Video Translation"]
)

print("⚙️  Menginisialisasi Translation Service... (Model Whisper akan dimuat)")
# Whisper model bisa dikonfigurasi via environment variable WHISPER_MODEL
# Default: "base", untuk speed gunakan "tiny", untuk accuracy gunakan "small"/"medium"
translation_service = TranslationService()
print("✅ Service siap. Router siap menerima permintaan.")

from app.utils.cache_manager import transcription_cache

def process_video_background(job_id: str, video_path: str, target_language: str):
    """
    Background task untuk memproses video.
    """
    try:
        job_manager.update_job(job_id, status=JobStatus.PROCESSING, progress=10, 
                              message="Memulai pemrosesan video...")
        
        print(f"[Job {job_id}] Memproses video: {video_path}")
        
        job_manager.update_job(job_id, progress=30, message="Mengekstrak audio...")
        results = translation_service.process_video(video_path, target_language)
        
        if not results:
            job_manager.update_job(job_id, status=JobStatus.FAILED, progress=0,
                                  error="Pemrosesan video gagal")
            return
        
        job_manager.update_job(job_id, status=JobStatus.COMPLETED, progress=100,
                              message="Pemrosesan selesai!", result=results)
        
        print(f"[Job {job_id}] Selesai memproses video")
        
    except Exception as e:
        print(f"[Job {job_id}] Error: {e}")
        job_manager.update_job(job_id, status=JobStatus.FAILED, progress=0,
                              error=str(e))


@router.post("/")
async def create_video_translation(
    background_tasks: BackgroundTasks,
    video_file: UploadFile = File(..., description="File video yang akan diproses (MP4, MKV, dll.)."),
    target_language: str = Form('id', description="Kode bahasa target untuk terjemahan (contoh: 'id', 'en', 'ja').")
):
    """
    Upload video untuk diproses di background. Return job_id untuk tracking status.
    """
    # Simpan file ke folder uploads (persistent)
    upload_dir = os.path.join(os.getcwd(), "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    video_path = os.path.join(upload_dir, video_file.filename)
    
    try:
        save_upload_file(video_file, video_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal menyimpan file video: {e}")
    
    # Buat job dan jalankan di background
    job_id = job_manager.create_job(video_file.filename, target_language)
    background_tasks.add_task(process_video_background, job_id, video_path, target_language)
    
    print(f"Job {job_id} dibuat untuk video: {video_file.filename}")
    
    return JSONResponse(content={
        "job_id": job_id,
        "filename": video_file.filename,
        "target_language": target_language,
        "status": "pending",
        "message": "Video sedang diproses di background. Gunakan endpoint /status/{job_id} untuk cek progress."
    })


@router.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """
    Cek status job berdasarkan job_id.
    """
    job = job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} tidak ditemukan")
    
    response = {
        "job_id": job["job_id"],
        "status": job["status"],
        "progress": job["progress"],
        "message": job["message"],
        "video_filename": job["video_filename"],
        "target_language": job["target_language"],
        "created_at": job["created_at"],
        "updated_at": job["updated_at"]
    }
    
    # Jika job selesai, sertakan hasil
    if job["status"] == JobStatus.COMPLETED and "result" in job and job["result"]:
        results = job["result"]
        response["result"] = {
            "original_transcript": results.get("transcript_content"),
            "original_srt": results.get("original_srt_content"),
            "translated_srt": results.get("translated_srt_content"),
            "video_url": results.get("video_url"),
            "srt_original_url": results.get("srt_original_url"),
            "srt_translated_url": results.get("srt_translated_url")
        }
    
    # Jika job gagal, sertakan error
    if job["status"] == JobStatus.FAILED and "error" in job and job["error"]:
        response["error"] = job["error"]
    
    return JSONResponse(content=jsonable_encoder(response))


@router.get("/jobs")
async def list_all_jobs():
    """
    List semua jobs (untuk debugging/monitoring).
    """
    jobs = job_manager.get_all_jobs()
    return JSONResponse(content={"total": len(jobs), "jobs": jobs})


@router.post("/cache/clear")
async def clear_cache():
    """
    Clear semua cache transkripsi (untuk maintenance).
    """
    transcription_cache.clear()
    return JSONResponse(content={"message": "Cache berhasil dihapus", "cache_size": 0})


@router.get("/cache/stats")
async def cache_stats():
    """
    Lihat statistik cache.
    """
    return JSONResponse(content={
        "cache_size": transcription_cache.size(),
        "max_size": transcription_cache.max_size,
        "message": f"Cache berisi {transcription_cache.size()} item"
    })