# Markdown Converter

A web application that converts various file formats to Markdown.

## Overview

This application allows users to easily convert different file types to Markdown format through a simple web interface. Users can upload files via drag-and-drop or file selection, and the application processes these files using the MarkItDown library.

## Features

- Convert various file formats to Markdown
- Drag-and-drop file upload interface
- Visual file type recognition with custom icons
- Preview of converted Markdown content
- Download functionality for converted files
- Responsive and user-friendly design

## Getting Started

### Prerequisites

- Python 3.x
- pip (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/markdown-project.git
cd markdown-project
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Open your browser and navigate to:
```
http://127.0.0.1:5000
```

## Usage

1. **Upload a File**:
   - Drag and drop a file onto the upload area, or
   - Click the upload area to select a file from your system

2. **Convert the File**:
   - Click the "Convert" button to start the conversion process

3. **View and Download Results**:
   - The converted Markdown will appear in the output area
   - Click the "Download Markdown" button to save the result

4. **Start Over**:
   - Click the "Clear" button to reset the interface and convert another file

## Supported File Types

The application supports various file formats through the MarkItDown library, including:

- Microsoft Office documents (.docx, .doc, .xlsx, .xls)
- PDF files
- Images (png, jpg, jpeg, gif)
- And other formats supported by the MarkItDown library

## License

[MIT License](LICENSE)

## Acknowledgments

- [Flask](https://flask.palletsprojects.com/) - Web framework
- [MarkItDown](https://pypi.org/project/markitdown/) - File conversion library
EOF < /dev/null
