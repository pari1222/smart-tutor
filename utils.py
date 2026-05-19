"""
Utility functions for the AI Tutor backend.
"""

import os
import logging
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

MAX_FILE_SIZE_MB = 50


def save_upload_file(file_bytes: bytes, filename: str) -> str:
    """Save uploaded bytes to a temp file, return the path."""
    if len(file_bytes) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise ValueError(f"File too large (max {MAX_FILE_SIZE_MB}MB)")

    suffix = Path(filename).suffix or ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file_bytes)
        return tmp.name


def cleanup_temp_file(filepath: str) -> None:
    """Safely delete a temp file."""
    try:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        logger.warning(f"Cleanup failed: {e}")


def validate_pdf(filename: str) -> bool:
    """Basic PDF filename check."""
    return bool(filename) and filename.lower().endswith(".pdf")
