#!/usr/bin/env python3
"""
EPUB Chapter Lister Script

A simple script that takes an EPUB filename as input and lists all chapters
found in the EPUB file with their titles, file names, and word counts.

Usage:
    python list_chapters.py <epub_file>
    python list_chapters.py book.epub

Features:
- Lists all chapters with titles
- Shows source file names
- Displays approximate word counts
- Shows book metadata (title, author, etc.)
- Clean, readable output format
"""

import sys
import os
from typing import List
from epub_to_markdown.epub_parser import EPUBParser, EPUBChapter, EPUBMetadata


def print_book_info(metadata: EPUBMetadata) -> None:
    """Print book metadata information."""
    print("📖 BOOK INFORMATION")
    print("=" * 60)
    print(f"Title: {metadata.title}")
    print(f"Author: {metadata.author}")
    print(f"Language: {metadata.language}")
    
    if metadata.publisher:
        print(f"Publisher: {metadata.publisher}")
    
    if metadata.identifier:
        print(f"Identifier: {metadata.identifier}")
    
    if metadata.description:
        # Truncate long descriptions
        desc = metadata.description
        if len(desc) > 200:
            desc = desc[:200] + "..."
        print(f"Description: {desc}")
    
    if metadata.rights:
        print(f"Rights: {metadata.rights}")
    
    print()


def print_chapters_list(chapters: List[EPUBChapter]) -> None:
    """Print the list of chapters with details."""
    print("📑 CHAPTERS")
    print("=" * 60)
    print(f"Total chapters found: {len(chapters)}")
    print()
    
    if not chapters:
        print("❌ No chapters found in this EPUB file.")
        return
    
    # Calculate column widths for better formatting
    max_title_len = max(len(chapter.title) for chapter in chapters)
    max_file_len = max(len(chapter.file_name) for chapter in chapters)
    
    # Ensure minimum widths
    title_width = max(max_title_len, 20)
    file_width = max(max_file_len, 15)
    
    # Print header
    print(f"{'#':<3} {'Title':<{title_width}} {'File':<{file_width}} {'Words':<8}")
    print("-" * (3 + title_width + file_width + 8 + 3))  # +3 for spacing
    
    # Print each chapter
    for i, chapter in enumerate(chapters, 1):
        word_count = len(chapter.content.split()) if chapter.content else 0
        
        # Truncate title if too long for display
        display_title = chapter.title
        if len(display_title) > title_width:
            display_title = display_title[:title_width-3] + "..."
        
        # Truncate filename if too long for display
        display_file = chapter.file_name
        if len(display_file) > file_width:
            display_file = "..." + display_file[-(file_width-3):]
        
        print(f"{i:<3} {display_title:<{title_width}} {display_file:<{file_width}} {word_count:<8}")


def print_summary(chapters: List[EPUBChapter]) -> None:
    """Print summary statistics."""
    if not chapters:
        return
    
    total_words = sum(len(chapter.content.split()) if chapter.content else 0 for chapter in chapters)
    avg_words = total_words // len(chapters) if chapters else 0
    
    print()
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"Total chapters: {len(chapters)}")
    print(f"Total words (approx): {total_words:,}")
    print(f"Average words per chapter: {avg_words:,}")


def main():
    """Main function to handle command line arguments and process EPUB file."""
    # Check command line arguments
    if len(sys.argv) != 2:
        print("Usage: python list_chapters.py <epub_file>")
        print()
        print("Examples:")
        print("  python list_chapters.py book.epub")
        print("  python list_chapters.py /path/to/my/book.epub")
        sys.exit(1)
    
    epub_file = sys.argv[1]
    
    # Validate input file
    if not os.path.exists(epub_file):
        print(f"❌ Error: File '{epub_file}' not found")
        sys.exit(1)
    
    if not os.path.isfile(epub_file):
        print(f"❌ Error: '{epub_file}' is not a file")
        sys.exit(1)
    
    if not epub_file.lower().endswith('.epub'):
        print(f"❌ Warning: '{epub_file}' does not appear to be an EPUB file")
        print("Continuing anyway...")
        print()
    
    try:
        print(f"📚 Analyzing EPUB file: {epub_file}")
        print()
        
        # Initialize parser (no image extraction needed for listing)
        parser = EPUBParser(epub_file, extract_images=False, single_file_mode=True)
        
        # Parse the EPUB file
        print("🔍 Parsing EPUB file...")
        metadata, chapters = parser.parse()
        print()
        
        # Display book information
        print_book_info(metadata)
        
        # Display chapters list
        print_chapters_list(chapters)
        
        # Display summary
        print_summary(chapters)
        
        print()
        print("✅ Analysis completed successfully!")
        
    except FileNotFoundError:
        print(f"❌ Error: File '{epub_file}' not found")
        sys.exit(1)
    except PermissionError:
        print(f"❌ Error: Permission denied accessing '{epub_file}'")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error analyzing EPUB file: {str(e)}")
        print()
        print("This might happen if:")
        print("- The file is corrupted or not a valid EPUB")
        print("- The file is password protected")
        print("- There are missing dependencies")
        sys.exit(1)


if __name__ == "__main__":
    main()
