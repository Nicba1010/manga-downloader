"""
Manga Downloader - CLI Entry Point
Supports Batoto with extensible architecture for other sites
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from manga_downloader.processors.batoto import BatotoProcessor


def determine_processor(url: str) -> Optional[BatotoProcessor]:
    """Determine which processor to use based on URL."""
    if 'bato' in url.lower() or 'dto' in url.lower():
        return BatotoProcessor()
    return None


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Download manga series as CBZ files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py https://dto.to/series/120046
  python main.py https://bato.to/series/12345 -o /path/to/downloads
        """
    )

    parser.add_argument(
        'url',
        help='Manga series URL to download'
    )

    parser.add_argument(
        '-o', '--output',
        type=Path,
        default=Path.cwd() / 'downloads',
        help='Output directory (default: ./downloads)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    # Determine processor
    processor = determine_processor(args.url)
    if processor is None:
        print(f"Error: Unsupported URL - {args.url}")
        print("Currently supported sites: Batoto (bato.to, dto.to)")
        sys.exit(1)

    # Set verbosity
    if args.verbose:
        processor.set_verbose(True)

    # Create output directory
    args.output.mkdir(parents=True, exist_ok=True)

    try:
        print(f"Starting download from: {args.url}")
        print(f"Output directory: {args.output}")

        processor.download_series(args.url, args.output)

        print("\nDownload completed successfully!")

    except KeyboardInterrupt:
        print("\nDownload interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()