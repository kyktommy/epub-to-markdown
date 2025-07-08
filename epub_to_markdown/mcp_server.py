"""
MCP Server for EPUB to Markdown Converter

This module provides a Model Context Protocol (MCP) server that exposes
the EPUB to markdown conversion functionality as tools for AI assistants.
"""

import logging
import os
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP

from .epub_parser import EPUBParser
from .markdown_converter import MarkdownConverter

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("epub-to-markdown")


@mcp.tool()
def convert_epub_to_markdown(epub_path: str, output_dir: Optional[str] = None) -> str:
    """
    Convert an EPUB file to markdown format.

    Args:
        epub_path: Path to the EPUB file to convert
        output_dir: Output directory for the markdown file (optional, defaults to same directory as input)

    Returns:
        str: Conversion result with markdown content
    """
    # Validate EPUB file exists
    if not os.path.exists(epub_path):
        raise ValueError(f"EPUB file not found: {epub_path}")

    # Validate EPUB file extension
    if not epub_path.lower().endswith('.epub'):
        raise ValueError("File must be an EPUB file (.epub extension)")

    # Set default output directory to same directory as input file
    if not output_dir:
        output_dir = os.path.dirname(os.path.abspath(epub_path))

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    try:
        # Parse EPUB file (single file mode, no image extraction)
        parser = EPUBParser(epub_path, extract_images=False, output_dir=output_dir, single_file_mode=True)
        metadata, chapters = parser.parse()

        if not chapters:
            raise ValueError("No chapters found in EPUB file")

        # Convert to markdown (single file mode)
        converter = MarkdownConverter(output_dir)
        created_files = converter.convert(metadata, chapters, single_file=True)

        if not created_files:
            raise ValueError("Conversion failed - no files created")

        # Read the created markdown file content
        markdown_file = created_files[0]

        # Prepare result
        result_text = f"Successfully converted EPUB to markdown: "
        result_text += f"📚 Title: {metadata.title}, "
        result_text += f"📁 Output: {markdown_file}"

        return result_text

    except Exception as e:
        logger.error(f"Error converting EPUB: {e}")
        raise ValueError(f"Error converting EPUB: {str(e)}")


def main():
    """
    Main function to run the MCP server.
    """
    mcp.run()


if __name__ == "__main__":
    main()
