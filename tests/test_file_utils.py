import os
import pytest
from fastapi import UploadFile
from unittest.mock import MagicMock

from app.utils.file_utils import save_upload_file, get_image_url, parse_image_filename
from app.config import settings


async def test_save_upload_file(temp_dir, monkeypatch):
    """Test saving an uploaded file."""
    # Mock the settings
    monkeypatch.setattr(settings, "UPLOAD_FOLDER", temp_dir)

    # Create a mock UploadFile
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test.pdf"

    # Create a mock file-like object
    mock_file.file.read.return_value = b"test content"

    # Save the file
    file_info = await save_upload_file(mock_file)

    # Check result
    assert file_info.filename == "test.pdf"
    assert file_info.path == os.path.join(temp_dir, "test.pdf")

    # Check that the file was actually created
    assert os.path.exists(file_info.path)

    # Check file content
    with open(file_info.path, "rb") as f:
        content = f.read()
        assert content == b"test content"


def test_get_image_url(monkeypatch):
    """Test generating an image URL."""
    # Mock the settings
    monkeypatch.setattr(settings, "API_PREFIX", "/api/v1")

    # Generate URL
    url = get_image_url("test_image.png")

    # Check result
    assert url == "/api/v1/images/test_image.png"


def test_parse_image_filename():
    """Test parsing an image filename."""
    # Test with standard filename format
    document_id, page_num, img_index = parse_image_filename("abc123_page_1_image_2.png")

    # Check result
    assert document_id == "abc123"
    assert page_num == 1
    assert img_index == 2

    # Test with UUID document ID
    document_id, page_num, img_index = parse_image_filename(
        "550e8400-e29b-41d4-a716-446655440000_page_3_image_1.jpg"
    )

    # Check result
    assert document_id == "550e8400-e29b-41d4-a716-446655440000"
    assert page_num == 3
    assert img_index == 1