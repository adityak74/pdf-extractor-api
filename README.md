# PDF Extractor API

A FastAPI application that extracts text, tables, and images from PDF files.

## Project Structure

```
pdf_extractor/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py
│   ├── controllers/
│   │   ├── __init__.py
│   │   ├── pdf_controller.py
│   │   └── worker_controller.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── pdf_service.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── file_utils.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   ├── models.py
│   │   └── repository.py
│   └── workers/
│       ├── __init__.py
│       └── file_cleanup.py
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── initial_migration.py
└── uploads/
    ├── pdfs/
    └── images/
```

## Dependencies

- FastAPI: Web framework
- PyMuPDF (fitz): For PDF text and image extraction
- pdfplumber: For PDF table extraction
- Pillow (PIL): For image processing
- SQLAlchemy: ORM for database operations
- Alembic: Database migration tool
- PostgreSQL: Relational database
- APScheduler: Task scheduling for background jobs
- uvicorn: ASGI server

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/pdf-extractor.git
cd pdf-extractor
```

2. Install Poetry (if not already installed):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

3. Install the dependencies:
```bash
poetry install
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env file as needed
```

## Running the Application

### Using Poetry (Local Development)

```bash
# Using Poetry
poetry run python -m app.main

# Or using uvicorn directly
poetry run uvicorn app.main:app --reload
```

### Using Docker

1. Build and start the Docker container:
```bash
# Build the image
docker-compose build

# Start the container
docker-compose up -d
```

2. Or use the Makefile (recommended):
```bash
# Show available commands
make help

# Build the image
make build

# Start the container
make up

# View logs
make logs

# Get a shell in the container
make shell

# Stop the container
make down

# Clean up all resources
make clean
```


The application will be available at http://localhost:8000.

API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

- `POST /api/v1/extract`: Upload a PDF file to extract text, tables, and images
- `GET /api/v1/documents/{document_id}`: Get previously processed PDF by ID
- `GET /api/v1/documents`: List all processed PDFs with pagination
- `GET /api/v1/images/{filename}`: Download an extracted image
- `GET /api/v1/workers/status`: Get the status of background workers
- `GET /health`: Health check endpoint
- `GET /`: Welcome message and links to documentation

## Features

- **PDF Extraction**: Extract text, tables, and images from PDF files
- **Database Storage**: Store extracted content in PostgreSQL database
- **ID-Based References**: Track all content with unique document IDs
- **Automatic Cleanup**: Background worker removes files after retention period (default: 10 minutes)
- **RESTful API**: Clean API for interacting with the service
- **Dockerized**: Easy deployment with Docker Compose

![diagram (1)](https://github.com/user-attachments/assets/c1035f73-8e24-4327-bc62-f91878040e18)

## Examples

### Extract content from a PDF file

```bash
curl -X POST "http://localhost:8000/api/v1/extract" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/document.pdf"
```

Response:
```json
{
  "id": "ff8c7e4a-1234-5678-9abc-def012345678",
  "filename": "document.pdf",
  "text": {
    "pages": {
      "Page 1": "Text content from page 1...",
      "Page 2": "Text content from page 2..."
    }
  },
  "tables": {
    "pages": {
      "Page 1": [
        [["Header 1", "Header 2"], ["Value 1", "Value 2"]]
      ]
    }
  },
  "images": [
    {
      "url": "/api/v1/images/ff8c7e4a-1234-5678-9abc-def012345678_page_1_image_1.png",
      "page": 1,
      "index": 1,
      "filename": "ff8c7e4a-1234-5678-9abc-def012345678_page_1_image_1.png",
      "document_id": "ff8c7e4a-1234-5678-9abc-def012345678"
    }
  ],
  "created_at": "2023-01-01T12:00:00Z"
}
```

### Get a processed PDF by ID

```bash
curl -X GET "http://localhost:8000/api/v1/documents/ff8c7e4a-1234-5678-9abc-def012345678" \
  -H "accept: application/json"
```

### List all processed PDFs

```bash
curl -X GET "http://localhost:8000/api/v1/documents?skip=0&limit=10" \
  -H "accept: application/json"
```

Response:
```json
{
  "documents": [
    {
      "id": "ff8c7e4a-1234-5678-9abc-def012345678",
      "filename": "document.pdf",
      "original_filename": "document.pdf",
      "created_at": "2023-01-01T12:00:00Z",
      "updated_at": null
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 10
}

## License

MIT
