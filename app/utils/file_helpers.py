"""
File handling utilities
"""
import re
from app.config.constants import ALLOWED_EXTENSIONS, CODE_FILE_EXTENSIONS


def allowed_file(filename):
    """Check if file extension is allowed for DocIQ"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_extension(filename):
    """Get file extension from filename"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''


def get_code_file_extension(language):
    """Get file extension for code execution"""
    return CODE_FILE_EXTENSIONS.get(language, 'txt')


def secure_filename(filename: str) -> str:
    """Sanitise a filename (replaces werkzeug.utils.secure_filename)."""
    # Keep only word chars, whitespace, hyphens and dots
    filename = re.sub(r'[^\w\s\-.]', '', filename)
    # Collapse whitespace to underscores
    filename = re.sub(r'\s+', '_', filename).strip('._')
    return filename or 'unnamed'
