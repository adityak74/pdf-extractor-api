from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database.connection import Base


def generate_uuid():
    """Generate a UUID string."""
    uuid_value = str(uuid.uuid4())
    print(f"Generated UUID: {uuid_value}")
    return uuid_value


class PDFDocument(Base):
    """Model for storing PDF document metadata."""
    __tablename__ = "pdf_documents"

    id = Column(String, primary_key=True, default=generate_uuid)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    text_contents = relationship("TextContent", back_populates="document", cascade="all, delete-orphan")
    images = relationship("Image", back_populates="document", cascade="all, delete-orphan")
    tables = relationship("Table", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PDFDocument(id='{self.id}', filename='{self.filename}')>"


class TextContent(Base):
    """Model for storing text extracted from PDF pages."""
    __tablename__ = "text_contents"

    id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(String, ForeignKey("pdf_documents.id", ondelete="CASCADE"), nullable=False)
    page_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    document = relationship("PDFDocument", back_populates="text_contents")


class Image(Base):
    """Model for storing image metadata extracted from PDFs."""
    __tablename__ = "images"

    id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(String, ForeignKey("pdf_documents.id", ondelete="CASCADE"), nullable=False)
    page_number = Column(Integer, nullable=False)
    image_index = Column(Integer, nullable=False)
    filename = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    document = relationship("PDFDocument", back_populates="images")


class Table(Base):
    """Model for storing table data extracted from PDFs."""
    __tablename__ = "tables"

    id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(String, ForeignKey("pdf_documents.id", ondelete="CASCADE"), nullable=False)
    page_number = Column(Integer, nullable=False)
    table_index = Column(Integer, nullable=False)
    table_data = Column(Text, nullable=False)  # Store as JSON string
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    document = relationship("PDFDocument", back_populates="tables")