"""
Manga processors package
"""

from .base import MangaProcessor
from .batoto import BatotoProcessor

__all__ = ['MangaProcessor', 'BatotoProcessor']