import json
import os
import uuid
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional

from app.database.models import PDFDocument, TextContent, Image, Table
from app.models.schemas import FileInfo


class PDFRepository:
    """Repository for PDF document database operations."""

    @staticmethod
    def create_document(db: Session, file_info: FileInfo) -> PDFDocument:
        """
        Create a new PDF document record.

        Args:
            db (Session): Database session
            file_info (FileInfo): File information

        Returns:
            PDFDocument: Created document record
        """
        # Generate UUID explicitly
        doc_id = str(uuid.uuid4())

        db_document = PDFDocument(
            id=doc_id,
            filename=os.path.basename(file_info.path),
            original_filename=file_info.filename
        )
        db.add(db_document)
        db.commit()
        db.refresh(db_document)

        # Debug print
        print(f"Created document with ID: {db_document.id}")

        return db_document

    @staticmethod
    def save_text_content(db: Session, document_id: str, text_data: Dict[str, str]) -> List[TextContent]:
        """
        Save text content for a document.

        Args:
            db (Session): Database session
            document_id (str): Document ID
            text_data (Dict[str, str]): Text data with page numbers as keys

        Returns:
            List[TextContent]: List of created text content records
        """
        text_contents = []

        for page_key, content in text_data.items():
            # Extract page number from the key (e.g., "Page 1" -> 1)
            page_number = int(page_key.split()[1])

            text_content = TextContent(
                document_id=document_id,
                page_number=page_number,
                content=content
            )
            db.add(text_content)
            text_contents.append(text_content)

        db.commit()
        return text_contents

    @staticmethod
    def save_images(db: Session, document_id: str, images: List[Dict[str, Any]]) -> List[Image]:
        """
        Save image metadata for a document.

        Args:
            db (Session): Database session
            document_id (str): Document ID
            images (List[Dict[str, Any]]): List of image metadata

        Returns:
            List[Image]: List of created image records
        """
        db_images = []

        for img in images:
            image = Image(
                document_id=document_id,
                page_number=img["page"],
                image_index=img["index"],
                filename=img["filename"]
            )
            db.add(image)
            db_images.append(image)

        db.commit()
        return db_images

    @staticmethod
    def save_tables(db: Session, document_id: str, tables_data: Dict[str, List[List[Any]]]) -> List[Table]:
        """
        Save table data for a document.

        Args:
            db (Session): Database session
            document_id (str): Document ID
            tables_data (Dict[str, List[List[Any]]]): Tables data with page numbers as keys

        Returns:
            List[Table]: List of created table records
        """
        tables = []

        for page_key, page_tables in tables_data.items():
            # Extract page number from the key (e.g., "Page 1" -> 1)
            page_number = int(page_key.split()[1])

            for table_index, table_data in enumerate(page_tables):
                table = Table(
                    document_id=document_id,
                    page_number=page_number,
                    table_index=table_index,
                    table_data=json.dumps(table_data)
                )
                db.add(table)
                tables.append(table)

        db.commit()
        return tables

    @staticmethod
    def get_document(db: Session, document_id: str) -> Optional[PDFDocument]:
        """
        Get a document by ID.

        Args:
            db (Session): Database session
            document_id (str): Document ID

        Returns:
            Optional[PDFDocument]: Document if found, None otherwise
        """
        return db.query(PDFDocument).filter(PDFDocument.id == document_id).first()

    @staticmethod
    def get_document_with_relations(db: Session, document_id: str) -> Optional[PDFDocument]:
        """
        Get a document with all its related data.

        Args:
            db (Session): Database session
            document_id (str): Document ID

        Returns:
            Optional[PDFDocument]: Document with relations if found, None otherwise
        """
        return db.query(PDFDocument).filter(PDFDocument.id == document_id).first()

    @staticmethod
    def list_documents(db: Session, skip: int = 0, limit: int = 100) -> List[PDFDocument]:
        """
        List all documents with pagination.

        Args:
            db (Session): Database session
            skip (int): Number of records to skip
            limit (int): Maximum number of records to return

        Returns:
            List[PDFDocument]: List of documents
        """
        return db.query(PDFDocument).order_by(PDFDocument.created_at.desc()).offset(skip).limit(limit).all()