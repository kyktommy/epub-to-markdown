#!/usr/bin/env python3
"""
Streamlit App Launcher

Run this script to start the Streamlit web interface for the EPUB to Markdown converter.
"""

import streamlit.web.cli as stcli
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🚀 Starting EPUB to Markdown Converter Web Interface...")
    print("🌐 Web interface will be available at: http://localhost:8501")
    print("\nPress Ctrl+C to stop the server")
    
    # Run Streamlit app
    sys.argv = [
        "streamlit",
        "run",
        "epub_to_markdown/streamlit_app.py",
        "--server.port=8501",
        "--server.address=0.0.0.0"
    ]
    
    stcli.main()
