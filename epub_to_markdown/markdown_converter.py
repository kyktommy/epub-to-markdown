"""
Markdown Converter Module

This module provides functionality to convert parsed EPUB content to properly
formatted markdown files.
"""

import os
import re
from typing import List, Optional
from .epub_parser import EPUBMetadata, EPUBChapter
from .image_extractor import EPUBImage
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarkdownConverter:
    """
    Converts parsed EPUB content to markdown format.
    """
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize the markdown converter.
        
        Args:
            output_dir (str): Directory to save markdown files
        """
        self.output_dir = output_dir
        self._ensure_output_dir()
    
    def _ensure_output_dir(self):
        """Ensure the output directory exists."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logger.info(f"Created output directory: {self.output_dir}")
    
    def convert(self, metadata: EPUBMetadata, chapters: List[EPUBChapter],
                single_file: bool = True) -> List[str]:
        """
        Convert EPUB content to markdown format.
        
        Args:
            metadata (EPUBMetadata): Book metadata
            chapters (List[EPUBChapter]): List of chapters
            single_file (bool): Whether to create a single markdown file or multiple files
            
        Returns:
            List[str]: List of created file paths
        """
        if single_file:
            return self._convert_to_single_file(metadata, chapters)
        else:
            return self._convert_to_multiple_files(metadata, chapters)
    
    def _convert_to_single_file(self, metadata: EPUBMetadata, chapters: List[EPUBChapter]) -> List[str]:
        """
        Convert all content to a single markdown file.
        
        Args:
            metadata (EPUBMetadata): Book metadata
            chapters (List[EPUBChapter]): List of chapters
            
        Returns:
            List[str]: List containing the single file path
        """
        # Create filename from book title
        filename = self._sanitize_filename(f"{metadata.title}.md")
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # Write metadata header
                f.write(self._create_metadata_header(metadata))
                f.write("\n\n---\n\n")
                
                # Write table of contents
                f.write("# Table of Contents\n\n")
                for i, chapter in enumerate(chapters, 1):
                    f.write(f"{i}. [{chapter.title}](#{self._create_anchor(chapter.title)})\n")
                f.write("\n---\n\n")
                
                # Write chapters
                for chapter in chapters:
                    f.write(self._format_chapter(chapter))
                    f.write("\n\n---\n\n")
            
            logger.info(f"Created single markdown file: {filepath}")
            return [filepath]
            
        except Exception as e:
            logger.error(f"Error creating single markdown file: {e}")
            return []
    
    def _convert_to_multiple_files(self, metadata: EPUBMetadata, chapters: List[EPUBChapter]) -> List[str]:
        """
        Convert content to multiple markdown files (one per chapter).
        
        Args:
            metadata (EPUBMetadata): Book metadata
            chapters (List[EPUBChapter]): List of chapters
            
        Returns:
            List[str]: List of created file paths
        """
        created_files = []
        
        # Create main index file
        index_filename = self._sanitize_filename(f"{metadata.title}_index.md")
        index_filepath = os.path.join(self.output_dir, index_filename)
        
        try:
            with open(index_filepath, 'w', encoding='utf-8') as f:
                # Write metadata header
                f.write(self._create_metadata_header(metadata))
                f.write("\n\n")
                
                # Write table of contents with links to chapter files
                f.write("# Table of Contents\n\n")
                for i, chapter in enumerate(chapters, 1):
                    chapter_filename = self._sanitize_filename(f"chapter_{i:02d}_{chapter.title}.md")
                    f.write(f"{i}. [{chapter.title}]({chapter_filename})\n")
                f.write("\n")
            
            created_files.append(index_filepath)
            logger.info(f"Created index file: {index_filepath}")
            
            # Create individual chapter files
            for i, chapter in enumerate(chapters, 1):
                chapter_filename = self._sanitize_filename(f"chapter_{i:02d}_{chapter.title}.md")
                chapter_filepath = os.path.join(self.output_dir, chapter_filename)
                
                try:
                    with open(chapter_filepath, 'w', encoding='utf-8') as f:
                        f.write(self._format_chapter(chapter, include_navigation=True, 
                                                   prev_chapter=chapters[i-2] if i > 1 else None,
                                                   next_chapter=chapters[i] if i < len(chapters) else None,
                                                   chapter_num=i))
                    
                    created_files.append(chapter_filepath)
                    logger.info(f"Created chapter file: {chapter_filepath}")
                    
                except Exception as e:
                    logger.error(f"Error creating chapter file {chapter_filename}: {e}")
            
            return created_files
            
        except Exception as e:
            logger.error(f"Error creating multiple markdown files: {e}")
            return []
    
    def _create_metadata_header(self, metadata: EPUBMetadata) -> str:
        """
        Create a metadata header for the markdown file.
        
        Args:
            metadata (EPUBMetadata): Book metadata
            
        Returns:
            str: Formatted metadata header
        """
        header = f"# {metadata.title}\n\n"
        header += f"**Author:** {metadata.author}\n\n"
        
        if metadata.publisher:
            header += f"**Publisher:** {metadata.publisher}\n\n"
        
        if metadata.description:
            header += f"**Description:** {metadata.description}\n\n"
        
        header += f"**Language:** {metadata.language}\n\n"
        
        if metadata.identifier:
            header += f"**Identifier:** {metadata.identifier}\n\n"
        
        if metadata.rights:
            header += f"**Rights:** {metadata.rights}\n\n"
        
        return header
    
    def _format_chapter(self, chapter: EPUBChapter, include_navigation: bool = False,
                       prev_chapter: Optional[EPUBChapter] = None,
                       next_chapter: Optional[EPUBChapter] = None,
                       chapter_num: Optional[int] = None) -> str:
        """
        Format a chapter as markdown.
        
        Args:
            chapter (EPUBChapter): Chapter to format
            include_navigation (bool): Whether to include navigation links
            prev_chapter (Optional[EPUBChapter]): Previous chapter for navigation
            next_chapter (Optional[EPUBChapter]): Next chapter for navigation
            chapter_num (Optional[int]): Chapter number for navigation
            
        Returns:
            str: Formatted chapter content
        """
        content = f"# {chapter.title}\n\n"
        
        # Add navigation if requested
        if include_navigation and chapter_num:
            nav = "["
            if prev_chapter:
                prev_filename = self._sanitize_filename(f"chapter_{chapter_num-1:02d}_{prev_chapter.title}.md")
                nav += f"← Previous: {prev_chapter.title}]({prev_filename})"
            else:
                nav += "← Previous"
            
            nav += " | "
            nav += "[📚 Index](index.md)"
            nav += " | "
            
            if next_chapter:
                next_filename = self._sanitize_filename(f"chapter_{chapter_num+1:02d}_{next_chapter.title}.md")
                nav += f"[Next: {next_chapter.title} →]({next_filename})"
            else:
                nav += "Next →"
            
            nav += "]\n\n---\n\n"
            content += nav
        
        # Format chapter content
        formatted_content = self._format_text_content(chapter.content)
        content += formatted_content

        # Add images if present
        if chapter.images:
            content += self._format_chapter_images(chapter.images)
        
        # Add navigation at the end too
        if include_navigation and chapter_num:
            content += f"\n\n---\n\n{nav}"
        
        return content
    
    def _format_text_content(self, text: str) -> str:
        """
        Format text content for markdown.
        
        Args:
            text (str): Raw text content
            
        Returns:
            str: Formatted markdown content
        """
        # Split into paragraphs
        paragraphs = text.split('\n\n')
        formatted_paragraphs = []
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if paragraph:
                # Basic formatting improvements
                paragraph = self._improve_paragraph_formatting(paragraph)
                formatted_paragraphs.append(paragraph)
        
        return '\n\n'.join(formatted_paragraphs)
    
    def _improve_paragraph_formatting(self, paragraph: str) -> str:
        """
        Improve paragraph formatting for better markdown readability.
        
        Args:
            paragraph (str): Raw paragraph text
            
        Returns:
            str: Improved paragraph text
        """
        # Remove excessive whitespace
        paragraph = re.sub(r'\s+', ' ', paragraph).strip()
        
        # Handle common formatting patterns
        # (Add more sophisticated formatting rules as needed)
        
        return paragraph
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for filesystem compatibility.
        
        Args:
            filename (str): Original filename
            
        Returns:
            str: Sanitized filename
        """
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = re.sub(r'\s+', '_', filename)
        filename = filename.strip('._')
        
        # Limit length
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:200-len(ext)] + ext
        
        return filename

    def _format_chapter_images(self, images: List[EPUBImage]) -> str:
        """
        Format images for inclusion in markdown.

        Args:
            images (List[EPUBImage]): List of images in the chapter

        Returns:
            str: Formatted markdown content for images
        """
        if not images:
            return ""

        content = "\n\n## Images\n\n"

        for image in images:
            # Create relative path to image
            image_path = os.path.join("images", image.filename)

            # Format image markdown
            alt_text = image.alt_text or image.caption or f"Image {image.page_number}"
            content += f"![{alt_text}]({image_path})\n\n"

            # Add image details
            if image.caption:
                content += f"**Caption:** {image.caption}\n\n"

            content += f"**Page:** {image.page_number}"
            if image.chapter_title:
                content += f" | **Chapter:** {image.chapter_title}"

            content += f" | **Size:** {image.width}x{image.height}"
            content += f" | **File Size:** {self._format_file_size(image.file_size)}\n\n"

            content += "---\n\n"

        return content

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    
    def _create_anchor(self, text: str) -> str:
        """
        Create a markdown anchor from text.
        
        Args:
            text (str): Text to convert to anchor
            
        Returns:
            str: Markdown anchor
        """
        anchor = text.lower()
        anchor = re.sub(r'[^\w\s-]', '', anchor)
        anchor = re.sub(r'[-\s]+', '-', anchor)
        return anchor.strip('-')
