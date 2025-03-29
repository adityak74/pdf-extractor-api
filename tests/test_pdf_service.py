import os
import pytest
import json
from unittest.mock import patch, MagicMock
from pathlib import Path

from app.models.schemas import FileInfo
from app.services.pdf_service import PDFService
from app.database.models import PDFDocument, TextContent, Image, Table


@pytest.fixture
def sample_file_info(test_pdf_file):
    """Create a sample FileInfo object."""
    return FileInfo(filename="test.pdf", path=test_pdf_file)


@pytest.mark.asyncio
async def test_extract_text_and_images(sample_file_info, monkeypatch, temp_dir):
    """Test extracting text and images from a PDF."""
    # Mock the settings
    monkeypatch.setattr("app.services.pdf_service.settings.IMAGE_FOLDER", temp_dir)
    monkeypatch.setattr("app.utils.file_utils.settings.API_PREFIX", "/api/v1")

    # Create a document ID
    document_id = "test-doc-id"

    # Mock the fitz.open method to avoid actual PDF processing
    mock_doc = MagicMock()
    mock_page = MagicMock()
    mock_page.get_text.return_value = "Test text content"
    mock_doc.load_page.return_value = mock_page

    # Mock page count
    mock_doc.__len__.return_value = 1

    # Mock get_images to return a single image
    mock_page.get_images.return_value = [(0, 0, 0, 0, 0, 0, 0)]  # xref is first element

    # Mock extract_image to return image data
    mock_doc.extract_image.return_value = {
        "image": b"fake image data",
        "ext": "png"
    }

    with patch("fitz.open", return_value=mock_doc):
        with patch("PIL.Image.open") as mock_pil_open:
            # Mock PIL.Image to avoid actual image processing
            mock_image = MagicMock()
            mock_pil_open.return_value = mock_image

            # Call the method
            text_data, image_links = await PDFService.extract_text_and_images(sample_file_info, document_id)

    # Check text data
    assert "Page 1" in text_data.pages
    assert text_data.pages["Page 1"] == "Test text content"

    # Check image links
    assert len(image_links) == 1
    assert image_links[0].page == 1
    assert image_links[0].index == 1
    assert image_links[0].document_id == document_id
    assert image_links[0].filename.startswith(f"{document_id}_page_0_image_1")
    assert image_links[0].url.startswith("/api/v1/images/")


@pytest.mark.asyncio
async def test_extract_tables(sample_file_info, monkeypatch):
    """Test extracting tables from a PDF."""
    # Mock pdfplumber to avoid actual PDF processing
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_pdf.pages = [mock_page]

    # Mock extract_tables to return a single table
    mock_page.extract_tables.return_value = [[["Header1", "Header2"], ["Value1", "Value2"]]]

    with patch("pdfplumber.open", return_value=mock_pdf):
        # Call the method
        table_data = await PDFService.extract_tables(sample_file_info)

    # Check table data
    assert "Page 1" in table_data.pages
    assert len(table_data.pages["Page 1"]) == 1
    assert table_data.pages["Page 1"][0][0][0] == "Header1"
    assert table_data.pages["Page 1"][0][1][1] == "Value2"


@pytest.mark.asyncio
async def test_process_pdf(sample_file_info, db_session, monkeypatch):
    """Test processing a PDF file."""
    # Create a document to return from the repository
    document = PDFDocument(
        id="test-doc-id",
        filename="test.pdf",
        original_filename="test.pdf"
    )

    # Mock the repository methods
    with patch("app.database.repository.PDFRepository.create_document", return_value=document) as mock_create:
        with patch("app.database.repository.PDFRepository.save_text_content") as mock_save_text:
            with patch("app.database.repository.PDFRepository.save_images") as mock_save_images:
                with patch("app.database.repository.PDFRepository.save_tables") as mock_save_tables:
                    # Mock the extract methods to avoid actual PDF processing
                    with patch.object(PDFService, "extract_text_and_images") as mock_extract_text:
                        with patch.object(PDFService, "extract_tables") as mock_extract_tables:
                            # Setup mock returns
                            mock_text_data = MagicMock()
                            mock_text_data.pages = {"Page 1": "Test text"}

                            mock_extract_text.return_value = (mock_text_data, [])

                            mock_tables_data = MagicMock()
                            mock_tables_data.pages = {}

                            mock_extract_tables.return_value = mock_tables_data

                            # Call the method
                            result = await PDFService.process_pdf(db_session, sample_file_info)

    # Check that repository methods were called
    mock_create.assert_called_once_with(db_session, sample_file_info)
    mock_save_text.assert_called_once()
    mock_save_images.assert_called_once()

    # Since tables is empty, save_tables should not be called
    mock_save_tables.assert_not_called()

    # Check result
    assert result.id == document.id
    assert result.filename == document.original_filename
    assert hasattr(result, "text")
    assert hasattr(result, "tables")
    assert hasattr(result, "images")


@pytest.mark.asyncio
async def test_get_pdf_by_id(db_session, monkeypatch):
    """Test retrieving a processed PDF by ID."""
    # Create a sample document
    document = PDFDocument(
        id="test-doc-id",
        filename="test.pdf",
        original_filename="test.pdf"
    )

    # Add text content
    text = TextContent(
        id="text-id",
        document_id=document.id,
        page_number=1,
        content="Test text content"
    )
    document.text_contents = [text]

    # Add image
    image = Image(
        id="image-id",
        document_id=document.id,
        page_number=1,
        image_index=1,
        filename="test_image.png"
    )
    document.images = [image]

    # Add table
    table = Table(
        id="table-id",
        document_id=document.id,
        page_number=1,
        table_index=1,
        table_data=json.dumps([["Header1", "Header2"], ["Value1", "Value2"]])
    )
    document.tables = [table]

    # Mock the repository method
    with patch("app.database.repository.PDFRepository.get_document_with_relations", return_value=document):
        # Mock the URL generator
        monkeypatch.setattr("app.utils.file_utils.settings.API_PREFIX", "/api/v1")

        # Call the method
        result = await PDFService.get_pdf_by_id(db_session, document.id)

    # Check result
    assert result.id == document.id
    assert result.filename == document.original_filename

    # Check text data
    assert "Page 1" in result.text.pages
    assert result.text.pages["Page 1"] == "Test text content"

    # Check image links
    assert len(result.images) == 1
    assert result.images[0].page == 1
    assert result.images[0].index == 1
    assert result.images[0].filename == "test_image.png"
    assert result.images[0].url == "/api/v1/images/test_image.png"

    # Check table data
    assert "Page 1" in result.tables.pages
    assert len(result.tables.pages["Page 1"]) == 1
    assert result.tables.pages["Page 1"][0][0][0] == "Header1"
    assert result.tables.pages["Page 1"][0][1][1] == "Value2"


@pytest.mark.asyncio
async def test_get_pdf_by_id_not_found(db_session):
    """Test retrieving a non-existent PDF."""
    # Mock the repository method to return None
    with patch("app.database.repository.PDFRepository.get_document_with_relations", return_value=None):
        # Call the method
        result = await PDFService.get_pdf_by_id(db_session, "non-existent-id")

    # Check result
    assert result is None