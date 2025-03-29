import os
import pytest
import tempfile
import shutil
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database.models import Base
from app.config import Settings
from app.main import app
from app.database.connection import get_db


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Clean up after test
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_pdf_file(temp_dir):
    """Create a dummy PDF file for testing."""
    pdf_path = Path(temp_dir) / "test.pdf"
    # Create a minimal valid PDF file
    with open(pdf_path, "wb") as f:
        f.write(
            b"%PDF-1.0\n%\xe2\xe3\xcf\xd3\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 3 3]>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000053 00000 n\n0000000102 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n149\n%EOF")
    return str(pdf_path)


@pytest.fixture
def db_engine():
    """Create a test database engine."""
    # Create an in-memory SQLite database for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(db_engine):
    """Create a test database session."""
    # Create a sessionmaker
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

    # Create a session
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_app():
    """Create a test application with test settings."""
    # Use test settings
    test_settings = Settings()
    test_settings.DEBUG = True

    # Create temp directories for files
    upload_dir = tempfile.mkdtemp()
    images_dir = tempfile.mkdtemp()

    # Set test paths
    test_settings.UPLOAD_FOLDER = upload_dir
    test_settings.IMAGE_FOLDER = images_dir

    yield app

    # Clean up
    shutil.rmtree(upload_dir)
    shutil.rmtree(images_dir)


@pytest.fixture
def test_client(test_app, db_session):
    """Create a test client for the FastAPI app."""

    # Override the dependency with our test session
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    # Remove dependency override
    app.dependency_overrides = {}
