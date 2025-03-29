import os
import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.config import settings


def main():
    """Check configuration settings."""
    print("Checking configuration settings...")

    # Print all settings attributes
    print("\nSettings attributes:")
    for attr in dir(settings):
        if not attr.startswith('_') and not callable(getattr(settings, attr)):
            print(f"  {attr}: {getattr(settings, attr)}")

    # Check for FILE_RETENTION_MINUTES specifically
    try:
        retention = settings.FILE_RETENTION_MINUTES
        print(f"\nFILE_RETENTION_MINUTES: {retention}")
    except Exception as e:
        print(f"\nError accessing FILE_RETENTION_MINUTES: {str(e)}")

    # Print environment variables
    print("\nEnvironment variables:")
    for key, value in os.environ.items():
        if "RETENTION" in key or "FILE" in key or key in [
            "DEBUG", "HOST", "PORT", "API_PREFIX", "APP_NAME", "LOG_LEVEL"
        ]:
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()