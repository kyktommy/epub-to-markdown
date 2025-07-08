# epub-to-markdown

A Python library with multiple interfaces for parsing EPUB files and converting them to properly formatted markdown files.

## Support

If you find this project helpful, consider buying me a coffee! ☕

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Support-orange?style=flat-square&logo=buy-me-a-coffee)](https://coff.ee/kyktommy)

## Features

- 📚 **Parse EPUB files** - Extract content, metadata, and structure from EPUB files
- 📝 **Convert to Markdown** - Generate clean, properly formatted markdown files
- 🖼️ **Image Extraction** - Extract, resize, and optimize images from EPUB files (multiple files mode only)
- 🔧 **Multiple Interfaces** - Command line, REST API, and web UI
- 🌐 **Web Interface** - User-friendly Streamlit web application
- 🚀 **REST API** - FastAPI-based API for integration
- 📊 **Batch Processing** - Convert multiple EPUB files at once
- 📖 **Rich Metadata** - Preserve book information (title, author, publisher, etc.)
- 🔍 **Chapter Analysis** - Extract and organize chapters with proper titles

## Build from sources

### Dependencies

```bash
git clone https://github.com/kyktommy/epub-to-markdown
cd epub-to-markdown
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Required Packages

- Python 3.8+
- ebooklib >= 0.18
- beautifulsoup4 >= 4.12.0
- lxml >= 4.9.0
- markdownify >= 0.11.6
- click >= 8.1.0
- fastapi >= 0.104.0
- uvicorn[standard] >= 0.24.0
- streamlit >= 1.28.0
- python-multipart >= 0.0.6
- aiofiles >= 23.2.0
- Pillow >= 10.0.0
- mozjpeg-lossless-optimization >= 1.1.0

## Usage Options

### 1. Web Interface (Streamlit) - Recommended for Users

Start the web interface using the CLI:

```bash
epub-to-markdown web
# or
python -m epub_to_markdown.cli web
```

Alternative using the standalone script:

```bash
python run_streamlit.py
```

Then open your browser to: http://localhost:8501

**Web Interface Options:**
- **Output Format**: Choose between single file or multiple files
- **Image Extraction**: Optional checkbox (disabled by default)
  - When enabled: Always downloads as ZIP (even for single file mode)
  - When disabled: Single file downloads as `.md`, multiple files as ZIP

**Features:**
- Drag & drop EPUB file upload
- Book information display
- Chapter title preview
- Output format options (single file or multiple files)
- Optional image extraction (disabled by default)
- Smart download format: individual file or ZIP based on settings
- User-friendly interface with progress indicators

### 2. REST API (FastAPI) - For Developers

Start the API server using the CLI:

```bash
epub-to-markdown api
# or
python -m epub_to_markdown.cli api
```

Alternative using the standalone script:

```bash
python run_api.py
```

API will be available at: http://localhost:8000

**API Documentation:**
- Interactive docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

**API Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information |
| `/info` | POST | Get EPUB file information |
| `/convert` | POST | Convert EPUB to markdown (single file → individual download, multiple files → ZIP) |
| `/download/{filename}` | GET | Download converted files |
| `/health` | GET | Health check |

**Example API Usage:**

```bash
# Get book information
curl -X POST "http://localhost:8000/info" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@book.epub"

# Convert EPUB to markdown (single file is now default - returns individual file)
curl -X POST "http://localhost:8000/convert" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@book.epub"

# Convert to multiple files (one per chapter - returns ZIP archive)
curl -X POST "http://localhost:8000/convert" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@book.epub" \
  -F "single_file=false"
```

### 3. Command Line Interface

**Available Commands:**

```bash
epub-to-markdown                    # Show help and available commands
epub-to-markdown convert book.epub  # Convert EPUB to markdown
epub-to-markdown info book.epub     # Show book information
epub-to-markdown batch directory/   # Batch convert directory
epub-to-markdown web               # Launch Streamlit web interface
epub-to-markdown api               # Launch FastAPI server
```

**Convert Command Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--output-dir` | `-o` | Output directory (default: same directory as input file) |
| `--multiple-files` | `-m` | Create multiple markdown files (one per chapter) |
| `--extract-images/--no-extract-images` | `-i` | Extract and process images from EPUB (only available in multiple files mode) |
| `--verbose` | `-v` | Enable verbose logging |

**Web Interface Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--port` | `-p` | Port to run on (default: 8501) |
| `--host` | `-h` | Host to bind to (default: 0.0.0.0) |

**API Server Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--port` | `-p` | Port to run on (default: 8000) |
| `--host` | `-h` | Host to bind to (default: 0.0.0.0) |
| `--reload` |  | Enable auto-reload for development |

**Example Usage:**

```bash
# Convert to same directory as input file (default behavior)
epub-to-markdown convert book.epub

# Convert with custom output directory
epub-to-markdown convert book.epub --output-dir /path/to/output

# Convert to multiple files (one per chapter) with image extraction
epub-to-markdown convert book.epub --multiple-files

# Convert to multiple files without extracting images
epub-to-markdown convert book.epub --multiple-files --no-extract-images

# Note: Image extraction is only available in multiple files mode

# Get book information only
epub-to-markdown info book.epub

# Batch convert directory
epub-to-markdown batch /path/to/epub/directory

# Launch web interface on custom port
epub-to-markdown web --port 8080

# Launch API with auto-reload
epub-to-markdown api --reload
```

### 4. Python API

Use programmatically in your Python code:

```python
from epub_to_markdown import EPUBParser, MarkdownConverter

# Parse EPUB file
parser = EPUBParser('book.epub')
metadata, chapters = parser.parse()

# Convert to markdown (single_file=True is now default)
converter = MarkdownConverter('output')
created_files = converter.convert(metadata, chapters)

print(f"Created {len(created_files)} files")
```

## Output Formats

### Single File Mode (Default)

```
output/
└── {book_title}.md                # All content in one file (no images)
```

### Multiple Files Mode

```
output/
├── {book_title}_index.md          # Main index with TOC
├── chapter_01_{chapter_title}.md  # Individual chapters
├── chapter_02_{chapter_title}.md
├── images/                        # Extracted and processed images
│   ├── img_001_cover.jpg
│   ├── img_002_diagram.jpg
│   └── ...
└── ...
```

**ZIP Archive Contents:**
- All markdown files
- Complete `images/` directory with all processed images
- Maintains folder structure for easy extraction

## Image Processing

The tool automatically extracts and processes images from EPUB files in **multiple files mode only** with the following features:

### Image Extraction Features
- **EPUB Files Only** - Image extraction works only with EPUB format files
- **Multiple Files Mode Only** - Images are only extracted when using `--multiple-files` option
- **Automatic Detection** - Finds all images referenced in EPUB chapters
- **Format Conversion** - Converts all images to optimized JPEG format
- **Mozjpeg Compression** - Uses mozjpeg for superior compression quality
- **Smart Resizing** - Resizes images to maximum 1920x1080 while maintaining aspect ratio
- **Caption Extraction** - Automatically extracts captions from figcaption tags and context

### Image Output
- Images are saved in the `images/` subdirectory
- **Smart Filename Format** (priority order):
  1. **Caption-based**: `descriptive_caption.jpg` (if caption available)
  2. **Page-based**: `page_001.jpg` (if page number available)
  3. **Chapter-based**: `chapter_001.jpg` (fallback sequence)
- **Conflict Resolution**: Duplicate names get `_01`, `_02` suffix
- **Included in ZIP**: All images are automatically included in the ZIP archive for multiple files mode
- Each image includes metadata overlay with:
  - Caption (if available)
  - Page/chapter number
  - Chapter title
  - Image dimensions and file size

### Image Extraction Usage

**CLI (Multiple Files Mode Only):**
```bash
# Enable image extraction (requires multiple files mode)
epub-to-markdown convert book.epub --multiple-files

# Disable image extraction in multiple files mode
epub-to-markdown convert book.epub --multiple-files --no-extract-images

# Single file mode (images not supported)
epub-to-markdown convert book.epub  # No images extracted
```

**API:**
```bash
# Multiple files with images
curl -X POST "http://localhost:8000/convert" \
  -F "file=@book.epub" \
  -F "single_file=false" \
  -F "extract_images=true"

# Multiple files without images
curl -X POST "http://localhost:8000/convert" \
  -F "file=@book.epub" \
  -F "single_file=false" \
  -F "extract_images=false"
```

**Web Interface:**
- Use the "🖼️ Extract images" checkbox (disabled by default)
- When enabled: Always downloads as ZIP (even for single file mode)
- When disabled: Single file downloads as `.md`, multiple files as ZIP

## Web Interface Screenshots

### Main Upload Interface
- Clean, intuitive file upload
- Real-time file validation
- Progress indicators

### Book Information Display
- Complete metadata extraction
- Chapter listing with word counts
- Publication details

### Conversion Results
- Download options (individual files or ZIP)
- File size information
- Success/error feedback

## API Response Examples

### Book Information Response

```json
{
  "title": "The Great Gatsby",
  "author": "F. Scott Fitzgerald",
  "language": "en",
  "identifier": "isbn:9780743273565",
  "publisher": "Scribner",
  "description": "A classic American novel...",
  "chapter_count": 9
}
```

### Conversion Response

**Single File Mode (Default):**
```json
{
  "success": true,
  "message": "Successfully converted EPUB to single markdown file",
  "book_info": { ... },
  "created_files": [
    "The_Great_Gatsby.md"
  ],
  "download_url": "/download/The_Great_Gatsby.md"
}
```

**Multiple Files Mode:**
```json
{
  "success": true,
  "message": "Successfully converted EPUB to multiple markdown files with 5 images",
  "book_info": { ... },
  "created_files": [
    "The_Great_Gatsby_index.md",
    "chapter_01_Chapter_1.md",
    "chapter_02_Chapter_2.md"
  ],
  "download_url": "/download/The_Great_Gatsby_markdown.zip"
}
```

**Note:** The ZIP archive includes both markdown files and the complete `images/` directory.

## Development

### Running in Development Mode

```bash
# Start API with auto-reload
python run_api.py

# Start Streamlit with auto-reload
python run_streamlit.py
```

### Project Structure

```
epub-to-markdown/
├── epub_to_markdown/
│   ├── __init__.py
│   ├── epub_parser.py      # Core EPUB parsing
│   ├── markdown_converter.py  # Markdown conversion
│   ├── image_extractor.py  # Image extraction and processing
│   ├── cli.py             # Command line interface
│   ├── api.py             # FastAPI REST API
│   └── streamlit_app.py   # Streamlit web interface
├── run_api.py             # API server launcher
├── run_streamlit.py       # Streamlit launcher
├── requirements.txt       # Dependencies
└── README.md
```

## Error Handling

All interfaces provide comprehensive error handling:

- **File validation** - Ensures uploaded files are valid EPUB format
- **Parsing errors** - Clear messages for corrupted or unsupported files
- **Conversion failures** - Detailed error reporting
- **Network issues** - Graceful handling of API timeouts

## License

This project is licensed under the MIT License.