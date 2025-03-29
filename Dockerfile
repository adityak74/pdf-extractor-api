FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.6.1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    poppler-utils \
    # Dependencies for pdfplumber and PyMuPDF
    libpoppler-dev \
    pkg-config \
    # Clean up
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install "poetry==$POETRY_VERSION"

# Copy poetry configuration files
COPY pyproject.toml poetry.lock* ./

# Install project dependencies
RUN poetry install --no-root --no-dev

# Install APScheduler explicitly to ensure it's available
RUN pip install apscheduler

# Copy project
COPY . .

# Create upload directories
RUN mkdir -p /app/uploads/pdfs /app/uploads/images \
    && chmod -R 777 /app/uploads

# Print configuration for debugging during build
RUN echo "Testing configuration during build:" && python -m app.utils.check_config

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]