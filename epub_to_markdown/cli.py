"""
Command Line Interface for EPUB to Markdown Converter

This module provides a command-line interface for converting EPUB files to markdown format.
"""

import os
import sys
import click
from typing import Optional
from .epub_parser import EPUBParser
from .markdown_converter import MarkdownConverter
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(version='0.1.0', prog_name='epub-to-markdown')
def cli(ctx):
    """EPUB to Markdown Converter CLI

    Convert EPUB files to markdown format using multiple interfaces:
    - Command line conversion
    - Web interface (Streamlit)
    - REST API (FastAPI)
    """
    if ctx.invoked_subcommand is None:
        click.echo("📚 EPUB to Markdown Converter")
        click.echo("=" * 40)
        click.echo("Available commands:")
        click.echo("  convert    Convert EPUB file to markdown")
        click.echo("  info       Show EPUB file information")
        click.echo("  batch      Convert multiple EPUB files")
        click.echo("  web        Launch Streamlit web interface")
        click.echo("  api        Launch FastAPI REST API server")
        click.echo("  mcp        Launch MCP (Model Context Protocol) server")
        click.echo()
        click.echo("Use 'epub-to-markdown COMMAND --help' for more information")
        click.echo()
        click.echo("Quick start:")
        click.echo("  epub-to-markdown convert book.epub")
        click.echo("  epub-to-markdown web")


@cli.command()
@click.argument('epub_file', type=click.Path(exists=True, readable=True))
@click.option('--output-dir', '-o', default=None,
              help='Output directory for markdown files (default: same directory as input file)')
@click.option('--multiple-files', '-m', is_flag=True,
              help='Create multiple markdown files instead of a single file (one per chapter)')
@click.option('--extract-images/--no-extract-images', '-i', default=True,
              help='Extract and process images from EPUB (only available in multiple files mode)')
@click.option('--verbose', '-v', is_flag=True,
              help='Enable verbose logging')
def convert(epub_file: str, output_dir: str, multiple_files: bool, extract_images: bool, verbose: bool):
    """
    Convert EPUB files to markdown format.
    
    EPUB_FILE: Path to the EPUB file to convert
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Validate input file
        if not epub_file.lower().endswith('.epub'):
            click.echo(f"Error: {epub_file} does not appear to be an EPUB file", err=True)
            sys.exit(1)

        # Set default output directory to input file's directory if not specified
        if output_dir is None:
            output_dir = os.path.dirname(os.path.abspath(epub_file))
            if not output_dir:  # Handle case where file is in current directory
                output_dir = '.'

        click.echo(f"📚 Converting EPUB file: {epub_file}")
        click.echo(f"📁 Output directory: {output_dir}")
        click.echo(f"📄 Output mode: {'Multiple files' if multiple_files else 'Single file'}")

        # Check if user wants images in single file mode
        if extract_images and not multiple_files:
            click.echo(f"⚠️  Image extraction is only available in multiple files mode")
            click.echo(f"🖼️  Extract images: No (disabled for single file mode)")
        else:
            click.echo(f"🖼️  Extract images: {'Yes' if extract_images and multiple_files else 'No'}")
        click.echo()
        
        # Initialize parser and converter
        single_file_mode = not multiple_files
        parser = EPUBParser(epub_file, extract_images=extract_images, output_dir=output_dir, single_file_mode=single_file_mode)
        converter = MarkdownConverter(output_dir)
        
        # Parse EPUB file
        click.echo("🔍 Parsing EPUB file...")
        metadata, chapters = parser.parse()
        
        if not chapters:
            click.echo("❌ No chapters found in the EPUB file", err=True)
            sys.exit(1)
        
        # Display book information
        click.echo(f"📖 Title: {metadata.title}")
        click.echo(f"✍️  Author: {metadata.author}")
        click.echo(f"🌐 Language: {metadata.language}")
        if metadata.publisher:
            click.echo(f"🏢 Publisher: {metadata.publisher}")
        click.echo(f"📑 Chapters found: {len(chapters)}")
        click.echo()
        
        # Convert to markdown
        click.echo("🔄 Converting to markdown...")
        created_files = converter.convert(metadata, chapters, not multiple_files)
        
        if created_files:
            click.echo("✅ Conversion completed successfully!")

            # Count images if available
            total_images = sum(len(chapter.images) for chapter in chapters)

            if total_images > 0:
                click.echo(f"📁 Created {len(created_files)} file(s) and extracted {total_images} image(s):")
            else:
                click.echo(f"📁 Created {len(created_files)} file(s):")

            for file_path in created_files:
                click.echo(f"   • {file_path}")

            if total_images > 0:
                click.echo(f"   • images/ directory with {total_images} processed image(s)")
        else:
            click.echo("❌ Conversion failed", err=True)
            sys.exit(1)
            
    except FileNotFoundError:
        click.echo(f"❌ Error: File '{epub_file}' not found", err=True)
        sys.exit(1)
    except PermissionError:
        click.echo(f"❌ Error: Permission denied accessing '{epub_file}'", err=True)
        sys.exit(1)
    except Exception as e:
        if verbose:
            logger.exception("Detailed error information:")
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


# Add a standalone main function for backward compatibility
@click.command()
@click.argument('epub_file', type=click.Path(exists=True, readable=True))
@click.option('--output-dir', '-o', default=None,
              help='Output directory for markdown files (default: same directory as input file)')
@click.option('--multiple-files', '-m', is_flag=True,
              help='Create multiple markdown files instead of a single file (one per chapter)')
@click.option('--extract-images/--no-extract-images', '-i', default=True,
              help='Extract and process images from EPUB (only available in multiple files mode)')
@click.option('--verbose', '-v', is_flag=True,
              help='Enable verbose logging')
@click.version_option(version='0.1.0', prog_name='epub-to-markdown')
def main(epub_file: str, output_dir: str, multiple_files: bool, extract_images: bool, verbose: bool):
    """
    Convert EPUB files to markdown format.

    EPUB_FILE: Path to the EPUB file to convert

    This is the standalone main function for backward compatibility.
    """
    # Implement the same logic as convert command
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Validate input file
        if not epub_file.lower().endswith('.epub'):
            click.echo(f"Error: {epub_file} does not appear to be an EPUB file", err=True)
            sys.exit(1)

        # Set default output directory to input file's directory if not specified
        if output_dir is None:
            output_dir = os.path.dirname(os.path.abspath(epub_file))
            if not output_dir:  # Handle case where file is in current directory
                output_dir = '.'

        click.echo(f"📚 Converting EPUB file: {epub_file}")
        click.echo(f"📁 Output directory: {output_dir}")
        click.echo(f"📄 Output mode: {'Multiple files' if multiple_files else 'Single file'}")

        # Check if user wants images in single file mode
        if extract_images and not multiple_files:
            click.echo(f"⚠️  Image extraction is only available in multiple files mode")
            click.echo(f"🖼️  Extract images: No (disabled for single file mode)")
        else:
            click.echo(f"🖼️  Extract images: {'Yes' if extract_images and multiple_files else 'No'}")
        click.echo()

        # Initialize parser and converter
        single_file_mode = not multiple_files
        parser = EPUBParser(epub_file, extract_images=extract_images, output_dir=output_dir, single_file_mode=single_file_mode)
        converter = MarkdownConverter(output_dir)

        # Parse EPUB file
        click.echo("🔍 Parsing EPUB file...")
        metadata, chapters = parser.parse()

        if not chapters:
            click.echo("❌ No chapters found in the EPUB file", err=True)
            sys.exit(1)

        # Display book information
        click.echo(f"📖 Title: {metadata.title}")
        click.echo(f"✍️  Author: {metadata.author}")
        click.echo(f"🌐 Language: {metadata.language}")
        if metadata.publisher:
            click.echo(f"🏢 Publisher: {metadata.publisher}")
        click.echo(f"📑 Chapters found: {len(chapters)}")
        click.echo()

        # Convert to markdown
        click.echo("🔄 Converting to markdown...")
        created_files = converter.convert(metadata, chapters, not multiple_files)

        if created_files:
            click.echo("✅ Conversion completed successfully!")

            # Count images if available
            total_images = sum(len(chapter.images) for chapter in chapters)

            if total_images > 0:
                click.echo(f"📁 Created {len(created_files)} file(s) and extracted {total_images} image(s):")
            else:
                click.echo(f"📁 Created {len(created_files)} file(s):")

            for file_path in created_files:
                click.echo(f"   • {file_path}")

            if total_images > 0:
                click.echo(f"   • images/ directory with {total_images} processed image(s)")
        else:
            click.echo("❌ Conversion failed", err=True)
            sys.exit(1)

    except FileNotFoundError:
        click.echo(f"❌ Error: File '{epub_file}' not found", err=True)
        sys.exit(1)
    except PermissionError:
        click.echo(f"❌ Error: Permission denied accessing '{epub_file}'", err=True)
        sys.exit(1)
    except Exception as e:
        if verbose:
            logger.exception("Detailed error information:")
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('epub_file', type=click.Path(exists=True, readable=True))
def info(epub_file: str):
    """
    Display information about an EPUB file without converting it.
    
    EPUB_FILE: Path to the EPUB file to analyze
    """
    try:
        if not epub_file.lower().endswith('.epub'):
            click.echo(f"Error: {epub_file} does not appear to be an EPUB file", err=True)
            sys.exit(1)
        
        click.echo(f"📚 Analyzing EPUB file: {epub_file}")
        click.echo()
        
        # Initialize parser
        parser = EPUBParser(epub_file)
        
        # Parse EPUB file
        metadata, chapters = parser.parse()
        
        # Display detailed information
        click.echo("📖 BOOK INFORMATION")
        click.echo("=" * 50)
        click.echo(f"Title: {metadata.title}")
        click.echo(f"Author: {metadata.author}")
        click.echo(f"Language: {metadata.language}")
        click.echo(f"Identifier: {metadata.identifier}")
        
        if metadata.publisher:
            click.echo(f"Publisher: {metadata.publisher}")
        
        if metadata.description:
            click.echo(f"Description: {metadata.description[:200]}{'...' if len(metadata.description) > 200 else ''}")
        
        if metadata.rights:
            click.echo(f"Rights: {metadata.rights}")
        
        click.echo()
        click.echo("📑 CHAPTERS")
        click.echo("=" * 50)
        click.echo(f"Total chapters: {len(chapters)}")
        click.echo()
        
        for i, chapter in enumerate(chapters, 1):
            word_count = len(chapter.content.split())
            click.echo(f"{i:2d}. {chapter.title}")
            click.echo(f"    File: {chapter.file_name}")
            click.echo(f"    Words: ~{word_count}")
            click.echo()
            
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--output-dir', '-o', default='batch_output',
              help='Output directory for all converted files (default: batch_output)')
@click.option('--multiple-files', '-m', is_flag=True,
              help='Create multiple markdown files for each EPUB (one per chapter)')
@click.option('--extract-images/--no-extract-images', '-i', default=True,
              help='Extract and process images from EPUB files (only available in multiple files mode)')
def batch(directory: str, output_dir: str, multiple_files: bool, extract_images: bool):
    """
    Convert all EPUB files in a directory to markdown format.

    DIRECTORY: Directory containing EPUB files to convert
    """
    try:
        # Find all EPUB files in the directory
        epub_files = []
        for file in os.listdir(directory):
            if file.lower().endswith('.epub'):
                epub_files.append(os.path.join(directory, file))

        if not epub_files:
            click.echo(f"❌ No EPUB files found in directory: {directory}", err=True)
            sys.exit(1)

        click.echo(f"📚 Found {len(epub_files)} EPUB file(s) to convert")
        click.echo(f"📁 Output directory: {output_dir}")
        click.echo()

        successful_conversions = 0
        failed_conversions = 0

        for epub_file in epub_files:
            try:
                click.echo(f"🔄 Converting: {os.path.basename(epub_file)}")

                # Create subdirectory for each book
                book_name = os.path.splitext(os.path.basename(epub_file))[0]
                book_output_dir = os.path.join(output_dir, book_name)

                # Initialize parser and converter
                single_file_mode = not multiple_files
                parser = EPUBParser(epub_file, extract_images=extract_images, output_dir=book_output_dir, single_file_mode=single_file_mode)
                converter = MarkdownConverter(book_output_dir)

                # Parse and convert
                metadata, chapters = parser.parse()
                created_files = converter.convert(metadata, chapters, not multiple_files)

                if created_files:
                    click.echo(f"   ✅ Success: Created {len(created_files)} file(s)")
                    successful_conversions += 1
                else:
                    click.echo(f"   ❌ Failed: No files created")
                    failed_conversions += 1

            except Exception as e:
                click.echo(f"   ❌ Failed: {str(e)}")
                failed_conversions += 1

        click.echo()
        click.echo(f"📊 Batch conversion completed:")
        click.echo(f"   ✅ Successful: {successful_conversions}")
        click.echo(f"   ❌ Failed: {failed_conversions}")

    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--port', '-p', default=8501, help='Port to run Streamlit on (default: 8501)')
@click.option('--host', '-h', default='0.0.0.0', help='Host to run Streamlit on (default: 0.0.0.0)')
def web(port: int, host: str):
    """
    Launch the Streamlit web interface.
    """
    try:
        import streamlit.web.cli as stcli

        click.echo("🚀 Starting EPUB to Markdown Converter Web Interface...")
        click.echo(f"🌐 Web interface will be available at: http://localhost:{port}")
        click.echo("\nPress Ctrl+C to stop the server")

        # Set up Streamlit arguments
        sys.argv = [
            "streamlit",
            "run",
            os.path.join(os.path.dirname(__file__), "streamlit_app.py"),
            f"--server.port={port}",
            f"--server.address={host}"
        ]

        # Run Streamlit
        stcli.main()

    except ImportError:
        click.echo("❌ Error: Streamlit is not installed", err=True)
        click.echo("Install it with: pip install streamlit", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error starting web interface: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--port', '-p', default=8000, help='Port to run API on (default: 8000)')
@click.option('--host', '-h', default='0.0.0.0', help='Host to run API on (default: 0.0.0.0)')
@click.option('--reload', is_flag=True, help='Enable auto-reload for development')
def api(port: int, host: str, reload: bool):
    """
    Launch the FastAPI REST API server.
    """
    try:
        import uvicorn

        # Create downloads directory if it doesn't exist
        os.makedirs("downloads", exist_ok=True)

        click.echo("🚀 Starting EPUB to Markdown Converter API...")
        click.echo(f"📡 API will be available at: http://localhost:{port}")
        click.echo(f"📖 API documentation at: http://localhost:{port}/docs")
        click.echo(f"🔧 Alternative docs at: http://localhost:{port}/redoc")
        click.echo("\nPress Ctrl+C to stop the server")

        # Run FastAPI with uvicorn
        uvicorn.run(
            "epub_to_markdown.api:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )

    except ImportError:
        click.echo("❌ Error: FastAPI/Uvicorn is not installed", err=True)
        click.echo("Install them with: pip install fastapi uvicorn[standard]", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error starting API server: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
def mcp():
    """
    Launch the MCP (Model Context Protocol) server.

    This starts an MCP server that exposes EPUB to markdown conversion
    tools for AI assistants and other applications.
    """
    try:
        from .mcp_server import main as mcp_main

        click.echo("🚀 Starting EPUB to Markdown MCP Server...")
        click.echo("📡 MCP server is running and ready to accept connections")
        click.echo("🔧 Available tool:")
        click.echo("   - convert_epub_to_markdown: Convert EPUB to single markdown file")
        click.echo("\nPress Ctrl+C to stop the server")

        # Run the MCP server
        mcp_main()

    except ImportError:
        click.echo("❌ Error: FastMCP library is not installed", err=True)
        click.echo("Install it with: pip install fastmcp", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n👋 MCP server stopped")
    except Exception as e:
        click.echo(f"❌ Error starting MCP server: {str(e)}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()
