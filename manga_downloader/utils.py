"""
Utility functions for manga downloader
"""

import re
import shutil
import time
from pathlib import Path


def clean_filename(filename: str) -> str:
    """
    Clean filename by removing or replacing invalid characters.

    Args:
        filename: Original filename string

    Returns:
        Cleaned filename safe for filesystem use
    """
    # Remove or replace special characters that are invalid in filenames
    special_chars = ["<", ">", ":", '"', "/", "\\", "|", "?", "*", ","]

    for char in special_chars:
        filename = filename.replace(char, '-')

    # Remove newlines and tabs
    filename = filename.replace('\n', '').replace('\t', '')

    # Strip whitespace from start and end
    filename = filename.strip()

    # Remove multiple consecutive spaces
    filename = re.sub(r'\s+', ' ', filename)

    # Ensure filename isn't empty
    if not filename:
        filename = "Unknown"

    return filename


def extract_chapter_number(chapter_text: str) -> str:
    """
    Extract chapter number from chapter text for sorting purposes.

    Args:
        chapter_text: Chapter name/title text

    Returns:
        Zero-padded chapter number string (e.g., "001", "023")
    """
    # Find all numbers in the text
    numbers = re.findall(r'\d+', chapter_text)

    if numbers:
        # Use the first number found and pad with zeros
        return numbers[0].zfill(3)
    else:
        # If no numbers found, return "000"
        return "000"


def safe_delete_folder(folder_path: Path, retries: int = 3, delay: float = 1.0) -> bool:
    """
    Safely delete a folder with retry logic.

    Args:
        folder_path: Path to folder to delete
        retries: Number of retry attempts
        delay: Delay between retries in seconds

    Returns:
        True if successfully deleted, False otherwise
    """
    if not folder_path.exists():
        return True

    for attempt in range(retries):
        try:
            shutil.rmtree(folder_path)
            return True
        except PermissionError as e:
            if attempt < retries - 1:
                time.sleep(delay)
                continue
            else:
                print(f"Warning: Could not delete temporary folder '{folder_path}': {e}")
                return False
        except Exception as e:
            print(f"Warning: Unexpected error deleting folder '{folder_path}': {e}")
            return False

    return False


def create_directory_safe(path: Path) -> bool:
    """
    Safely create directory with error handling.

    Args:
        path: Directory path to create

    Returns:
        True if created successfully, False otherwise
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory '{path}': {e}")
        return False


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB"]
    size_index = 0
    size = float(size_bytes)

    while size >= 1024.0 and size_index < len(size_names) - 1:
        size /= 1024.0
        size_index += 1

    return f"{size:.1f} {size_names[size_index]}"


def validate_url(url: str) -> bool:
    """
    Basic URL validation.

    Args:
        url: URL string to validate

    Returns:
        True if URL appears valid, False otherwise
    """
    if not url or not isinstance(url, str):
        return False

    # Basic URL pattern check
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    return url_pattern.match(url) is not None


def progress_bar(current: int, total: int, width: int = 50) -> str:
    """
    Generate a progress bar string.

    Args:
        current: Current progress value
        total: Total progress value
        width: Width of progress bar in characters

    Returns:
        Progress bar string
    """
    if total == 0:
        percent = 0
    else:
        percent = min(100, int((current / total) * 100))

    filled = int((current / total) * width) if total > 0 else 0
    bar = '█' * filled + '░' * (width - filled)

    return f"[{bar}] {percent}% ({current}/{total})"