"""
Job manager untuk tracking status background tasks.
Menggunakan in-memory storage sederhana (dapat diganti dengan Redis untuk production).
"""
import uuid
from datetime import datetime
from typing import Dict, Optional
from enum import Enum


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobManager:
    """Singleton job manager untuk tracking background tasks."""
    
    _instance = None
    _jobs: Dict[str, dict] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(JobManager, cls).__new__(cls)
        return cls._instance
    
    def create_job(self, video_filename: str, target_language: Optional[str] = None) -> str:
        """
        Buat job baru dan return job_id.
        """
        job_id = str(uuid.uuid4())
        self._jobs[job_id] = {
            "job_id": job_id,
            "status": JobStatus.PENDING,
            "video_filename": video_filename,
            "target_language": target_language,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "progress": 0,
            "message": "Job created, waiting to start...",
            "result": None,
            "error": None
        }
        return job_id
    
    def update_job(self, job_id: str, status: Optional[JobStatus] = None, 
                   progress: Optional[int] = None, message: Optional[str] = None,
                   result: Optional[dict] = None, error: Optional[str] = None):
        """
        Update job status, progress, atau result.
        """
        if job_id not in self._jobs:
            return False
        
        job = self._jobs[job_id]
        
        if status:
            job["status"] = status
        if progress is not None:
            job["progress"] = progress
        if message:
            job["message"] = message
        if result:
            job["result"] = result
        if error:
            job["error"] = error
            
        job["updated_at"] = datetime.utcnow().isoformat()
        return True
    
    def get_job(self, job_id: str) -> Optional[dict]:
        """
        Dapatkan informasi job berdasarkan job_id.
        """
        return self._jobs.get(job_id)
    
    def delete_job(self, job_id: str) -> bool:
        """
        Hapus job dari memory (optional cleanup).
        """
        if job_id in self._jobs:
            del self._jobs[job_id]
            return True
        return False
    
    def get_all_jobs(self) -> list:
        """
        Dapatkan semua jobs (untuk debugging/admin).
        """
        return list(self._jobs.values())


# Singleton instance
job_manager = JobManager()
