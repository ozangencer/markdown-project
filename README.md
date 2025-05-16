# Markdown Converter

A web application that converts various file formats to Markdown.

## Overview

This application allows users to easily convert different file types to Markdown format through a simple web interface. Users can upload files via drag-and-drop or file selection, and the application processes these files using the MarkItDown library.

## Features

- Convert various file formats to Markdown
- YouTube video transcription to Markdown with source URL reference
- AI-powered summarization and analysis of YouTube video transcripts
- Image to Markdown conversion using AI (requires OpenAI API key)
- Drag-and-drop file upload interface
- Visual file type recognition with custom icons
- Preview of converted Markdown content
- Download functionality for converted files
- Clean uploads folder with only Markdown output files
- Real-time processing indicators for long operations
- Responsive and user-friendly design

## Getting Started

### Prerequisites

- Python 3.x
- pip (Python package manager)
- OpenAI API key (for image conversion and YouTube summarization)

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

3. Configure your OpenAI API key:
   - Create a `.env` file in the project root
   - Add your OpenAI API key: `OPENAI_API_KEY=your_api_key_here`
   - This file is included in `.gitignore` for security

4. Run the application:
```bash
python app.py
```

5. Open your browser and navigate to:
```
http://127.0.0.1:5001
```

## Usage

### File Conversion
1. **Select File Tab**:
   - Click on the "File Upload" tab (default)

2. **Upload a File**:
   - Drag and drop a file onto the upload area, or
   - Click the upload area to select a file from your system

3. **Convert the File**:
   - Click the "Convert" button to start the conversion process

4. **View and Download Results**:
   - The converted Markdown will appear in the output area
   - Click the "Download Markdown" button to save the result

5. **Start Over**:
   - Click the "Clear" button to reset the interface and convert another file

### YouTube Transcription and Analysis
1. **Select YouTube Tab**:
   - Click on the "YouTube URL" tab

2. **Enter YouTube URL**:
   - Paste a valid YouTube video URL in the input field

3. **Convert the Video**:
   - Click the "Convert" button to extract and convert the transcript
   - Wait for the transcript to be processed (a loading indicator will be displayed)

4. **View and Download Transcript**:
   - The converted Markdown transcript will appear in the output area
   - The transcript includes the YouTube video URL as reference
   - Click the "Download Markdown" button to save the transcript

5. **Summarize and Analyze with AI**:
   - After the transcript is loaded, click the "Summarize with AI" button
   - The application will generate a comprehensive analysis including:
     - Brief summary of the video content
     - Main topics discussed
     - Key takeaways or insights
     - Notable quotes
     - Overall analysis

6. **View and Download Analysis**:
   - The AI-generated analysis will replace the transcript in the output area
   - The analysis includes the YouTube video URL as reference
   - Click the "Download Markdown" button to save the analysis

7. **Start Over**:
   - Click the "Clear" button to reset the interface and convert another video

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
