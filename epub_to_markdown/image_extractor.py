"""
Image Extractor Module

This module provides functionality to extract, process, and optimize images from EPUB files.
Images are compressed using mozjpeg, resized to max 1920x1080, and labeled with captions and page numbers.
"""

import os
import re
import tempfile
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EPUBImage:
    """Represents an image extracted from an EPUB book."""
    filename: str
    original_path: str
    processed_path: str
    caption: Optional[str] = None
    alt_text: Optional[str] = None
    page_number: int = 0
    chapter_title: str = ""
    width: int = 0
    height: int = 0
    file_size: int = 0


class ImageExtractor:
    """
    Extracts and processes images from EPUB files.
    """
    
    def __init__(self, output_dir: str, max_width: int = 1920, max_height: int = 1080):
        """
        Initialize the image extractor.

        Args:
            output_dir (str): Directory to save processed images
            max_width (int): Maximum image width
            max_height (int): Maximum image height
        """
        self.output_dir = output_dir
        self.max_width = max_width
        self.max_height = max_height
        self.images_dir = os.path.join(output_dir, "images")
        self.used_filenames = set()  # Track used filenames to avoid conflicts
        os.makedirs(self.images_dir, exist_ok=True)
        
    def extract_images_from_epub(self, book: epub.EpubBook, chapters_data: List[Dict]) -> List[EPUBImage]:
        """
        Extract all images from an EPUB book.
        
        Args:
            book (epub.EpubBook): The EPUB book object
            chapters_data (List[Dict]): Chapter data with HTML content
            
        Returns:
            List[EPUBImage]: List of extracted and processed images
        """
        extracted_images = []
        image_counter = 1
        
        try:
            # Get all image items from the book
            image_items = {}
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_IMAGE:
                    image_items[item.get_name()] = item
            
            logger.info(f"Found {len(image_items)} images in EPUB")
            
            # Process images found in chapters
            for chapter_idx, chapter_data in enumerate(chapters_data):
                soup = BeautifulSoup(chapter_data['content'], 'html.parser')
                img_tags = soup.find_all('img')
                
                for img_tag in img_tags:
                    src = img_tag.get('src', '')
                    if not src:
                        continue
                    
                    # Clean up the image path
                    img_path = self._clean_image_path(src)
                    
                    # Find the corresponding image item
                    matching_item = self._find_matching_image_item(img_path, image_items)
                    if not matching_item:
                        logger.warning(f"Image not found in EPUB: {img_path}")
                        continue
                    
                    # Extract image metadata
                    caption = self._extract_image_caption(img_tag, soup)
                    alt_text = img_tag.get('alt', '')
                    
                    # Process the image
                    processed_image = self._process_image(
                        matching_item,
                        image_counter,
                        chapter_idx + 1,
                        chapter_data.get('title', ''),
                        caption,
                        alt_text
                    )
                    
                    if processed_image:
                        extracted_images.append(processed_image)
                        image_counter += 1
            
            logger.info(f"Successfully processed {len(extracted_images)} images")
            return extracted_images
            
        except Exception as e:
            logger.error(f"Error extracting images: {e}")
            return []
    
    def _clean_image_path(self, src: str) -> str:
        """Clean and normalize image path."""
        # Remove leading slashes and resolve relative paths
        src = src.lstrip('/')
        # Handle relative paths like ../images/image.jpg
        src = os.path.normpath(src)
        return src
    
    def _find_matching_image_item(self, img_path: str, image_items: Dict) -> Optional[ebooklib.epub.EpubItem]:
        """Find matching image item in the EPUB."""
        # Try exact match first
        if img_path in image_items:
            return image_items[img_path]
        
        # Try matching by filename
        img_filename = os.path.basename(img_path)
        for item_path, item in image_items.items():
            if os.path.basename(item_path) == img_filename:
                return item
        
        # Try partial matching
        for item_path, item in image_items.items():
            if img_path in item_path or item_path.endswith(img_path):
                return item
        
        return None
    
    def _extract_image_caption(self, img_tag, soup: BeautifulSoup) -> Optional[str]:
        """Extract caption from image context."""
        # Look for figcaption
        parent = img_tag.parent
        if parent and parent.name == 'figure':
            figcaption = parent.find('figcaption')
            if figcaption:
                caption = figcaption.get_text().strip()
                if caption:
                    return caption

        # Look for alt text as caption
        alt_text = img_tag.get('alt', '').strip()
        if alt_text and len(alt_text) > 3 and len(alt_text) < 100:
            return alt_text

        # Look for title attribute
        title_text = img_tag.get('title', '').strip()
        if title_text and len(title_text) > 3 and len(title_text) < 100:
            return title_text

        # Look for nearby text that might be a caption
        # Check for text in the same paragraph or following paragraph
        if parent:
            text = parent.get_text().strip()
            # If the parent has more text than just the alt text, it might be a caption
            if text and text != alt_text and len(text) > 3 and len(text) < 150:
                # Clean up the text
                text = re.sub(r'\s+', ' ', text)
                return text

        # Look for previous or next sibling that might contain caption
        if parent:
            for sibling in [parent.previous_sibling, parent.next_sibling]:
                if sibling and hasattr(sibling, 'get_text'):
                    sibling_text = sibling.get_text().strip()
                    if sibling_text and len(sibling_text) > 3 and len(sibling_text) < 100:
                        return sibling_text

        return None
    
    def _process_image(self, image_item: ebooklib.epub.EpubItem, image_number: int,
                      page_number: int, chapter_title: str, caption: Optional[str],
                      alt_text: str) -> Optional[EPUBImage]:
        """
        Process a single image: resize, compress, and add labels.

        Args:
            image_item: EPUB image item
            image_number: Sequential image number
            page_number: Page/chapter number
            chapter_title: Title of the chapter
            caption: Image caption
            alt_text: Alt text

        Returns:
            EPUBImage: Processed image data
        """
        try:
            # Get image data
            image_data = image_item.get_content()
            original_filename = os.path.basename(image_item.get_name())

            # Create processed filename based on priority: caption > page number > chapter number
            if caption and caption.strip():
                # Use caption as filename
                base_name = self._sanitize_filename(caption.strip())
                processed_filename = self._get_unique_filename(f"{base_name}.jpg")
            elif page_number:
                # Use page number
                processed_filename = self._get_unique_filename(f"page_{page_number:03d}.jpg")
            else:
                # Use chapter number in sequence
                processed_filename = self._get_unique_filename(f"chapter_{image_number:03d}.jpg")

            processed_path = os.path.join(self.images_dir, processed_filename)
            
            # Save original image temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.tmp') as temp_file:
                temp_file.write(image_data)
                temp_path = temp_file.name
            
            try:
                # Open and process image
                with Image.open(temp_path) as img:
                    # Convert to RGB if necessary
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Resize if necessary
                    img = self._resize_image(img)
                    
                    # Save as JPEG with mozjpeg optimization
                    self._save_optimized_jpeg(img, processed_path)
                    
                    # Get file size
                    file_size = os.path.getsize(processed_path)
                    
                    return EPUBImage(
                        filename=processed_filename,
                        original_path=image_item.get_name(),
                        processed_path=processed_path,
                        caption=caption,
                        alt_text=alt_text,
                        page_number=page_number,
                        chapter_title=chapter_title,
                        width=img.width,
                        height=img.height,
                        file_size=file_size
                    )
                    
            finally:
                # Clean up temporary file
                os.unlink(temp_path)
                
        except Exception as e:
            logger.error(f"Error processing image {original_filename}: {e}")
            return None
    
    def _resize_image(self, img: Image.Image) -> Image.Image:
        """Resize image to fit within max dimensions while maintaining aspect ratio."""
        width, height = img.size
        
        if width <= self.max_width and height <= self.max_height:
            return img
        
        # Calculate scaling factor
        width_ratio = self.max_width / width
        height_ratio = self.max_height / height
        scale_factor = min(width_ratio, height_ratio)
        
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        
        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def _save_optimized_jpeg(self, img: Image.Image, output_path: str):
        """Save image as optimized JPEG using mozjpeg if available."""
        try:
            # Try to use mozjpeg optimization
            try:
                import mozjpeg_lossless_optimization
                # Save with high quality first
                img.save(output_path, 'JPEG', quality=95, optimize=True)
                # Apply mozjpeg optimization
                mozjpeg_lossless_optimization.optimize(output_path)
                logger.debug(f"Applied mozjpeg optimization to {output_path}")
            except ImportError:
                # Fall back to standard PIL optimization
                img.save(output_path, 'JPEG', quality=85, optimize=True)
                logger.debug(f"Used standard JPEG optimization for {output_path}")
                
        except Exception as e:
            logger.error(f"Error saving optimized JPEG: {e}")
            # Final fallback
            img.save(output_path, 'JPEG', quality=80)
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem compatibility."""
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = re.sub(r'\s+', '_', filename)
        filename = filename.strip('._')

        # Remove common words and clean up
        filename = re.sub(r'\b(image|img|figure|fig|photo|picture|pic)\b', '', filename, flags=re.IGNORECASE)
        filename = re.sub(r'_+', '_', filename)  # Replace multiple underscores with single
        filename = filename.strip('_')

        # Limit length but keep meaningful content
        if len(filename) > 80:
            # Try to keep the first part which is usually more descriptive
            filename = filename[:80]
            # Cut at word boundary if possible
            last_underscore = filename.rfind('_')
            if last_underscore > 40:  # Only if we have a reasonable amount of text
                filename = filename[:last_underscore]

        # Ensure we have something meaningful
        if not filename or len(filename) < 3:
            return "image"

        return filename

    def _get_unique_filename(self, filename: str) -> str:
        """
        Get a unique filename by adding a counter if the filename already exists.

        Args:
            filename (str): Desired filename

        Returns:
            str: Unique filename
        """
        if filename not in self.used_filenames:
            self.used_filenames.add(filename)
            return filename

        # If filename exists, add a counter
        name, ext = os.path.splitext(filename)
        counter = 1
        while True:
            new_filename = f"{name}_{counter:02d}{ext}"
            if new_filename not in self.used_filenames:
                self.used_filenames.add(new_filename)
                return new_filename
            counter += 1
