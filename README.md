# Manga Downloader

A Python tool for downloading manga series as CBZ files from supported websites.

## Features

- **Batoto Support**: Download from bato.to and dto.to
- **CBZ Format**: Creates comic book archive files (CBZ) compatible with most comic readers
- **Full Series Download**: Always downloads all available chapters
- **Type-Hinted**: Fully type-hinted codebase for better development experience
- **Extensible Architecture**: Easy to add support for new manga sites
- **CLI Interface**: Simple command-line interface
- **Error Handling**: Robust error handling with retry logic for failed downloads

## Installation

1. Clone or download this repository
2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

3. **Important**: You need to have Chrome/Chromium browser installed for sites that require Selenium (future extensions)

## Usage

### Basic Usage

```bash
# Download a manga series
poetry run manga-downloader "https://dto.to/series/120046"

# Specify output directory
poetry run manga-downloader "https://dto.to/series/120046" -o /path/to/downloads

# Enable verbose output
poetry run manga-downloader "https://dto.to/series/120046" --verbose
```

### Command Line Options

- `url`: Manga series URL (required)
- `-o, --output`: Output directory (default: ./downloads)
- `-v, --verbose`: Enable verbose output
- `-h, --help`: Show help message

## Supported Sites

Currently supported:
- **Batoto**: bato.to, dto.to

## Output Format

- Downloads are saved as CBZ files (ZIP archives containing images)
- Files are named with chapter numbers for proper sorting: `001_Chapter-Name.cbz`
- Each series gets its own folder
- CBZ files can be opened with comic readers like CDisplayEx, Perfect Viewer, etc.

## Project Structure

```
manga-downloader/
├── __main__.py            # CLI entry point
├── utils.py               # Utility functions
├── downloader.py          # Image downloading and CBZ creation
├── processors/
│   ├── __init__.py
│   ├── base.py           # Base processor class
│   └── batoto.py         # Batoto implementation
├── pyproject.toml        # Poetry configuration
└── README.md             # This file
```

## Adding New Sites

To add support for a new manga site:

1. Create a new processor in `processors/` (e.g., `processors/newsite.py`)
2. Inherit from `MangaProcessor` and implement required methods:
   - `extract_series_info()`
   - `extract_chapter_images()`
   - `download_series()`
3. Add detection logic in `__main__.py`'s `determine_processor()` function
4. Update the imports in `processors/__init__.py`

Example:

```python
# processors/newsite.py
from pathlib import Path

from manga_downloader.processors import MangaProcessor

class NewSiteProcessor(MangaProcessor):
    def extract_series_info(self, url: str) -> tuple[str, list[str], list[str]]:
        # Implementation here
        pass
    
    def extract_chapter_images(self, chapter_url: str) -> tuple[list[str], str]:
        # Implementation here  
        pass
    
    def download_series(self, series_url: str, output_dir: Path) -> None:
        # Implementation here
        pass
```

## Error Handling

The downloader includes several error handling mechanisms:

- **Retry Logic**: Failed downloads are retried up to 3 times
- **Placeholder Images**: If an image fails to download, a placeholder is created
- **Graceful Degradation**: Individual chapter failures don't stop the entire download
- **Validation**: URLs and image data are validated before processing

## Troubleshooting

### Common Issues

1. **"Unsupported URL" error**: Make sure you're using a supported site (currently only Batoto)
2. **Download failures**: Check your internet connection and try running with `--verbose` for more details
3. **Permission errors**: Make sure you have write permissions to the output directory

### Debug Mode

Use the `--verbose` flag to see detailed information about the download process:

```bash
python __main__.py "https://dto.to/series/120046" --verbose
```

## License

This project is for educational purposes. Please respect the terms of service of the websites you're downloading from and support the manga creators by purchasing official releases when available.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add type hints to all new code
5. Test your changes
6. Submit a pull request

When adding new site support, please ensure:
- Full type hinting
- Proper error handling
- Consistent naming conventions
- Documentation for new methods