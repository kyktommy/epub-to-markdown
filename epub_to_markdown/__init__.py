"""
EPUB to Markdown Converter

A Python library for parsing EPUB files and converting them to markdown format.
"""

__version__ = "0.1.0"
__author__ = "kyktommy"

from .epub_parser import EPUBParser
from .markdown_converter import MarkdownConverter
from .cli import cli, main

__all__ = ["EPUBParser", "MarkdownConverter", "cli", "main"]
