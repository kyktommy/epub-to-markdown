"""
EPUB Parser Module

This module provides functionality to parse EPUB files and extract their content,
metadata, and structure for conversion to markdown format.
"""

import os
import re
import zipfile
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import logging

from .image_extractor import ImageExtractor, EPUBImage

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
    images: List[EPUBImage] = field(default_factory=list)


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
    
    def __init__(self, epub_path: str, extract_images: bool = True, output_dir: str = "output", single_file_mode: bool = True):
        """
        Initialize the EPUB parser.

        Args:
            epub_path (str): Path to the EPUB file
            extract_images (bool): Whether to extract and process images (only for multiple files mode)
            output_dir (str): Output directory for processed images
            single_file_mode (bool): Whether converting to single file (disables image extraction)
        """
        self.epub_path = epub_path
        self.extract_images = extract_images and not single_file_mode  # Only extract in multiple files mode
        self.output_dir = output_dir
        self.single_file_mode = single_file_mode
        self.book = None
        self.metadata = None
        self.chapters = []
        self.image_extractor = None

        # Only create image extractor for EPUB files in multiple files mode
        if self.extract_images and epub_path.lower().endswith('.epub'):
            self.image_extractor = ImageExtractor(output_dir)
        
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

            # Extract images if enabled (only for EPUB files in multiple files mode)
            if self.extract_images and self.image_extractor and not self.single_file_mode:
                self._extract_and_process_images()

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
                raw_publisher = self.book.get_metadata('DC', 'publisher')[0][0]
                publisher = self._clean_metadata_text(raw_publisher)

            description = None
            if self.book.get_metadata('DC', 'description'):
                raw_description = self.book.get_metadata('DC', 'description')[0][0]
                description = self._clean_metadata_text(raw_description)

            rights = None
            if self.book.get_metadata('DC', 'rights'):
                raw_rights = self.book.get_metadata('DC', 'rights')[0][0]
                rights = self._clean_metadata_text(raw_rights)

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

    def _clean_metadata_text(self, text: str) -> str:
        """
        Clean metadata text that may contain HTML tags and convert to plain text.

        Args:
            text (str): Raw metadata text that may contain HTML

        Returns:
            str: Cleaned plain text
        """
        if not text or not text.strip():
            return text

        # Check if the text contains HTML tags
        if '<' in text and '>' in text:
            try:
                # Parse as HTML and extract text
                soup = BeautifulSoup(text, 'html.parser')

                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()

                # Get text with separator to handle adjacent elements
                cleaned_text = soup.get_text(separator=' ')

                # Clean up whitespace and fix spacing around punctuation
                lines = (line.strip() for line in cleaned_text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                cleaned_text = ' '.join(chunk for chunk in chunks if chunk)

                # Fix spacing around punctuation (remove space before punctuation)
                cleaned_text = re.sub(r'\s+([.!?,:;])', r'\1', cleaned_text)

                return cleaned_text
            except Exception as e:
                logger.warning(f"Error parsing HTML in metadata text: {e}")
                # Fallback to original text if HTML parsing fails
                return text.strip()

        # If no HTML tags detected, just clean up whitespace
        return text.strip()

    def _extract_and_process_images(self):
        """Extract and process images from the EPUB, associating them with chapters."""
        try:
            # Prepare chapter data for image extraction
            chapters_data = []
            for chapter in self.chapters:
                # Get the original HTML content for image processing
                for item in self.book.get_items():
                    if item.get_type() == ebooklib.ITEM_DOCUMENT and item.get_name() == chapter.file_name:
                        chapters_data.append({
                            'title': chapter.title,
                            'content': item.get_content().decode('utf-8'),
                            'file_name': chapter.file_name
                        })
                        break

            # Extract images using the image extractor
            extracted_images = self.image_extractor.extract_images_from_epub(self.book, chapters_data)

            # Associate images with chapters
            for image in extracted_images:
                # Find the chapter this image belongs to
                chapter_index = image.page_number - 1  # page_number is 1-based
                if 0 <= chapter_index < len(self.chapters):
                    self.chapters[chapter_index].images.append(image)

            logger.info(f"Associated {len(extracted_images)} images with chapters")

        except Exception as e:
            logger.error(f"Error extracting images: {e}")
            # Don't fail the entire parsing process if image extraction fails
