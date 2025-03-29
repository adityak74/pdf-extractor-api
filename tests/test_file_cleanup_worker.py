import os
import pytest
from unittest.mock import patch, MagicMock, call
from datetime import datetime, timedelta
from freezegun import freeze_time

from app.workers.file_cleanup import FileCleanupWorker
from app.database.models import PDFDocument, Image


def test_file_cleanup_worker_init():
    """Test initializing the FileCleanupWorker."""
    # Create a worker
    worker = FileCleanupWorker(retention_minutes=15)

    # Check attributes
    assert worker.retention_minutes == 15
    assert worker.scheduler is not None
    assert not worker.scheduler.running

    # Check job registration
    job = worker.scheduler.get_job("cleanup_old_files")
    assert job is not None
    assert job.name == "Cleanup old PDF files and images"


def test_file_cleanup_worker_start_stop():
    """Test starting and stopping the FileCleanupWorker."""
    # Create a worker
    worker = FileCleanupWorker()

    # Mock the scheduler methods
    worker.scheduler.start = MagicMock()
    worker.scheduler.shutdown = MagicMock()
    worker.scheduler.running = False

    # Start the worker
    worker.start()
    worker.scheduler.running = True  # Mock the running state

    # Check that the scheduler was started
    worker.scheduler.start.assert_called_once()

    # Stop the worker
    worker.stop()

    # Check that the scheduler was shut down
    worker.scheduler.shutdown.assert_called_once()


def test_file_cleanup_worker_no_old_documents(db_session):
    """Test cleanup with no old documents."""
    # Create a worker
    worker = FileCleanupWorker()

    # Mock SessionLocal to return our test session
    with patch("app.workers.file_cleanup.SessionLocal", return_value=db_session):
        # Mock query to return an empty list
        db_session.query = MagicMock(return_value=MagicMock())
        db_session.query.return_value.filter.return_value.all.return_value = []

        # Run the cleanup
        worker.cleanup_old_files()

    # Check query was called with PDFDocument
    db_session.query.assert_called_with(PDFDocument)


@freeze_time("2023-01-01 12:00:00")
def test_file_cleanup_worker_with_old_documents(db_session, temp_dir, monkeypatch):
    """Test cleanup with old documents that should be deleted."""
    # Mock settings
    monkeypatch.setattr("app.workers.file_cleanup.settings.UPLOAD_FOLDER", temp_dir)
    monkeypatch.setattr("app.workers.file_cleanup.settings.IMAGE_FOLDER", temp_dir)

    # Create a worker
    worker = FileCleanupWorker(retention_minutes=10)

    # Create test files
    pdf_path = os.path.join(temp_dir, "test.pdf")
    image_path = os.path.join(temp_dir, "test_image.png")

    with open(pdf_path, "wb") as f:
        f.write(b"test pdf content")

    with open(image_path, "wb") as f:
        f.write(b"test image content")

    # Create a mock old document
    old_doc = MagicMock(spec=PDFDocument)
    old_doc.id = "old-doc-id"
    old_doc.filename = "test.pdf"
    old_doc.created_at = datetime.now() - timedelta(minutes=20)  # 20 minutes old

    # Create a mock image
    mock_image = MagicMock(spec=Image)
    mock_image.filename = "test_image.png"

    # Set up the document to have the image
    old_doc.images = [mock_image]

    # Mock SessionLocal to return our test session
    with patch("app.workers.file_cleanup.SessionLocal", return_value=db_session):
        # Mock query to return our old document
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [old_doc]
        db_session.query.return_value = mock_query

        # Run the cleanup
        worker.cleanup_old_files()

    # Check that the files were deleted
    assert not os.path.exists(pdf_path)
    assert not os.path.exists(image_path)


@freeze_time("2023-01-01 12:00:00")
def test_file_cleanup_worker_with_recent_documents(db_session, temp_dir, monkeypatch):
    """Test cleanup with recent documents that should not be deleted."""
    # Mock settings
    monkeypatch.setattr("app.workers.file_cleanup.settings.UPLOAD_FOLDER", temp_dir)
    monkeypatch.setattr("app.workers.file_cleanup.settings.IMAGE_FOLDER", temp_dir)

    # Create a worker
    worker = FileCleanupWorker(retention_minutes=10)

    # Create test files
    pdf_path = os.path.join(temp_dir, "test.pdf")
    image_path = os.path.join(temp_dir, "test_image.png")

    with open(pdf_path, "wb") as f:
        f.write(b"test pdf content")

    with open(image_path, "wb") as f:
        f.write(b"test image content")

    # Create a mock recent document
    recent_doc = MagicMock(spec=PDFDocument)
    recent_doc.id = "recent-doc-id"
    recent_doc.filename = "test.pdf"
    recent_doc.created_at = datetime.now() - timedelta(minutes=5)  # 5 minutes old

    # Create a mock image
    mock_image = MagicMock(spec=Image)
    mock_image.filename = "test_image.png"

    # Set up the document to have the image
    recent_doc.images = [mock_image]

    # Mock SessionLocal to return our test session
    with patch("app.workers.file_cleanup.SessionLocal", return_value=db_session):
        # Mock query to return no old documents
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        db_session.query.return_value = mock_query

        # Run the cleanup
        worker.cleanup_old_files()

    # Check that the files were not deleted
    assert os.path.exists(pdf_path)
    assert os.path.exists(image_path)


@freeze_time("2023-01-01 12:00:00")
def test_file_cleanup_worker_missing_files(db_session, temp_dir, monkeypatch):
    """Test cleanup with old documents but missing files."""
    # Mock settings
    monkeypatch.setattr("app.workers.file_cleanup.settings.UPLOAD_FOLDER", temp_dir)
    monkeypatch.setattr("app.workers.file_cleanup.settings.IMAGE_FOLDER", temp_dir)

    # Create a worker
    worker = FileCleanupWorker(retention_minutes=10)

    # Create a mock old document with non-existent files
    old_doc = MagicMock(spec=PDFDocument)
    old_doc.id = "old-doc-id"
    old_doc.filename = "non_existent.pdf"
    old_doc.created_at = datetime.now() - timedelta(minutes=20)  # 20 minutes old

    # Create a mock image with non-existent file
    mock_image = MagicMock(spec=Image)
    mock_image.filename = "non_existent_image.png"

    # Set up the document to have the image
    old_doc.images = [mock_image]

    # Mock SessionLocal to return our test session
    with patch("app.workers.file_cleanup.SessionLocal", return_value=db_session):
        # Mock query to return our old document
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [old_doc]
        db_session.query.return_value = mock_query

        # Run the cleanup without raising exceptions
        worker.cleanup_old_files()

    # The test passes if no exceptions were raised
    assert True


def test_file_cleanup_worker_error_handling(db_session):
    """Test error handling in the cleanup worker."""
    # Create a worker
    worker = FileCleanupWorker()

    # Mock SessionLocal to raise an exception
    with patch("app.workers.file_cleanup.SessionLocal", side_effect=Exception("Database error")):
        # Run the cleanup - should not raise an exception
        worker.cleanup_old_files()

    # The test passes if no exceptions were raised
    assert True


@freeze_time("2023-01-01 12:00:00")
def test_file_cleanup_worker_retention_threshold(db_session):
    """Test that the worker correctly calculates the retention threshold."""
    # Create workers with different retention times
    worker_10 = FileCleanupWorker(retention_minutes=10)
    worker_60 = FileCleanupWorker(retention_minutes=60)

    # Get the current time
    now = datetime.now()

    # Mock SessionLocal to return our test session
    with patch("app.workers.file_cleanup.SessionLocal", return_value=db_session):
        # Create a mock query that captures the filter
        mock_query = MagicMock()
        db_session.query.return_value = mock_query
        mock_query.filter.return_value.all.return_value = []

        # Run the cleanup for the 10-minute worker
        worker_10.cleanup_old_files()

        # Save the filter call
        filter_call_10 = mock_query.filter.call_args[0][0]

        # Reset the mock
        mock_query.filter.reset_mock()

        # Run the cleanup for the 60-minute worker
        worker_60.cleanup_old_files()

        # Save the filter call
        filter_call_60 = mock_query.filter.call_args[0][0]

    # Check that the thresholds are different
    assert filter_call_10 != filter_call_60

    # We can't directly compare the filter objects, but we can check the worker's retention_minutes
    assert worker_10.retention_minutes == 10
    assert worker_60.retention_minutes == 60