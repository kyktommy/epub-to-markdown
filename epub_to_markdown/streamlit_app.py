"""
Streamlit Web Interface for EPUB to Markdown Converter

This module provides a user-friendly web interface for converting EPUB files to markdown format.
"""

import os
import tempfile
import shutil
import zipfile
import time
from io import BytesIO
import streamlit as st
from pathlib import Path
import logging

try:
    from .epub_parser import EPUBParser
    from .markdown_converter import MarkdownConverter
except ImportError:
    # Handle case when running as standalone script
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from epub_to_markdown.epub_parser import EPUBParser
    from epub_to_markdown.markdown_converter import MarkdownConverter

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="EPUB to Markdown Converter",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stAppHeader {
        display: none;
    }
    [data-testid="stSidebarHeader"] {
        display: none;
    }
    .stMainBlockContainer {
        padding-top: 1rem;
    }
    .stSidebar {
        padding-top: 2rem;
    }
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #c3e6cb;
    }
    .error-box {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #f5c6cb;
    }
    .loading-text {
        color: #1f77b4;
        font-weight: 500;
        text-align: center;
        padding: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main Streamlit application."""
    
    # Header
    st.markdown('<h1 class="main-header">📚 EPUB to Markdown Converter</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center;">Convert your EPUB books to clean, formatted Markdown files</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Output format options
        output_format = st.radio(
            "Output Format",
            ["Single File (All chapters) - Default", "Multiple Files (One per chapter)"],
            help="Choose whether to combine everything into one file (default) or create separate files for each chapter"
        )

        single_file = output_format.startswith("Single File")

        # Image extraction option
        extract_images = st.checkbox(
            "🖼️ Extract images",
            value=False,
            help="Each image max 1920x1080 jpeg. Download as ZIP."
        )

        # Show download format info
        if extract_images:
            st.info("📦 **ZIP Download**: Image extraction enabled - output will be downloaded as ZIP archive.")
        elif single_file:
            st.info("📄 **Single File Download**: Output will be downloaded as individual markdown file.")
        else:
            st.info("📦 **ZIP Download**: Multiple files mode - output will be downloaded as ZIP archive.")
    
    uploaded_file = st.file_uploader(
        "Choose an EPUB file",
        type=['epub'],
        help="Upload your EPUB file to convert it to Markdown format"
    )
    
    if uploaded_file is not None:
        # Process the file immediately and convert to markdown
        process_epub_file(uploaded_file, single_file, extract_images)

def process_epub_file(uploaded_file, single_file, extract_images):
    """Process the uploaded EPUB file and automatically convert to markdown."""

    temp_file_path = None

    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.epub') as temp_file:
            temp_file.write(uploaded_file.read())
            temp_file_path = temp_file.name

        # Parse EPUB for metadata and chapters info
        with st.spinner("📖 Parsing EPUB file..."):
            parser = EPUBParser(temp_file_path, extract_images=False)  # Just for metadata/preview
            metadata, chapters = parser.parse()

        if not chapters:
            st.error("❌ No chapters found in the EPUB file")
            return

        # Automatically convert to markdown
        st.header("🔄 Converting to Markdown...")
        convert_and_download(temp_file_path, metadata, chapters, single_file, extract_images)

        # Display book information
        display_book_metadata(metadata)

        if st.button("🔍 Show Chapters"):
            display_chapters_info(chapters)

    except Exception as e:
        st.error(f"❌ Error processing EPUB file: {str(e)}")
        logger.error(f"Error processing EPUB: {e}")

    finally:
        # Clean up temporary file
        if temp_file_path:
            try:
                os.unlink(temp_file_path)
            except:
                pass

def display_book_metadata(metadata):
    """Display book metadata in a nice format."""
    
    st.header("📋 Book Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Title:** {metadata.title}")
        st.markdown(f"**Author:** {metadata.author}")
        st.markdown(f"**Language:** {metadata.language}")
    
    with col2:
        if metadata.publisher:
            st.markdown(f"**Publisher:** {metadata.publisher}")
        if metadata.identifier:
            st.markdown(f"**Identifier:** {metadata.identifier}")
    
    if metadata.description:
        st.markdown("**Description:**")
        st.markdown(f"_{metadata.description[:100]}{'...' if len(metadata.description) > 300 else ''}_")

def display_chapters_info(chapters):
    """Display chapters information."""

    st.header(f"📑 Chapters ({len(chapters)} found)")

    # Show loading spinner while processing chapter information
    progress_bar = st.progress(0)
    status_text = st.empty()

    # Create a dataframe for better display
    chapter_data = []
    total_words = 0

    for i, chapter in enumerate(chapters, 1):
        # Update progress
        progress = i / len(chapters)
        progress_bar.progress(progress)

        # Truncate long titles for display
        display_title = chapter.title[:40] + "..." if len(chapter.title) > 40 else chapter.title
        status_text.text(f"📊 Analyzing chapter {i}/{len(chapters)}: {display_title}")

        # Add small delay for better UX on very fast processing
        if len(chapters) > 20:
            time.sleep(0.01)  # Small delay only for very large books

        word_count = len(chapter.content.split())
        total_words += word_count
        chapter_data.append({
            "Chapter": i,
            "Title": chapter.title,
            "File": chapter.file_name
        })

    # Show completion message briefly
    status_text.text(f"✅ Processed {len(chapters)} chapters")
    time.sleep(0.5)  # Brief pause to show completion

    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()

    st.dataframe(chapter_data, use_container_width=True)

    # Show completion message
    st.success(f"📚 Successfully loaded {len(chapters)} chapters!")

def convert_and_download(epub_path, metadata, chapters, single_file, extract_images):
    """Convert EPUB to markdown and provide download."""

    try:
        # Create temporary output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = os.path.join(temp_dir, "output")

            # Re-parse EPUB with image extraction if enabled
            if extract_images:
                with st.spinner("🔄 Converting to Markdown and extracting images..."):
                    # Re-parse with image extraction enabled
                    # For single file mode with images, we need to extract images but not restrict by single_file_mode
                    parser = EPUBParser(epub_path, extract_images=True, output_dir=output_dir, single_file_mode=False)
                    metadata, chapters = parser.parse()

                    converter = MarkdownConverter(output_dir)
                    created_files = converter.convert(metadata, chapters, single_file)
            else:
                # No image extraction
                with st.spinner("🔄 Converting to Markdown..."):
                    converter = MarkdownConverter(output_dir)
                    created_files = converter.convert(metadata, chapters, single_file)

            if not created_files:
                st.error("❌ Conversion failed - no files were created")
                return

            # Success message with image count
            total_images = sum(len(chapter.images) for chapter in chapters)
            if total_images > 0:
                st.success(f"✅ Successfully converted to {len(created_files)} Markdown file(s) and extracted {total_images} image(s)!")
            else:
                st.success(f"✅ Successfully converted to {len(created_files)} Markdown file(s)!")

            # Show download section header
            st.header("📥 Download Converted Files")

            # Create download options
            # Use ZIP download if images are extracted OR multiple files mode
            if extract_images or len(created_files) > 1:
                # Multiple files - create ZIP
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    # Add markdown files
                    for file_path in created_files:
                        arcname = os.path.basename(file_path)
                        zip_file.write(file_path, arcname)

                    # Add images directory if it exists
                    images_dir = os.path.join(output_dir, "images")
                    if os.path.exists(images_dir):
                        for root, _, files in os.walk(images_dir):
                            for file in files:
                                file_path = os.path.join(root, file)
                                # Create archive path relative to output_dir
                                arcname = os.path.relpath(file_path, output_dir)
                                zip_file.write(file_path, arcname)

                zip_buffer.seek(0)
                zip_filename = f"{metadata.title.replace(' ', '_')}_markdown.zip"

                # Count total images across all chapters
                total_images = sum(len(chapter.images) for chapter in chapters)

                # Create label based on content
                if total_images > 0:
                    label = f"📥 Download ZIP Archive ({len(created_files)} files + {total_images} images)"
                else:
                    label = f"📥 Download ZIP Archive ({len(created_files)} files)"

                st.download_button(
                    label=label,
                    data=zip_buffer.getvalue(),
                    file_name=zip_filename,
                    mime="application/zip",
                    use_container_width=True
                )
            else:
                # Single file download without images
                file_path = created_files[0]
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                filename = os.path.basename(file_path)
                st.download_button(
                    label=f"📥 Download {filename}",
                    data=content,
                    file_name=filename,
                    mime="text/markdown",
                    use_container_width=True
                )

    except Exception as e:
        st.error(f"❌ Error during conversion: {str(e)}")
        logger.error(f"Error during conversion: {e}")

# Footer
def show_footer():
    """Display footer information."""
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; padding: 1rem;'>
            📚 EPUB to Markdown Converter | Built with Streamlit | 
            <a href='https://github.com/kyktommy/epub-to-markdown' target='_blank'>GitHub</a>
            <br />
            <a href="https://coff.ee/kyktommy">
                <img src="https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Support-orange?style=flat-square&logo=buy-me-a-coffee" />
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
    show_footer()
