import os
import logging
import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.database.connection import SessionLocal
from app.database.models import PDFDocument, Image

# Set up logging
logger = logging.getLogger("file_cleanup_worker")
logger.setLevel(logging.INFO)


class FileCleanupWorker:
    """Worker for cleaning up old PDF files and images after a retention period."""

    def __init__(self, retention_minutes: int = 10):
        """
        Initialize the worker.

        Args:
            retention_minutes (int): How long to keep files before deletion (in minutes)
        """
        self.retention_minutes = retention_minutes
        logger.info(f"Initializing file cleanup worker with retention period: {retention_minutes} minutes")

        self.scheduler = BackgroundScheduler()
        self.trigger = IntervalTrigger(minutes=1)  # Check every minute

        # Register the cleanup task
        self.scheduler.add_job(
            self.cleanup_old_files,
            trigger=self.trigger,
            id="cleanup_old_files",
            name="Cleanup old PDF files and images",
            replace_existing=True,
        )

    def start(self):
        """Start the scheduler."""
        if not self.scheduler.running:
            logger.info("Starting file cleanup worker")
            self.scheduler.start()

    def stop(self):
        """Stop the scheduler."""
        if self.scheduler.running:
            logger.info("Stopping file cleanup worker")
            self.scheduler.shutdown()

    def cleanup_old_files(self):
        """Clean up old PDF files and images."""
        try:
            logger.info("Running file cleanup task")

            # Get the retention threshold
            retention_threshold = datetime.datetime.now() - datetime.timedelta(minutes=self.retention_minutes)

            # Get a database session
            db = SessionLocal()
            try:
                # Find documents older than the retention threshold
                old_documents = db.query(PDFDocument).filter(
                    PDFDocument.created_at < retention_threshold
                ).all()

                if not old_documents:
                    logger.info("No old documents found for cleanup")
                    return

                logger.info(f"Found {len(old_documents)} old documents to clean up")

                for document in old_documents:
                    logger.info(f"Cleaning up document: {document.id}")

                    # Get the original PDF file path
                    pdf_path = os.path.join(settings.UPLOAD_FOLDER, document.filename)

                    # Delete the PDF file if it exists
                    try:
                        if os.path.exists(pdf_path):
                            os.remove(pdf_path)
                            logger.info(f"Deleted PDF file: {pdf_path}")
                        else:
                            logger.warning(f"PDF file not found for deletion: {pdf_path}")
                    except Exception as e:
                        logger.error(f"Error deleting PDF file {pdf_path}: {str(e)}")

                    # Get all images for this document
                    images = document.images

                    # Delete each image file
                    for image in images:
                        image_path = os.path.join(settings.IMAGE_FOLDER, image.filename)
                        try:
                            if os.path.exists(image_path):
                                os.remove(image_path)
                                logger.info(f"Deleted image file: {image_path}")
                            else:
                                logger.warning(f"Image file not found for deletion: {image_path}")
                        except Exception as e:
                            logger.error(f"Error deleting image file {image_path}: {str(e)}")

            finally:
                db.close()

            logger.info("File cleanup task completed")

        except Exception as e:
            logger.error(f"Error in file cleanup task: {str(e)}")


# Create a single instance of the worker
try:
    # First try to get the value directly from settings
    retention_minutes = getattr(settings, 'FILE_RETENTION_MINUTES', 10)
    print(f"Config FILE_RETENTION_MINUTES value: {retention_minutes}")

    # Check for environment variable directly
    env_retention = os.environ.get('FILE_RETENTION_MINUTES')
    print(f"Environment FILE_RETENTION_MINUTES value: {env_retention}")

    # If environment variable exists, use that value
    if env_retention:
        try:
            retention_minutes = int(env_retention)
            print(f"Using retention minutes from environment: {retention_minutes}")
        except ValueError:
            print(f"Could not convert environment value to int: {env_retention}")

    # Print all environment variables for debugging
    print("All environment variables:")
    for key, value in os.environ.items():
        if "RETENTION" in key or "FILE" in key:
            print(f"  {key}: {value}")

    # Print all settings attributes
    print("All settings attributes:")
    for attr in dir(settings):
        if not attr.startswith('_') and attr.isupper():
            print(f"  {attr}: {getattr(settings, attr)}")

    file_cleanup_worker = FileCleanupWorker(retention_minutes=retention_minutes)
    print(f"Created file cleanup worker with retention minutes: {retention_minutes}")
except Exception as e:
    logger.error(f"Error initializing file cleanup worker: {str(e)}")
    # Use default retention period
    file_cleanup_worker = FileCleanupWorker(retention_minutes=10)
    print("Created file cleanup worker with default retention minutes: 10")