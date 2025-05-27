"""
Base manga processor class for extensible site support
"""

from abc import ABC, abstractmethod
from pathlib import Path


class MangaProcessor(ABC):
    """Abstract base class for manga site processors."""

    def __init__(self) -> None:
        self.verbose: bool = False

    def set_verbose(self, verbose: bool) -> None:
        """Enable or disable verbose output."""
        self.verbose = verbose

    def _log(self, message: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(f"[DEBUG] {message}")

    @abstractmethod
    def extract_series_info(self, url: str) -> tuple[str, list[str], list[str]]:
        """
        Extract series information from the main series page.

        Args:
            url: Main series page URL

        Returns:
            Tuple of (series_name, chapter_names, chapter_urls)
        """
        pass

    @abstractmethod
    def extract_chapter_images(self, chapter_url: str) -> tuple[list[str], str]:
        """
        Extract image URLs from a chapter page.

        Args:
            chapter_url: URL of the chapter page

        Returns:
            Tuple of (image_urls, chapter_name)
        """
        pass

    @abstractmethod
    def download_series(self, series_url: str, output_dir: Path) -> None:
        """
        Download entire manga series.

        Args:
            series_url: Main series page URL
            output_dir: Directory to save downloaded files
        """
        pass