from fastapi import APIRouter, Depends
from typing import Dict

from app.workers.file_cleanup import file_cleanup_worker
from app.config import settings

# Create router
router = APIRouter(tags=["Worker Status"])


@router.get(
    "/workers/status",
    summary="Get worker status",
    description="Get the status of background workers.",
)
async def get_worker_status() -> Dict:
    """
    Get the status of background workers.

    Returns:
        Dict: Status information about background workers
    """
    return {
        "file_cleanup_worker": {
            "running": file_cleanup_worker.scheduler.running,
            "retention_minutes": file_cleanup_worker.retention_minutes,
            "next_run": file_cleanup_worker.scheduler.get_job("cleanup_old_files").next_run_time.isoformat()
            if file_cleanup_worker.scheduler.running else None,
            "job_count": len(file_cleanup_worker.scheduler.get_jobs())
        }
    }