"""
Batoto manga processor implementation
"""

import json
import re
import requests
from bs4 import BeautifulSoup, Tag
from pathlib import Path

from manga_downloader.processors import MangaProcessor
from manga_downloader.utils import clean_filename, extract_chapter_number
from manga_downloader.downloader import ImageDownloader


class BatotoProcessor(MangaProcessor):
    """Processor for Batoto manga sites (bato.to, dto.to)."""

    def __init__(self) -> None:
        super().__init__()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.downloader = ImageDownloader()

    def extract_series_info(self, url: str) -> tuple[str, list[str], list[str]]:
        """Extract series information from Batoto main page."""
        self._log(f"Extracting series info from: {url}")

        response = self.session.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract series name
        series_name = self._extract_series_name(soup)
        self._log(f"Found series: {series_name}")

        # Extract chapter links and names
        chapter_urls, chapter_names = self._extract_chapters(soup, url)

        self._log(f"Found {len(chapter_urls)} chapters")

        return series_name, chapter_names, chapter_urls

    def _extract_series_name(self, soup: BeautifulSoup) -> str:
        """Extract series name from the page."""
        name_element = soup.find('h3', class_='item-title')
        if name_element and isinstance(name_element, Tag):
            return clean_filename(name_element.get_text().strip())

        # Fallback to any h3 element
        h3_elements = soup.find_all('h3')
        if h3_elements:
            return clean_filename(h3_elements[0].get_text().strip())

        raise ValueError("Could not extract series name from page")

    def _extract_chapters(self, soup: BeautifulSoup, base_url: str) -> tuple[list[str], list[str]]:
        """Extract chapter URLs and names."""
        all_links = []
        for link in soup.find_all('a'):
            href = link.get('href')
            if href:
                all_links.append(href)

        # Filter for chapter links
        chapter_links = [link for link in all_links if link and '/chapter/' in link]

        # Extract chapter names
        chapter_names = []
        episode_elements = soup.find_all('a', class_='visited chapt')

        for element in episode_elements:
            if isinstance(element, Tag):
                chapter_text = element.get_text().strip()
                if chapter_text.startswith('[') and chapter_text.endswith(']'):
                    chapter_text = chapter_text[1:-1]  # Remove brackets
                chapter_names.append(chapter_text)

        # Ensure we have matching counts
        if len(chapter_links) != len(chapter_names):
            self._log(f"Mismatch: {len(chapter_links)} links vs {len(chapter_names)} names")
            # Use generic names if needed
            chapter_names = [f"Chapter {i + 1}" for i in range(len(chapter_links))]

        # Reverse for proper order (oldest first)
        chapter_links.reverse()
        chapter_names.reverse()

        return chapter_links, chapter_names

    def extract_chapter_images(self, chapter_url: str) -> tuple[list[str], str]:
        """Extract image URLs from a Batoto chapter page."""
        # Construct full URL if needed
        if not chapter_url.startswith('http'):
            chapter_url = f"https://batocomic.com{chapter_url}"

        self._log(f"Extracting images from: {chapter_url}")

        response = self.session.get(chapter_url, allow_redirects=True, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract image URLs from JavaScript
        img_urls = self._extract_image_urls_from_js(soup)

        # Extract chapter name from JavaScript
        chapter_name = self._extract_chapter_name_from_js(soup)

        if not img_urls:
            raise ValueError(f"No images found in chapter: {chapter_url}")

        self._log(f"Found {len(img_urls)} images in chapter: {chapter_name}")

        return img_urls, chapter_name

    def _extract_image_urls_from_js(self, soup: BeautifulSoup) -> list[str]:
        """Extract image URLs from JavaScript variables."""
        script_tags = soup.find_all('script')

        for script in script_tags:
            if not script.string:
                continue

            # Look for imgHttps variable
            img_https_match = re.search(r'imgHttps\s*=\s*(\[[^\]]+\])', script.string)
            if img_https_match:
                try:
                    img_urls = json.loads(img_https_match.group(1))
                    return [url for url in img_urls if url and isinstance(url, str)]
                except json.JSONDecodeError:
                    continue

        return []

    def _extract_chapter_name_from_js(self, soup: BeautifulSoup) -> str:
        """Extract chapter name from JavaScript variables."""
        script_tags = soup.find_all('script')

        for script in script_tags:
            if not script.string:
                continue

            # Look for local_text_epi variable
            epi_match = re.search(r'local_text_epi\s*=\s*(\'[^\']+\')', script.string)
            if epi_match:
                chapter_name = epi_match.group(1)[1:-1]  # Remove quotes
                return clean_filename(chapter_name)

        return "Unknown Chapter"

    def download_series(self, series_url: str, output_dir: Path) -> None:
        """Download entire manga series from Batoto."""
        # Extract series information
        series_name, chapter_names, chapter_urls = self.extract_series_info(series_url)

        # Create series directory
        series_dir = output_dir / clean_filename(series_name)
        series_dir.mkdir(parents=True, exist_ok=True)

        print(f"Downloading '{series_name}' ({len(chapter_urls)} chapters)")

        # Download each chapter
        for i, (chapter_url, expected_name) in enumerate(zip(chapter_urls, chapter_names), 1):
            try:
                print(f"[{i}/{len(chapter_urls)}] Processing {expected_name}...")

                # Extract chapter images
                img_urls, actual_chapter_name = self.extract_chapter_images(chapter_url)

                # Use actual chapter name if available, otherwise use expected
                chapter_name = actual_chapter_name if actual_chapter_name != "Unknown Chapter" else expected_name

                # Create CBZ filename with chapter number for sorting
                chapter_num = extract_chapter_number(chapter_name)
                cbz_filename = f"{chapter_num}_{clean_filename(chapter_name)}.cbz"
                cbz_path = series_dir / cbz_filename

                # Skip if already exists
                if cbz_path.exists():
                    print(f"  Skipping (already exists): {cbz_filename}")
                    continue

                # Download and create CBZ
                self.downloader.create_cbz(img_urls, cbz_path, chapter_name)

                print(f"  Completed: {cbz_filename}")

            except Exception as e:
                print(f"  Error processing chapter {i}: {e}")
                if self.verbose:
                    import traceback
                    traceback.print_exc()
                continue

        print(f"\nSeries download completed: {series_dir}")