"""
Image downloading and CBZ creation functionality
"""

import io
import requests
import tempfile
import zipfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from urllib.parse import urlparse

from manga_downloader.utils import safe_delete_folder, format_file_size


class ImageDownloader:
    """Handles downloading images and creating CBZ files."""

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.timeout = 30
        self.max_retries = 3

    def download_image(self, url: str, timeout: int | None = None) -> bytes | None:
        """
        Download image from URL with retry logic.

        Args:
            url: Image URL to download
            timeout: Request timeout in seconds

        Returns:
            Image data as bytes, or None if download failed
        """
        if timeout is None:
            timeout = self.timeout

        for attempt in range(self.max_retries):
            try:
                # Add referer header for some sites
                headers = self.session.headers.copy()
                if urlparse(url).netloc:
                    headers['Referer'] = f"https://{urlparse(url).netloc}/"

                response = self.session.get(url, headers=headers, timeout=timeout, stream=True)
                response.raise_for_status()

                # Read image data
                image_data = response.content

                # Verify it's a valid image
                if self._verify_image(image_data):
                    return image_data
                else:
                    print(f"    Warning: Invalid image data from {url}")

            except requests.RequestException as e:
                print(f"    Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self.max_retries - 1:
                    continue
            except Exception as e:
                print(f"    Unexpected error downloading {url}: {e}")
                break

        # If all attempts failed, create a placeholder image
        return self._create_placeholder_image(url)

    def _verify_image(self, image_data: bytes) -> bool:
        """
        Verify that image data is valid.

        Args:
            image_data: Raw image bytes

        Returns:
            True if image is valid, False otherwise
        """
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                img.verify()
            return True
        except Exception:
            return False

    def _create_placeholder_image(self, url: str) -> bytes:
        """
        Create placeholder image when download fails.

        Args:
            url: Original URL that failed

        Returns:
            Placeholder image as bytes
        """
        # Create a simple placeholder image
        img = Image.new('RGB', (800, 600), color=(240, 240, 240))
        draw = ImageDraw.Draw(img)

        try:
            # Try to use a default font
            font = ImageFont.load_default()
        except Exception:
            font = None

        # Draw error message
        text_lines = [
            "Failed to download image",
            "",
            f"URL: {url[:60]}{'...' if len(url) > 60 else ''}",
            "",
            "This is a placeholder image"
        ]

        y_offset = 100
        for line in text_lines:
            if font:
                draw.text((50, y_offset), line, fill=(100, 100, 100), font=font)
            else:
                draw.text((50, y_offset), line, fill=(100, 100, 100))
            y_offset += 30

        # Save to bytes
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        return img_buffer.getvalue()

    def create_cbz(self, image_urls: list[str], output_path: Path, chapter_name: str) -> bool:
        """
        Download images and create CBZ file.

        Args:
            image_urls: List of image URLs to download
            output_path: Path where CBZ file should be saved
            chapter_name: Name of the chapter for progress display

        Returns:
            True if CBZ was created successfully, False otherwise
        """
        if not image_urls:
            print(f"    No images to download for {chapter_name}")
            return False

        # Create temporary directory for images
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            print(f"    Downloading {len(image_urls)} images...")

            # Download all images
            downloaded_images: list[tuple[Path, int]] = []

            for i, url in enumerate(image_urls, 1):
                image_data = self.download_image(url)

                if image_data:
                    # Determine file extension from image data
                    extension = self._get_image_extension(image_data)

                    # Save with zero-padded number for proper sorting
                    image_filename = f"{i:03d}.{extension}"
                    image_path = temp_path / image_filename

                    with open(image_path, 'wb') as f:
                        f.write(image_data)

                    downloaded_images.append((image_path, len(image_data)))

                    # Progress feedback
                    if i % 5 == 0 or i == len(image_urls):
                        print(f"    Progress: {i}/{len(image_urls)} images downloaded")
                else:
                    print(f"    Failed to download image {i}")

            if not downloaded_images:
                print(f"    No images were successfully downloaded for {chapter_name}")
                return False

            # Create CBZ file
            try:
                return self._create_zip_file(downloaded_images, output_path)
            except Exception as e:
                print(f"    Error creating CBZ file: {e}")
                return False

    def _get_image_extension(self, image_data: bytes) -> str:
        """
        Determine image file extension from image data.

        Args:
            image_data: Raw image bytes

        Returns:
            File extension (without dot)
        """
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                format_name = img.format
                if format_name:
                    return format_name.lower()
        except Exception:
            pass

        # Fallback to jpg
        return 'jpg'

    def _create_zip_file(self, image_files: list[tuple[Path, int]], output_path: Path) -> bool:
        """
        Create CBZ (ZIP) file from downloaded images.

        Args:
            image_files: List of (image_path, file_size) tuples
            output_path: Output CBZ file path

        Returns:
            True if successful, False otherwise
        """
        try:
            total_size = sum(size for _, size in image_files)

            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_STORED) as cbz_file:
                for image_path, _ in image_files:
                    # Add file to CBZ with just the filename (no directory structure)
                    cbz_file.write(image_path, image_path.name)

            # Verify the CBZ was created and get its size
            if output_path.exists():
                cbz_size = output_path.stat().st_size
                print(f"    CBZ created: {format_file_size(cbz_size)} "
                      f"({len(image_files)} images, {format_file_size(total_size)} total)")
                return True
            else:
                print(f"    Error: CBZ file was not created")
                return False

        except Exception as e:
            print(f"    Error creating CBZ: {e}")
            return False