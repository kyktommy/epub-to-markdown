#!/usr/bin/env python3
"""
FastAPI Server Launcher

Run this script to start the FastAPI server for the EPUB to Markdown converter.
"""

import uvicorn
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # Create downloads directory if it doesn't exist
    os.makedirs("downloads", exist_ok=True)
    
    print("🚀 Starting EPUB to Markdown Converter API...")
    print("📡 API will be available at: http://localhost:8000")
    print("📖 API documentation at: http://localhost:8000/docs")
    print("🔧 Alternative docs at: http://localhost:8000/redoc")
    print("\nPress Ctrl+C to stop the server")
    
    uvicorn.run(
        "epub_to_markdown.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
