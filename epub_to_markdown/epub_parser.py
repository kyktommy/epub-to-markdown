"""
EPUB Parser Module

This module provides functionality to parse EPUB files and extract their content,
metadata, and structure for conversion to markdown format.
"""

import os
import zipfile
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EPUBChapter:
    """Represents a chapter in an EPUB book."""
    title: str
    content: str
    file_name: str
    order: int


@dataclass
class EPUBMetadata:
    """Represents metadata of an EPUB book."""
    title: str
    author: str
    language: str
    identifier: str
    publisher: Optional[str] = None
    description: Optional[str] = None
    rights: Optional[str] = None


class EPUBParser:
    """
    A parser for EPUB files that extracts content, metadata, and structure.
    """
    
    def __init__(self, epub_path: str):
        """
        Initialize the EPUB parser.
        
        Args:
            epub_path (str): Path to the EPUB file
        """
        self.epub_path = epub_path
        self.book = None
        self.metadata = None
        self.chapters = []
        
    def parse(self) -> Tuple[EPUBMetadata, List[EPUBChapter]]:
        """
        Parse the EPUB file and extract metadata and chapters.
        
        Returns:
            Tuple[EPUBMetadata, List[EPUBChapter]]: Metadata and list of chapters
        """
        try:
            # Read the EPUB file
            self.book = epub.read_epub(self.epub_path)
            logger.info(f"Successfully loaded EPUB: {self.epub_path}")
            
            # Extract metadata
            self.metadata = self._extract_metadata()
            
            # Extract chapters
            self.chapters = self._extract_chapters()
            
            return self.metadata, self.chapters
            
        except Exception as e:
            logger.error(f"Error parsing EPUB file: {e}")
            raise
    
    def _extract_metadata(self) -> EPUBMetadata:
        """
        Extract metadata from the EPUB book.
        
        Returns:
            EPUBMetadata: Book metadata
        """
        try:
            title = self.book.get_metadata('DC', 'title')[0][0] if self.book.get_metadata('DC', 'title') else "Unknown Title"
            author = self.book.get_metadata('DC', 'creator')[0][0] if self.book.get_metadata('DC', 'creator') else "Unknown Author"
            language = self.book.get_metadata('DC', 'language')[0][0] if self.book.get_metadata('DC', 'language') else "en"
            identifier = self.book.get_metadata('DC', 'identifier')[0][0] if self.book.get_metadata('DC', 'identifier') else ""
            
            publisher = None
            if self.book.get_metadata('DC', 'publisher'):
                publisher = self.book.get_metadata('DC', 'publisher')[0][0]
            
            description = None
            if self.book.get_metadata('DC', 'description'):
                description = self.book.get_metadata('DC', 'description')[0][0]
            
            rights = None
            if self.book.get_metadata('DC', 'rights'):
                rights = self.book.get_metadata('DC', 'rights')[0][0]
            
            return EPUBMetadata(
                title=title,
                author=author,
                language=language,
                identifier=identifier,
                publisher=publisher,
                description=description,
                rights=rights
            )
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return EPUBMetadata(
                title="Unknown Title",
                author="Unknown Author",
                language="en",
                identifier=""
            )
    
    def _extract_chapters(self) -> List[EPUBChapter]:
        """
        Extract chapters from the EPUB book.
        
        Returns:
            List[EPUBChapter]: List of chapters
        """
        chapters = []
        order = 0
        
        try:
            # Get all items in the book
            for item in self.book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    # Parse HTML content
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    
                    # Extract title (try h1, h2, title tag, or use filename)
                    title = self._extract_chapter_title(soup, item.get_name())
                    
                    # Clean and extract text content
                    content = self._clean_html_content(soup)
                    
                    if content.strip():  # Only add chapters with content
                        chapter = EPUBChapter(
                            title=title,
                            content=content,
                            file_name=item.get_name(),
                            order=order
                        )
                        chapters.append(chapter)
                        order += 1
                        
            logger.info(f"Extracted {len(chapters)} chapters")
            return chapters
            
        except Exception as e:
            logger.error(f"Error extracting chapters: {e}")
            return []
    
    def _extract_chapter_title(self, soup: BeautifulSoup, filename: str) -> str:
        """
        Extract chapter title from HTML content.
        
        Args:
            soup (BeautifulSoup): Parsed HTML content
            filename (str): Filename as fallback
            
        Returns:
            str: Chapter title
        """
        # Try to find title in various tags
        for tag in ['h1', 'h2', 'h3', 'title']:
            element = soup.find(tag)
            if element and element.get_text().strip():
                return element.get_text().strip()
        
        # Use filename as fallback
        return os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ').title()
    
    def _clean_html_content(self, soup: BeautifulSoup) -> str:
        """
        Clean HTML content and extract readable text.
        
        Args:
            soup (BeautifulSoup): Parsed HTML content
            
        Returns:
            str: Cleaned text content
        """
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text and clean it up
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
