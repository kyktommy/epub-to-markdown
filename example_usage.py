#!/usr/bin/env python3
"""
Example usage of the EPUB to Markdown Converter

This script demonstrates how to use the library programmatically.
"""

import os
import sys
from epub_to_markdown import EPUBParser, MarkdownConverter

def main():
    """Main example function."""
    
    # Check if an EPUB file was provided
    if len(sys.argv) < 2:
        print("Usage: python example_usage.py <epub_file>")
        print("\nExample:")
        print("  python example_usage.py sample_book.epub")
        sys.exit(1)
    
    epub_file = sys.argv[1]
    
    # Check if file exists
    if not os.path.exists(epub_file):
        print(f"Error: File '{epub_file}' not found")
        sys.exit(1)
    
    # Check if it's an EPUB file
    if not epub_file.lower().endswith('.epub'):
        print(f"Error: '{epub_file}' does not appear to be an EPUB file")
        sys.exit(1)
    
    try:
        print(f"📚 Processing EPUB file: {epub_file}")
        print("=" * 50)
        
        # Step 1: Parse the EPUB file
        print("🔍 Parsing EPUB file...")
        parser = EPUBParser(epub_file)
        metadata, chapters = parser.parse()
        
        # Step 2: Display book information
        print("\n📖 Book Information:")
        print(f"  Title: {metadata.title}")
        print(f"  Author: {metadata.author}")
        print(f"  Language: {metadata.language}")
        if metadata.publisher:
            print(f"  Publisher: {metadata.publisher}")
        if metadata.description:
            description = metadata.description[:100] + "..." if len(metadata.description) > 100 else metadata.description
            print(f"  Description: {description}")
        
        print(f"\n📑 Found {len(chapters)} chapters:")
        for i, chapter in enumerate(chapters[:5], 1):  # Show first 5 chapters
            word_count = len(chapter.content.split())
            print(f"  {i}. {chapter.title} (~{word_count} words)")
        
        if len(chapters) > 5:
            print(f"  ... and {len(chapters) - 5} more chapters")
        
        # Step 3: Convert to markdown
        print(f"\n🔄 Converting to markdown...")
        
        # Create output directory
        output_dir = "example_output"
        converter = MarkdownConverter(output_dir)
        
        # Convert (single file is now the default, set to False for multiple files)
        single_file = True  # This is now the default
        created_files = converter.convert(metadata, chapters, single_file)
        
        # Step 4: Display results
        if created_files:
            print(f"\n✅ Successfully created {len(created_files)} file(s):")
            total_size = 0
            for file_path in created_files:
                file_size = os.path.getsize(file_path)
                total_size += file_size
                print(f"  📄 {os.path.basename(file_path)} ({file_size:,} bytes)")
            
            print(f"\n📊 Total output size: {total_size:,} bytes")
            print(f"📁 Files saved to: {os.path.abspath(output_dir)}")
            
            # Optional: Show first few lines of the index file if it exists
            index_file = None
            for file_path in created_files:
                if "index" in os.path.basename(file_path).lower():
                    index_file = file_path
                    break
            
            if index_file:
                print(f"\n📋 Preview of {os.path.basename(index_file)}:")
                print("-" * 40)
                try:
                    with open(index_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()[:10]  # First 10 lines
                        for line in lines:
                            print(f"  {line.rstrip()}")
                        if len(lines) == 10:
                            print("  ...")
                except Exception as e:
                    print(f"  Error reading file: {e}")
        else:
            print("❌ No files were created")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
