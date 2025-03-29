import os
import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.services.pdf_service import PDFService
from app.models.schemas import PDFExtractResponse, TextData, TableData
from app.database.models import PDFDocument, TextContent, Image, Table
from datetime import datetime


def test_root_endpoint(test_client):
    """Test the root endpoint."""
    response = test_client.get("/")

    assert response.status_code == 200
    assert "message" in response.json()
    assert "documentation" in response.json()


def test_health_check(test_client):
    """Test the health check endpoint."""
    response = test_client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_worker_status_endpoint(test_client):
    """Test the worker status endpoint."""
    # Create a mock FileCleanupWorker
    mock_worker = MagicMock()
    mock_worker.scheduler = MagicMock()
    mock_worker.scheduler.running = True
    mock_worker.retention_minutes = 10

    # Mock the get_job method
    mock_job = MagicMock()
    mock_job.next_run_time = datetime.now()
    mock_worker.scheduler.get_job.return_value = mock_job

    # Mock the get_jobs method
    mock_worker.scheduler.get_jobs.return_value = [mock_job]

    # Patch the file_cleanup_worker
    with patch("app.controllers.worker_controller.file_cleanup_worker", mock_worker):
        response = test_client.get("/api/v1/workers/status")

    # Check response
    assert response.status_code == 200
    assert "file_cleanup_worker" in response.json()
    assert response.json()["file_cleanup_worker"]["running"] is True
    assert response.json()["file_cleanup_worker"]["retention_minutes"] == 10
    assert "next_run" in response.json()["file_cleanup_worker"]
    assert response.json()["file_cleanup_worker"]["job_count"] == 1


def test_list_documents_endpoint(test_client, db_session):
    """Test the list documents endpoint."""
    # Create sample documents
    documents = []
    for i in range(3):
        doc = PDFDocument(
            id=f"doc-{i}",
            filename=f"test{i}.pdf",
            original_filename=f"test{i}.pdf"
        )
        db_session.add(doc)
        documents.append(doc)

    db_session.commit()

    # Call the endpoint
    response = test_client.get("/api/v1/documents")

    # Check response
    assert response.status_code == 200
    assert "documents" in response.json()
    assert "total" in response.json()
    assert response.json()["total"] == 3
    assert len(response.json()["documents"]) == 3

    # Check document IDs
    doc_ids = [doc["id"] for doc in response.json()["documents"]]
    assert "doc-0" in doc_ids
    assert "doc-1" in doc_ids
    assert "doc-2" in doc_ids


def test_get_document_endpoint(test_client, db_session):
    """Test the get document endpoint."""
    # Create a sample document
    doc = PDFDocument(
        id="test-doc-id",
        filename="test.pdf",
        original_filename="test.pdf"
    )
    db_session.add(doc)

    # Add some content
    text = TextContent(
        document_id=doc.id,
        page_number=1,
        content="Test text content"
    )
    db_session.add(text)

    # Commit to the database
    db_session.commit()

    # Call the endpoint
    response = test_client.get(f"/api/v1/documents/{doc.id}")

    # Check response
    assert response.status_code == 200
    assert response.json()["id"] == doc.id
    assert response.json()["filename"] == doc.original_filename
    assert "text" in response.json()
    assert "Page 1" in response.json()["text"]["pages"]
    assert response.json()["text"]["pages"]["Page 1"] == "Test text content"


def test_get_document_not_found(test_client):
    """Test the get document endpoint with non-existent ID."""
    response = test_client.get("/api/v1/documents/non-existent-id")

    # Check response
    assert response.status_code == 404
    assert "detail" in response.json()
    assert "not found" in response.json()["detail"]


def test_extract_endpoint_with_mock(test_client, test_pdf_file):
    """Test the extract endpoint with mocked PDF processing."""
    # Create a mock response for the PDF service
    mock_response = PDFExtractResponse(
        id="test-doc-id",
        filename="test.pdf",
        text=TextData(pages={"Page 1": "Test text content"}),
        tables=TableData(pages={}),
        images=[],
        created_at=datetime.now()
    )

    # Patch the PDF service to return our mock response
    with patch.object(PDFService, "process_pdf", return_value=mock_response):
        # Create a file to upload
        with open(test_pdf_file, "rb") as pdf:
            response = test_client.post(
                "/api/v1/extract",
                files={"file": ("test.pdf", pdf, "application/pdf")}
            )

    # Check response
    assert response.status_code == 200
    assert response.json()["id"] == "test-doc-id"
    assert response.json()["filename"] == "test.pdf"
    assert "text" in response.json()
    assert "Page 1" in response.json()["text"]["pages"]
    assert response.json()["text"]["pages"]["Page 1"] == "Test text content"


def test_extract_endpoint_invalid_file(test_client, temp_dir):
    """Test the extract endpoint with an invalid file type."""
    # Create a text file
    text_file = os.path.join(temp_dir, "test.txt")
    with open(text_file, "w") as f:
        f.write("This is not a PDF file")

    # Upload the text file
    with open(text_file, "rb") as f:
        response = test_client.post(
            "/api/v1/extract",
            files={"file": ("test.txt", f, "text/plain")}
        )

    # Check response
    assert response.status_code == 400
    assert "detail" in response.json()
    assert "Only PDF files are supported" in response.json()["detail"]


def test_download_image_endpoint(test_client, temp_dir, monkeypatch):
    """Test the download image endpoint."""
    # Mock the settings
    monkeypatch.setattr("app.controllers.pdf_controller.settings.IMAGE_FOLDER", temp_dir)

    # Create a test image
    image_path = os.path.join(temp_dir, "test_image.png")
    with open(image_path, "wb") as f:
        f.write(b"fake image data")

    # Call the endpoint
    response = test_client.get("/api/v1/images/test_image.png")

    # Check response
    assert response.status_code == 200
    assert response.content == b"fake image data"
    assert "image/png" in response.headers["content-type"]


def test_download_image_not_found(test_client, temp_dir, monkeypatch):
    """Test the download image endpoint with a non-existent image."""
    # Mock the settings
    monkeypatch.setattr("app.controllers.pdf_controller.settings.IMAGE_FOLDER", temp_dir)

    # Call the endpoint
    response = test_client.get("/api/v1/images/non_existent_image.png")

    # Check response
    assert response.status_code == 404
    assert "detail" in response.json()
    assert "Image not found" in response.json()["detail"]


def test_docs_endpoint(test_client):
    """Test that the documentation endpoints are accessible."""
    # OpenAPI schema
    response = test_client.get("/openapi.json")
    assert response.status_code == 200

    # Swagger UI
    response = test_client.get("/docs")
    assert response.status_code == 200

    # ReDoc
    response = test_client.get("/redoc")
    assert response.status_code == 200