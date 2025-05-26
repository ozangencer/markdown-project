# Markdown Converter

A web application that converts various file formats to Markdown.

## Overview

This application allows users to easily convert different file types to Markdown format through a simple web interface. Users can upload files via drag-and-drop or file selection, and the application processes these files using the MarkItDown library.

## Features

- Convert various file formats to Markdown
- **Multiple file conversion** - Convert multiple files at once into a single Markdown document
- **File accumulation system** - Add files progressively without losing previous selections
- YouTube video transcription to Markdown with source URL reference
- **Multiple YouTube URL processing** - Convert multiple YouTube videos in one operation
- AI-powered summarization and analysis of YouTube video transcripts
- **Batch YouTube summarization** - Summarize multiple YouTube videos together with AI
- **Custom AI restructuring** - Restructure any converted content with custom prompts
- **Professional .panda document processing** - Specialized business document analysis with intelligent default prompts for consulting materials (Gantt charts, process flows, tables, diagrams) - **Note: OpenAI provider recommended for optimal .panda document analysis**
- **Multi-AI Provider Support** - Choose between OpenAI, DeepSeek, and Google Gemini
- Image to Markdown conversion using AI with multiple provider options
- **Professional callout formatting** - AI image analysis results are presented in attractive callout boxes for better readability
- **Custom filename support** - Set custom names for downloaded Markdown files
- **Archive file processing** - ZIP files and other archive formats (like .panda) with automatic extraction and conversion of all contents
- **Folder drop support** - Drag and drop entire folders to convert all files inside recursively
- Natural sorting for extracted files with numerical names (e.g., "Slide1.png" before "Slide2.png")
- Drag-and-drop file upload interface with multi-file support
- **Clipboard image paste support** - Paste images directly from clipboard (screenshots, copied images)
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
- AI Provider API key (choose one or more):
  - OpenAI API key (for GPT-4o)
  - DeepSeek API key (for fast and cost-effective processing)
  - Google API key (for Gemini 2.5 Flash - fast image processing)

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

3. Configure your AI provider API keys:
   - Create a `.env` file in the project root
   - Add one or more API keys:
     ```
     OPENAI_API_KEY=your_openai_key_here
     DEEPSEEK_API_KEY=your_deepseek_key_here
     GOOGLE_API_KEY=your_google_key_here
     AI_PROVIDER=openai  # Default provider (optional)
     ```
   - This file is included in `.gitignore` for security

4. Run the application:
```bash
python app.py
```

5. Open your browser and navigate to:
```
http://127.0.0.1:5003
```

## Usage

### AI Provider Selection
1. **Choose AI Provider**:
   - In the "AI Provider Settings" section, select your preferred provider:
     - **OpenAI (GPT-4o)**: Best quality, supports all features including image processing
     - **DeepSeek**: Fast and cost-effective, text processing only
     - **Google (Gemini 2.5 Flash)**: Very fast, excellent image processing
   - The provider will be activated automatically when you select it from the dropdown
   - The status indicator will show if the provider is ready

### File Conversion
1. **Select File Tab**:
   - Click on the "File Upload" tab (default)

2. **Upload Files**:
   - Drag and drop one or more files onto the upload area, or
   - **Drag and drop entire folders** to automatically include all files inside, or
   - Click the upload area to select files from your system, or
   - **Paste images from clipboard** using Ctrl+V (Windows/Linux) or Cmd+V (Mac)
   - You can select multiple files at once and combine with pasted images and folder contents

3. **Manage Selected Files**:
   - View all selected files in the preview list
   - **Files accumulate**: New files are added to existing selection (no auto-clear)
   - Remove individual files by clicking the "Remove" button next to each file
   - **Duplicate prevention**: Same files (name + size) won't be added twice
   - Add more files by dragging, selecting, or pasting

4. **Convert the Files**:
   - Click the "Convert" button to start the conversion process
   - Multiple files will be combined into a single Markdown document
   - **Restructure with AI** button will become available after conversion

5. **Custom AI Restructuring** (Optional):
   - Click the "Restructure with AI" button after conversion
   - **For .panda files**: An intelligent default prompt automatically appears, specifically designed for business consulting documents (Gantt charts, process flows, tables, diagrams). This prompt ensures:
     - Complete transcription of all visible text (no summaries)
     - Detailed analysis of business processes and data
     - Comprehensive documentation of timelines, metrics, and relationships
     - Professional consulting-grade output with technical details
   - **For other files**: Enter your custom prompt (e.g., "Create a table of contents", "Summarize key points", "Extract action items")
   - You can always modify the default prompt or write your own
   - Click "Execute" to process the content with your custom instructions
   - The restructured content will replace the original output

6. **View and Download Results**:
   - The converted (or restructured) Markdown will appear in the output area
   - **Optional**: Enter a custom filename in the "File Name" field
   - Click the "Download Markdown" button to save the result with your chosen name

7. **Start Over**:
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

5. **AI Processing Options** (after transcripts are loaded):

   **Summarize All with AI**:
   - Click the "Summarize All with AI" button for predefined comprehensive analysis
   - Generates: Brief overview, main topics, key takeaways, notable quotes, and analysis
   
   **Restructure with AI** (Custom):
   - Click the "Restructure with AI" button for custom processing
   - Enter your own prompt (e.g., "Extract all mentioned tools and technologies", "Create a FAQ from this content")
   - Get personalized analysis based on your specific needs

6. **View and Download Results**:
   - The AI-generated content will replace the transcripts in the output area
   - All content includes YouTube video URLs as references
   - **Optional**: Enter a custom filename in the "File Name" field
   - Click the "Download Markdown" button to save the results

7. **Start Over**:
   - Click the "Clear" button to reset the interface and convert more videos

## Supported File Types

The application supports various file formats through the MarkItDown library, including:

- Microsoft Office documents (.docx, .doc, .xlsx, .xls, .pptx, .ppt)
- PDF files
- Images (png, jpg, jpeg, gif) - **AI-powered analysis with multiple provider support and professional callout formatting**
- **Archive files** (ZIP, .panda and other configured formats - extracts and converts all files inside, excluding hidden files)
- **Folders** (drag and drop entire folders to process all contents recursively)
- And other formats supported by the MarkItDown library

## AI Provider Capabilities

| Feature | OpenAI (GPT-4o) | DeepSeek | Google (Gemini 2.5 Flash) |
|---------|----------------|----------|---------------------------|
| Text Processing | ✅ Excellent | ✅ Fast & Cost-effective | ✅ Very Fast |
| Image Processing | ✅ GPT-4V | ❌ Not supported yet* | ✅ Gemini Vision |
| YouTube Summarization | ✅ Comprehensive | ✅ Efficient | ✅ Detailed |
| .panda Document Analysis | ✅ **Recommended** | ✅ Good | 🟡 Limited** |
| Speed | 🟡 Moderate | 🟢 Very Fast | 🟢 Very Fast |
| Cost | 🟡 Premium | 🟢 Budget-friendly | 🟢 Free tier available |

*DeepSeek-VL2 (vision model) is coming soon to the API
**Google provider may have limitations with complex business document analysis due to safety filters

## Getting API Keys

### OpenAI
1. Visit: https://platform.openai.com/
2. Sign up/Login and go to API Keys
3. Create a new API key

### DeepSeek
1. Visit: https://platform.deepseek.com/
2. Sign up/Login and go to API Keys
3. Create a new API key

### Google AI
1. Visit: https://aistudio.google.com/
2. Click "Get API key"
3. Create a new API key

## Customizing AI Prompts

The application uses customizable prompt templates stored in `prompt_templates.json`:

- **File-specific prompts**: Different templates for .panda, .xlsx, .docx, .pdf files
- **Easy customization**: Edit the JSON file to modify or add new prompt templates
- **Automatic detection**: System automatically selects appropriate template based on file type
- **Consulting focus**: .panda files get specialized business document analysis prompts by default

To customize prompts, simply edit `prompt_templates.json` and restart the application.


