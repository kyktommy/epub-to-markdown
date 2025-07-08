#!/usr/bin/env python3
"""
Standalone launcher for the EPUB to Markdown MCP Server

This script provides a convenient way to start the MCP server
without using the CLI interface.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from epub_to_markdown.mcp_server import main


if __name__ == "__main__":
    try:
        print("🚀 Starting EPUB to Markdown MCP Server...")
        print("📡 MCP server is running and ready to accept connections")
        print("🔧 Available tool:")
        print("   - convert_epub_to_markdown: Convert EPUB to single markdown file")
        print("\nPress Ctrl+C to stop the server")

        # Run the MCP server
        main()

    except KeyboardInterrupt:
        print("\n👋 MCP server stopped")
    except Exception as e:
        print(f"❌ Error starting MCP server: {str(e)}", file=sys.stderr)
        sys.exit(1)
