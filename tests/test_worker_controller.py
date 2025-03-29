import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from app.controllers.worker_controller import get_worker_status
from app.workers.file_cleanup import FileCleanupWorker


@pytest.mark.asyncio
async def test_get_worker_status_running():
    """Test getting worker status when the worker is running."""
    # Create a mock worker
    mock_worker = MagicMock()
    mock_worker.scheduler = MagicMock()
    mock_worker.scheduler.running = True
    mock_worker.retention_minutes = 10

    # Create a mock job
    mock_job = MagicMock()
    next_run_time = datetime.now() + timedelta(minutes=1)
    mock_job.next_run_time = next_run_time

    # Set up the mock job in the scheduler
    mock_worker.scheduler.get_job.return_value = mock_job
    mock_worker.scheduler.get_jobs.return_value = [mock_job]

    # Patch the file_cleanup_worker
    with patch("app.controllers.worker_controller.file_cleanup_worker", mock_worker):
        # Call the endpoint
        response = await get_worker_status()

    # Check response
    assert response["file_cleanup_worker"]["running"] is True
    assert response["file_cleanup_worker"]["retention_minutes"] == 10
    assert response["file_cleanup_worker"]["next_run"] == next_run_time.isoformat()
    assert response["file_cleanup_worker"]["job_count"] == 1


@pytest.mark.asyncio
async def test_get_worker_status_not_running():
    """Test getting worker status when the worker is not running."""
    # Create a mock worker
    mock_worker = MagicMock()
    mock_worker.scheduler = MagicMock()
    mock_worker.scheduler.running = False
    mock_worker.retention_minutes = 10

    # Mock get_job to raise an exception (worker not initialized)
    mock_worker.scheduler.get_job.side_effect = Exception("Worker not initialized")
    mock_worker.scheduler.get_jobs.return_value = []

    # Patch the file_cleanup_worker
    with patch("app.controllers.worker_controller.file_cleanup_worker", mock_worker):
        # Call the endpoint
        response = await get_worker_status()

    # Check response
    assert response["file_cleanup_worker"]["running"] is False
    assert "error" in response["file_cleanup_worker"]
    assert "Worker not initialized" in response["file_cleanup_worker"]["error"]


@pytest.mark.asyncio
async def test_get_worker_status_error_handling():
    """Test error handling in the worker status endpoint."""
    # Create a mock worker that raises an unexpected exception
    mock_worker = MagicMock()
    mock_worker.scheduler = MagicMock()
    mock_worker.scheduler.running = True
    mock_worker.retention_minutes = 10

    # Simulate an unexpected error
    mock_worker.scheduler.get_job.side_effect = Exception("Unexpected error")

    # Patch the file_cleanup_worker
    with patch("app.controllers.worker_controller.file_cleanup_worker", mock_worker):
        # Call the endpoint
        response = await get_worker_status()

    # Check response contains error information
    assert response["file_cleanup_worker"]["running"] is False
    assert response["file_cleanup_worker"]["retention_minutes"] == 10
    assert response["file_cleanup_worker"]["next_run"] is None
    assert response["file_cleanup_worker"]["job_count"] == 0
    assert "error" in response["file_cleanup_worker"]
    assert "Unexpected error" in response["file_cleanup_worker"]["error"]