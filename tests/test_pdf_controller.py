import os
import pytest
import json
from unittest.mock import patch, MagicMock
from fastapi import UploadFile, HTTPException
from fastapi.responses import FileResponse
from datetime import datetime

from app.controllers.pdf_controller import extract_pdf, get_pdf_document, list_pdf_documents, download_image
from app.models.schemas import PDFExtractResponse, TextData, TableData, PDFDocumentListResponse
from app.database.models import PDFDocument
from app.config import settings


@pytest.mark.asyncio
async def test_extract_pdf_valid_file(test_pdf_file, db_session):
    """Test extracting content from a valid PDF file."""
    # Create a mock UploadFile
    with open(test_pdf_file, "rb") as f:
        file_content = f.read()

    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test.pdf"
    mock_file.file.read.return_value = file_content

    # Mock the save_upload_file function
    mock_file_info = MagicMock()
    mock_file_info.filename = "test.pdf"
    mock_file_info.path = test_pdf_file

    # Create a mock response
    mock_response = PDFExtractResponse(
        id="test-doc-id",
        filename="test.pdf",
        text=TextData(pages={"Page 1": "Test text"}),
        tables=TableData(pages={}),
        images=[],
        created_at=datetime.now()
    )

    with patch("app.controllers.pdf_controller.save_upload_file", return_value=mock_file_info):
        with patch("app.controllers.pdf_controller.PDFService.process_pdf", return_value=mock_response):
            # Call the endpoint
            response = await extract_pdf(file=mock_file, db=db_session)

    # Check response
    assert response.id == "test-doc-id"
    assert response.filename == "test.pdf"
    assert "Page 1" in response.text.pages
    assert response.text.pages["Page 1"] == "Test text"


@pytest.mark.asyncio
async def test_extract_pdf_invalid_extension(db_session):
    """Test extracting content from a file with invalid extension."""
    # Create a mock UploadFile with non-PDF extension
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test.txt"

    # Call the endpoint and check for exception
    with pytest.raises(HTTPException) as excinfo:
        await extract_pdf(file=mock_file, db=db_session)

    # Check exception details
    assert excinfo.value.status_code == 400
    assert "Only PDF files are supported" in str(excinfo.value.detail)


@pytest.mark.asyncio
async def test_extract_pdf_processing_error(test_pdf_file, db_session):
    """Test handling of processing errors during extraction."""
    # Create a mock UploadFile
    with open(test_pdf_file, "rb") as f:
        file_content = f.read()

    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test.pdf"
    mock_file.file.read.return_value = file_content

    # Mock the save_upload_file function
    mock_file_info = MagicMock()
    mock_file_info.filename = "test.pdf"
    mock_file_info.path = test_pdf_file

    # Mock process_pdf to raise an exception
    with patch("app.controllers.pdf_controller.save_upload_file", return_value=mock_file_info):
        with patch("app.controllers.pdf_controller.PDFService.process_pdf", side_effect=Exception("Processing error")):
            # Call the endpoint and check for exception
            with pytest.raises(HTTPException) as excinfo:
                await extract_pdf(file=mock_file, db=db_session)

    # Check exception details
    assert excinfo.value.status_code == 400
    assert "Error processing PDF: Processing error" in str(excinfo.value.detail)


@pytest.mark.asyncio
async def test_get_pdf_document_found(db_session):
    """Test retrieving a PDF document by ID."""
    # Create a mock response
    mock_response = PDFExtractResponse(
        id="test-doc-id",
        filename="test.pdf",
        text=TextData(pages={"Page 1": "Test text"}),
        tables=TableData(pages={}),
        images=[],
        created_at=datetime.now()
    )

    # Mock the get_pdf_by_id method
    with patch("app.controllers.pdf_controller.PDFService.get_pdf_by_id", return_value=mock_response):
        # Call the endpoint
        response = await get_pdf_document(document_id="test-doc-id", db=db_session)

    # Check response
    assert response.id == "test-doc-id"
    assert response.filename == "test.pdf"
    assert "Page 1" in response.text.pages
    assert response.text.pages["Page 1"] == "Test text"


@pytest.mark.asyncio
async def test_get_pdf_document_not_found(db_session):
    """Test retrieving a non-existent PDF document."""
    # Mock the get_pdf_by_id method to return None
    with patch("app.controllers.pdf_controller.PDFService.get_pdf_by_id", return_value=None):
        # Call the endpoint and check for exception
        with pytest.raises(HTTPException) as excinfo:
            await get_pdf_document(document_id="non-existent-id", db=db_session)

    # Check exception details
    assert excinfo.value.status_code == 404
    assert "Document with ID non-existent-id not found" in str(excinfo.value.detail)


@pytest.mark.asyncio
async def test_list_pdf_documents(db_session):
    """Test listing PDF documents."""
    # Create mock documents
    mock_documents = [
        PDFDocument(id=f"doc-{i}", filename=f"test{i}.pdf", original_filename=f"test{i}.pdf")
        for i in range(5)
    ]

    # Mock the list_documents method
    with patch("app.controllers.pdf_controller.PDFRepository.list_documents", return_value=mock_documents):
        # Mock the count query
        with patch("app.controllers.pdf_controller.PDFRepository.list_documents", return_value=mock_documents):
            # Call the endpoint
            response = await list_pdf_documents(skip=0, limit=10, db=db_session)

    # Check response
    assert isinstance(response, PDFDocumentListResponse)
    assert len(response.documents) == 5
    assert response.total == 5
    assert response.skip == 0
    assert response.limit == 10

    # Check document IDs
    doc_ids = [doc.id for doc in response.documents]
    assert "doc-0" in doc_ids
    assert "doc-4" in doc_ids


@pytest.mark.asyncio
async def test_download_image_found(temp_dir, monkeypatch):
    """Test downloading an image that exists."""
    # Mock the settings
    monkeypatch.setattr(settings, "IMAGE_FOLDER", temp_dir)

    # Create a test image file
    image_path = os.path.join(temp_dir, "test_image.png")
    with open(image_path, "wb") as f:
        f.write(b"fake image data")

    # Mock the FileResponse class
    with patch("app.controllers.pdf_controller.FileResponse", return_value="file_response") as mock_file_response:
        # Call the endpoint
        response = await download_image(filename="test_image.png")

    # Check that FileResponse was called with the correct path
    mock_file_response.assert_called_once_with(image_path)

    # Check response
    assert response == "file_response"


@pytest.mark.asyncio
async def test_download_image_not_found(temp_dir, monkeypatch):
    """Test downloading a non-existent image."""
    # Mock the settings
    monkeypatch.setattr(settings, "IMAGE_FOLDER", temp_dir)

    # Call the endpoint and check for exception
    with pytest.raises(HTTPException) as excinfo:
        await download_image(filename="non_existent_image.png")

    # Check exception details
    assert excinfo.value.status_code == 404
    assert "Image not found: non_existent_image.png" in str(excinfo.value.detail)