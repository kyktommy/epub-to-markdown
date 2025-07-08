"""
FastAPI Web Interface for EPUB to Markdown Converter

This module provides a REST API for converting EPUB files to markdown format.
"""

import os
import tempfile
import shutil
import zipfile
from typing import List, Optional
from pathlib import Path
import aiofiles
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

from .epub_parser import EPUBParser, EPUBMetadata, EPUBChapter
from .markdown_converter import MarkdownConverter

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="EPUB to Markdown Converter API",
    description="Convert EPUB files to markdown format via REST API",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API responses
class BookInfo(BaseModel):
    title: str
    author: str
    language: str
    identifier: str
    publisher: Optional[str] = None
    description: Optional[str] = None
    rights: Optional[str] = None
    chapter_count: int

class ChapterInfo(BaseModel):
    title: str
    file_name: str
    order: int
    word_count: int

class ConversionResult(BaseModel):
    success: bool
    message: str
    book_info: Optional[BookInfo] = None
    created_files: List[str] = []
    download_url: Optional[str] = None

class ConversionStatus(BaseModel):
    task_id: str
    status: str  # "pending", "processing", "completed", "failed"
    message: str
    result: Optional[ConversionResult] = None

# In-memory storage for conversion tasks (in production, use Redis or database)
conversion_tasks = {}

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "EPUB to Markdown Converter API",
        "version": "0.1.0",
        "endpoints": {
            "convert": "/convert",
            "info": "/info",
            "status": "/status/{task_id}",
            "download": "/download/{filename}"
        }
    }

@app.post("/info", response_model=BookInfo)
async def get_epub_info(file: UploadFile = File(...)):
    """
    Get information about an EPUB file without converting it.
    """
    if not file.filename.lower().endswith('.epub'):
        raise HTTPException(status_code=400, detail="File must be an EPUB file")
    
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.epub') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Parse EPUB
            parser = EPUBParser(temp_file_path)
            metadata, chapters = parser.parse()
            
            return BookInfo(
                title=metadata.title,
                author=metadata.author,
                language=metadata.language,
                identifier=metadata.identifier,
                publisher=metadata.publisher,
                description=metadata.description,
                rights=metadata.rights,
                chapter_count=len(chapters)
            )
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
            
    except Exception as e:
        logger.error(f"Error processing EPUB info: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing EPUB file: {str(e)}")

@app.post("/convert", response_model=ConversionResult)
async def convert_epub(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    single_file: bool = Form(True)
):
    """
    Convert an EPUB file to markdown format.

    Output format is automatically determined:
    - Single file mode: Returns individual file for download
    - Multiple files mode: Returns ZIP archive
    """
    if not file.filename.lower().endswith('.epub'):
        raise HTTPException(status_code=400, detail="File must be an EPUB file")
    
    try:
        # Create temporary directories
        temp_dir = tempfile.mkdtemp()
        output_dir = os.path.join(temp_dir, "output")
        
        # Save uploaded file
        epub_path = os.path.join(temp_dir, file.filename)
        async with aiofiles.open(epub_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        try:
            # Parse EPUB
            parser = EPUBParser(epub_path)
            metadata, chapters = parser.parse()
            
            if not chapters:
                raise HTTPException(status_code=400, detail="No chapters found in EPUB file")
            
            # Convert to markdown
            converter = MarkdownConverter(output_dir)
            created_files = converter.convert(metadata, chapters, single_file)
            
            if not created_files:
                raise HTTPException(status_code=500, detail="Conversion failed - no files created")
            
            # Create book info
            book_info = BookInfo(
                title=metadata.title,
                author=metadata.author,
                language=metadata.language,
                identifier=metadata.identifier,
                publisher=metadata.publisher,
                description=metadata.description,
                rights=metadata.rights,
                chapter_count=len(chapters)
            )
            
            # Handle output format based on single_file setting
            if single_file:
                # Single file mode: Return individual file for download
                if len(created_files) != 1:
                    raise HTTPException(status_code=500, detail="Expected single file but got multiple files")

                # Move single file to downloads directory
                downloads_dir = "downloads"
                os.makedirs(downloads_dir, exist_ok=True)

                original_file = created_files[0]
                filename = os.path.basename(original_file)
                final_file_path = os.path.join(downloads_dir, filename)
                shutil.move(original_file, final_file_path)

                # Schedule cleanup
                background_tasks.add_task(cleanup_temp_dir, temp_dir)

                return ConversionResult(
                    success=True,
                    message=f"Successfully converted EPUB to single markdown file",
                    book_info=book_info,
                    created_files=[filename],
                    download_url=f"/download/{filename}"
                )
            else:
                # Multiple files mode: Return ZIP archive
                zip_filename = f"{metadata.title.replace(' ', '_')}_markdown.zip"
                zip_path = os.path.join(temp_dir, zip_filename)

                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in created_files:
                        arcname = os.path.basename(file_path)
                        zipf.write(file_path, arcname)

                # Move ZIP to downloads directory
                downloads_dir = "downloads"
                os.makedirs(downloads_dir, exist_ok=True)
                final_zip_path = os.path.join(downloads_dir, zip_filename)
                shutil.move(zip_path, final_zip_path)

                # Schedule cleanup
                background_tasks.add_task(cleanup_temp_dir, temp_dir)

                return ConversionResult(
                    success=True,
                    message=f"Successfully converted EPUB to multiple markdown files",
                    book_info=book_info,
                    created_files=[os.path.basename(f) for f in created_files],
                    download_url=f"/download/{zip_filename}"
                )
                
        finally:
            # Cleanup is handled by background tasks for both single file and zip modes
            pass
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error converting EPUB: {e}")
        raise HTTPException(status_code=500, detail=f"Error converting EPUB file: {str(e)}")

@app.get("/download/{filename}")
async def download_file(filename: str):
    """
    Download a converted markdown file.
    """
    file_path = os.path.join("downloads", filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/zip' if filename.endswith('.zip') else 'text/markdown'
    )

@app.get("/chapters/{filename}")
async def get_chapters(filename: str):
    """
    Get detailed chapter information from an uploaded EPUB file.
    """
    # This would require storing uploaded files temporarily
    # Implementation depends on your storage strategy
    raise HTTPException(status_code=501, detail="Not implemented yet")

def cleanup_temp_dir(temp_dir: str):
    """Background task to clean up temporary directories."""
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
        logger.info(f"Cleaned up temporary directory: {temp_dir}")
    except Exception as e:
        logger.error(f"Error cleaning up temporary directory {temp_dir}: {e}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "epub-to-markdown-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
