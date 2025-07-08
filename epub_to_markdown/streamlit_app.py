"""
Streamlit Web Interface for EPUB to Markdown Converter

This module provides a user-friendly web interface for converting EPUB files to markdown format.
"""

import os
import tempfile
import shutil
import zipfile
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
    
    st.header("📁 Upload EPUB File")
    
    uploaded_file = st.file_uploader(
        "Choose an EPUB file",
        type=['epub'],
        help="Upload your EPUB file to convert it to Markdown format"
    )
    
    if uploaded_file is not None:
        # Display file information
        st.markdown(f"**File:** {uploaded_file.name}")
        st.markdown(f"**Size:** {uploaded_file.size:,} bytes")

        show_metadata, show_chapters, auto_download = True, True, True
        
        # Process the file
        process_epub_file(uploaded_file, single_file, show_metadata, show_chapters, auto_download)

def process_epub_file(uploaded_file, single_file, show_metadata, show_chapters, auto_download):
    """Process the uploaded EPUB file."""
    
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.epub') as temp_file:
            temp_file.write(uploaded_file.read())
            temp_file_path = temp_file.name
        
        # Parse EPUB
        with st.spinner("📖 Parsing EPUB file..."):
            parser = EPUBParser(temp_file_path)
            metadata, chapters = parser.parse()
        
        if not chapters:
            st.error("❌ No chapters found in the EPUB file")
            return
        
        # Display book information
        if show_metadata:
            display_book_metadata(metadata)
        
        # Display chapters information
        if show_chapters:
            display_chapters_info(chapters)
        
        # Conversion section
        st.header("🔄 Convert to Markdown")
        
        if st.button("🚀 Convert to Markdown", type="primary", use_container_width=True):
            convert_and_download(temp_file_path, metadata, chapters, single_file, auto_download)
        
    except Exception as e:
        st.error(f"❌ Error processing EPUB file: {str(e)}")
        logger.error(f"Error processing EPUB: {e}")
    
    finally:
        # Clean up temporary file
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
        st.markdown(f"_{metadata.description[:300]}{'...' if len(metadata.description) > 300 else ''}_")

def display_chapters_info(chapters):
    """Display chapters information."""
    
    st.header(f"📑 Chapters ({len(chapters)} found)")
    
    # Create a dataframe for better display
    chapter_data = []
    for i, chapter in enumerate(chapters, 1):
        word_count = len(chapter.content.split())
        chapter_data.append({
            "Chapter": i,
            "Title": chapter.title,
            "Words": f"{word_count:,}",
            "File": chapter.file_name
        })
    
    st.dataframe(chapter_data, use_container_width=True)

def convert_and_download(epub_path, metadata, chapters, single_file, auto_download):
    """Convert EPUB to markdown and provide download."""
    
    try:
        # Create temporary output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = os.path.join(temp_dir, "output")
            
            # Convert to markdown
            with st.spinner("🔄 Converting to Markdown..."):
                converter = MarkdownConverter(output_dir)
                created_files = converter.convert(metadata, chapters, single_file)
            
            if not created_files:
                st.error("❌ Conversion failed - no files were created")
                return
            
            # Success message
            st.success(f"✅ Successfully converted to {len(created_files)} Markdown file(s)!")
            
            # Create download options
            if len(created_files) == 1:
                # Single file download
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
            else:
                # Multiple files - create ZIP
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for file_path in created_files:
                        arcname = os.path.basename(file_path)
                        zip_file.write(file_path, arcname)
                
                zip_buffer.seek(0)
                zip_filename = f"{metadata.title.replace(' ', '_')}_markdown.zip"
                
                st.download_button(
                    label=f"📥 Download ZIP Archive ({len(created_files)} files)",
                    data=zip_buffer.getvalue(),
                    file_name=zip_filename,
                    mime="application/zip",
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
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
    show_footer()
