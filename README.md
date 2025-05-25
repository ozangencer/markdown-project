# Markdown Converter

A web application that converts various file formats to Markdown.

## Overview

This application allows users to easily convert different file types to Markdown format through a simple web interface. Users can upload files via drag-and-drop or file selection, and the application processes these files using the MarkItDown library.

## Features

- Convert various file formats to Markdown
- **Multiple file conversion** - Convert multiple files at once into a single Markdown document
- YouTube video transcription to Markdown with source URL reference
- **Multiple YouTube URL processing** - Convert multiple YouTube videos in one operation
- AI-powered summarization and analysis of YouTube video transcripts
- **Batch YouTube summarization** - Summarize multiple YouTube videos together with AI
- Image to Markdown conversion using AI (requires OpenAI API key)
- ZIP file processing with automatic extraction and conversion of all contents
- Natural sorting for extracted files with numerical names (e.g., "Slide1.png" before "Slide2.png")
- Drag-and-drop file upload interface with multi-file support
- Visual file type recognition with custom icons
- Individual file preview and removal before conversion
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

2. **Upload Files**:
   - Drag and drop one or more files onto the upload area, or
   - Click the upload area to select files from your system
   - You can select multiple files at once

3. **Manage Selected Files**:
   - View all selected files in the preview list
   - Remove individual files by clicking the "Remove" button next to each file
   - Add more files by dragging or selecting again

4. **Convert the Files**:
   - Click the "Convert" button to start the conversion process
   - Multiple files will be combined into a single Markdown document

5. **View and Download Results**:
   - The converted Markdown will appear in the output area
   - Click the "Download Markdown" button to save the result

6. **Start Over**:
   - Click the "Clear" button to reset the interface and convert more files

### YouTube Transcription and Analysis
1. **Select YouTube Tab**:
   - Click on the "YouTube URL" tab

2. **Enter YouTube URLs**:
   - Paste a valid YouTube video URL in the input field
   - Click "+ Add Another URL" to add more YouTube URLs
   - You can add as many URLs as needed
   - Remove individual URLs using the "Remove" button (visible when you have more than one URL)

3. **Convert the Videos**:
   - Click the "Convert All" button to extract and convert all transcripts
   - Wait for the transcripts to be processed (a loading indicator will be displayed)
   - All videos will be processed sequentially

4. **View and Download Transcripts**:
   - The converted Markdown transcripts will appear in the output area
   - Each transcript includes its YouTube video URL as reference
   - All transcripts are combined into a single document
   - Click the "Download Markdown" button to save all transcripts

5. **Summarize and Analyze with AI**:
   - After the transcripts are loaded, click the "Summarize All with AI" button
   - The application will generate a comprehensive analysis including:
     - Brief overview of all videos
     - Individual summaries for each video
     - Common themes across all videos
     - Key takeaways from the collection
     - Connections or contrasts between videos

6. **View and Download Analysis**:
   - The AI-generated analysis will replace the transcripts in the output area
   - The analysis includes all YouTube video URLs as references
   - Click the "Download Markdown" button to save the analysis

7. **Start Over**:
   - Click the "Clear" button to reset the interface and convert more videos

## Supported File Types

The application supports various file formats through the MarkItDown library, including:

- Microsoft Office documents (.docx, .doc, .xlsx, .xls)
- PDF files
- Images (png, jpg, jpeg, gif)
- ZIP archives (extracts and converts all files inside)
- And other formats supported by the MarkItDown library


