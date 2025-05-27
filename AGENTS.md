# AGENTS.md - AI Agent Development Guide

This document provides a comprehensive overview of the manga downloader codebase for AI agents working on maintenance, debugging, or extending the system.

## Architecture Overview

### Design Pattern: Strategy Pattern + Template Method
- **Base Class**: `MangaProcessor` (abstract base class)
- **Concrete Implementation**: `BatotoProcessor`
- **Factory Method**: `determine_processor()` in `__main__.py`

The system uses the Strategy pattern to allow different manga site processors while maintaining a consistent interface. Each processor implements site-specific logic while following the same contract.

### Core Components

```
__main__.py (CLI entry point)
    ↓
processors/base.py (Abstract interface)
    ↓
processors/batoto.py (Batoto implementation)
    ↓
downloader.py (Image handling + CBZ creation)
    ↓
utils.py (Utility functions)
```

## File-by-File Analysis

### `__main__.py` - CLI Entry Point
**Purpose**: Command-line interface and application bootstrap
**Key Functions**:
- `determine_processor(url: str) -> BatotoProcessor | None`: URL-based processor selection
- `main() -> None`: Argument parsing and execution flow

**Extension Points**:
- Add new site detection in `determine_processor()`
- Add new CLI arguments in the `argparse` setup

### `processors/base.py` - Abstract Base Class
**Purpose**: Defines the contract for all manga site processors
**Key Methods** (all abstract):
- `extract_series_info()`: Get series name and chapter list
- `extract_chapter_images()`: Get image URLs from a chapter
- `download_series()`: Orchestrate the full download process

**Important**: All new processors MUST implement these three methods

### `processors/batoto.py` - Batoto Implementation
**Purpose**: Handles Batoto-specific scraping logic
**Key Implementation Details**:
- Uses `requests.Session` for connection pooling
- Extracts data from JavaScript variables using regex
- Handles both `bato.to` and `dto.to` domains
- JavaScript parsing targets: `imgHttps` and `local_text_epi` variables

**Scraping Strategy**:
1. Parse main series page for chapter links
2. Extract chapter metadata from `<a class="visited chapt">` elements
3. For each chapter: parse JavaScript variables for image URLs
4. Use session cookies for consistency

### `downloader.py` - Image Downloader
**Purpose**: Downloads images and creates CBZ archives
**Key Features**:
- Retry logic (3 attempts per image)
- Image validation using PIL
- Placeholder creation for failed downloads
- CBZ creation using `zipfile` with `ZIP_STORED` compression

**Error Handling Strategy**:
- Primary: `requests` with custom headers
- Fallback: Placeholder image with error message
- Validation: PIL image verification before saving

### `utils.py` - Utility Functions
**Purpose**: Common functionality shared across components
**Key Functions**:
- `clean_filename()`: Sanitizes filenames for filesystem compatibility
- `extract_chapter_number()`: Extracts and zero-pads chapter numbers for sorting
- `safe_delete_folder()`: Safe temporary directory cleanup
- `format_file_size()`: Human-readable file size formatting

## Type Hinting Strategy

### Comprehensive Coverage
- **ALL** function parameters have type hints
- **ALL** return values have type hints
- **ALL** class attributes have type hints where possible
- Use `T | None` for nullable values
- Use union types like `str | int` when multiple types are valid

### Import Pattern for Type Hints
```python
from pathlib import Path
# No typing imports needed for basic types in Python 3.10+
```

### Complex Types Used
- `tuple[str, list[str], list[str]]`: Series info return type
- `tuple[list[str], str]`: Chapter images return type
- `list[tuple[Path, int]]`: Downloaded images with sizes
- `bytes | None`: Image data that might fail to download

## Error Handling Patterns

### Hierarchical Error Handling
1. **Function Level**: Try/catch specific operations
2. **Method Level**: Log errors and continue or fail gracefully
3. **Class Level**: Handle session/connection errors
4. **Application Level**: Catch-all in `main()` with user-friendly messages

### Error Categories
- **Network Errors**: Retry with exponential backoff
- **Parsing Errors**: Log and skip problematic content
- **File System Errors**: Inform user, don't crash
- **Validation Errors**: Create fallbacks (placeholder images)

## Extension Guide for New Sites

### Step 1: Create New Processor
```python
# processors/newsite.py
from manga_downloader.processors import MangaProcessor
from pathlib import Path

class NewSiteProcessor(MangaProcessor):
    def __init__(self) -> None:
        super().__init__()
        # Site-specific initialization
    
    def extract_series_info(self, url: str) -> tuple[str, list[str], list[str]]:
        # Return: (series_name, chapter_names, chapter_urls)
        pass
    
    def extract_chapter_images(self, chapter_url: str) -> tuple[list[str], str]:
        # Return: (image_urls, chapter_name)
        pass
    
    def download_series(self, series_url: str, output_dir: Path) -> None:
        # Orchestrate full download using base utilities
        pass
```

### Step 2: Add Detection Logic
```python
# In __main__.py determine_processor()
elif 'newsite.com' in url.lower():
    return NewSiteProcessor()
```

### Step 3: Update Package Imports
```python
# processors/__init__.py
from manga_downloader.processors.newsite import NewSiteProcessor
__all__ = ['MangaProcessor', 'BatotoProcessor', 'NewSiteProcessor']
```

## Selenium Integration Points (Future)

### Current State: HTTP-Only
Batoto processor uses `requests` + `BeautifulSoup` for performance and simplicity.

### Selenium Ready Architecture
The processor pattern supports Selenium integration:

```python
from selenium import webdriver
from manga_downloader.processors import MangaProcessor

class JavaScriptProcessor(MangaProcessor):
    def __init__(self) -> None:
        super().__init__()
        self.driver: webdriver.Chrome | None = None
    
    def _init_driver(self) -> None:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        self.driver = webdriver.Chrome(options=options)
    
    def __del__(self) -> None:
        if self.driver:
            self.driver.quit()
```

## Performance Considerations

### Session Reuse
- `requests.Session` objects are reused for connection pooling
- Custom headers set once per processor instance

### Memory Management
- Images processed in streaming mode when possible
- Temporary directories cleaned up automatically
- Large files handled in chunks

### Concurrency Notes
- Current implementation is single-threaded
- Adding concurrency should be done at the chapter level, not image level
- Consider rate limiting for respectful scraping

## Security Considerations

### Input Validation
- URLs validated with regex patterns
- Filenames sanitized against directory traversal
- Image data validated before processing

### Headers and User Agents
- Realistic browser User-Agent strings
- Appropriate Accept headers for image requests
- Referer headers set for some sites

## Debugging Guide

### Common Issues
1. **JavaScript Extraction Failures**: Check regex patterns in `_extract_*_from_js()` methods
2. **Image Download Failures**: Enable verbose mode, check headers and referers
3. **CBZ Creation Issues**: Verify temporary directory permissions and disk space

### Debug Workflow
1. Enable verbose mode: `--verbose`
2. Check network requests with session debugging
3. Validate intermediate data structures
4. Test individual components in isolation

## Code Quality Standards

### Type Checking
- Use `mypy` for static type checking
- Aim for zero type errors
- Use `# type: ignore` sparingly with comments

### Code Formatting
- Follow PEP 8 style guidelines
- Use meaningful variable names
- Keep functions focused and small (< 50 lines when possible)

### Documentation
- All public methods should have docstrings
- Include type information in docstrings
- Document complex algorithms inline

### Dependencies
- Minimize external dependencies
- Prefer standard library when possible

This document should be updated whenever significant architectural changes are made to the codebase.