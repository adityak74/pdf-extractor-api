import os
import shutil
from fastapi import UploadFile
from app.config import settings
from app.models.schemas import FileInfo


async def save_upload_file(file: UploadFile) -> FileInfo:
    """
    Save an uploaded file to the upload directory.

    Args:
        file (UploadFile): The uploaded file

    Returns:
        FileInfo: Information about the saved file
    """
    file_path = os.path.join(settings.UPLOAD_FOLDER, file.filename)

    # Save the file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return FileInfo(filename=file.filename, path=file_path)


def get_image_url(filename: str) -> str:
    """
    Generate a URL for accessing an image.

    Args:
        filename (str): The image filename

    Returns:
        str: The URL to access the image
    """
    return f"{settings.API_PREFIX}/images/{filename}"


def parse_image_filename(filename: str) -> tuple:
    """
    Parse document ID, page number and image index from a filename.

    Args:
        filename (str): The image filename (format: {document_id}_page_{page_num}_image_{img_index}.{ext})

    Returns:
        tuple: (document_id, page_number, image_index)
    """
    # Split by underscore first to get document_id
    parts = filename.split('_')
    document_id = parts[0]

    # Find page number (after "page_")
    page_num = int(parts[2])

    # Find image index (after "image_")
    img_index = int(parts[4].split('.')[0])

    return document_id, page_num, img_index