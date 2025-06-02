# Technical Documentation - Markdown Converter

This document provides technical details about the Markdown Converter application, its architecture, and implementation.

## Technology Stack

- **Backend**: Python 3.x with Flask framework
- **Frontend**: HTML, CSS, JavaScript (vanilla)
- **File Conversion**: markitdown library
- **AI Services**: Multi-provider support
  - OpenAI API (GPT-4o model)
  - DeepSeek API (DeepSeek-V3 model)
  - Google Generative AI (Gemini 2.5 Flash Preview)
- **AI Provider Management**: Abstract factory pattern with modular provider system

## Application Architecture

The application follows a simple client-server architecture:

1. **Client-side**: Browser-based UI for file uploading and displaying results
2. **Server-side**: Flask web server that handles requests and performs file conversions
3. **AI Integration**: Multi-provider AI system supporting OpenAI, DeepSeek, and Google APIs
4. **AI Provider Layer**: Abstracted provider interface allowing runtime switching between AI services

## Prompt Library System

The application implements a centralized prompt management system that replaces hardcoded prompts throughout the codebase.

### Architecture

1. **Prompt Storage**: All prompts are stored in `prompt_library.json` with metadata:
   - `name`: Human-readable prompt name
   - `description`: Purpose and usage description
   - `category`: Organization category (file_processing, youtube, general, system, file_templates)
   - `prompt`: The actual prompt text with variable placeholders

2. **Dynamic Loading**: Prompts are loaded using the `get_prompt()` function:
   ```python
   def get_prompt(prompt_key, variables=None):
       library = load_prompt_library()
       prompt = library[prompt_key]['prompt']
       # Replace variables like {youtube_url}, {content}
       if variables:
           for key, value in variables.items():
               prompt = prompt.replace(f'{{{key}}}', str(value))
       return prompt
   ```

3. **Frontend Management**: The Prompt Preferences tab provides:
   - Category-based organization
   - Real-time editing with syntax highlighting
   - Variable detection and display
   - Save/Reset functionality
   - Visual feedback for operations

### API Endpoints

- `GET /prompt-library`: Retrieve all prompts
- `POST /prompt-library`: Update a specific prompt
  ```json
  {
    "key": "image_analysis",
    "prompt": "Updated prompt content..."
  }
  ```

### Variable System

Prompts support dynamic variables using `{variable_name}` syntax:
- `{youtube_url}`: Replaced with actual YouTube URL
- `{transcript}`: Replaced with video transcript
- `{content}`: Replaced with document content
- `{custom_prompt}`: User-provided custom instructions
- `{videos_content}`: Multiple video transcripts

### Migration from Hardcoded Prompts

All hardcoded prompts have been migrated to the prompt library:
- Image analysis prompts (3 instances)
- YouTube summarization prompts (single and multiple)
- Content restructuring prompt
- File-specific templates (.panda, .xlsx, .pdf, .docx)

Note: System prompts remain hardcoded as they define AI behavior and are not intended for user modification.

## Component Breakdown

### Backend (Python/Flask)

The backend is implemented in `app.py` using Flask:

- **Routes**:
  - `/` - Serves the main application page
  - `/convert` - Handles file uploads and conversion (POST)
  - `/convert-youtube-multiple` - Handles multiple YouTube URL transcription (POST)
  - `/summarize-youtube-multiple` - Processes YouTube transcripts using selected AI provider (POST)
  - `/restructure` - Custom AI restructuring with user-defined prompts (POST)
  - `/ai-providers` - GET/POST endpoints for AI provider management
  - `/download/<filename>` - Facilitates downloading converted files
  - `/download-custom` - Custom filename download endpoint with content formatting (POST)

- **File Processing**:
  - Uses the `MarkItDown` library to convert uploaded files to Markdown
  - **Enhanced Email Processing**: Custom .eml parser using Python's email module for structured output with clean headers, message body, and attachment information (fallback to MarkItDown if needed)
  - Creates temporary files for processing and removes them after conversion
  - Only keeps generated Markdown files in the `uploads` directory
  - Stores all outputs with unique identifiers in filenames
  - Adds source URL references to YouTube transcripts and summaries

- **AI Integration**:
  - **Multi-Provider Architecture**: Supports OpenAI, DeepSeek, and Google AI providers
  - **Runtime Provider Switching**: Users can change AI providers during session
  - **Provider-Specific Image Processing**: 
    - OpenAI: Uses GPT-4V via MarkItDown
    - Google: Uses Gemini Vision API directly
    - DeepSeek: Text-only (image processing not supported)
  - **Intelligent Fallback**: Automatic provider detection and error handling
  - Sends YouTube transcripts to selected AI provider for comprehensive summarization
  - Generates structured markdown content from AI responses

- **Content Formatting**:
  - **Professional Callout System**: AI image analysis results are automatically formatted in callout boxes
  - **Download-time Processing**: Content cleaning and formatting applied during both conversion and download
  - **Markdown Enhancement**: HTML comments and text markers converted to GitHub-style callouts

- **Environment Management**:
  - Uses python-dotenv for securing API keys
  - Loads configuration from .env file (not tracked in git)

- **Error Handling**:
  - Validates file uploads and API requests
  - Checks for AI provider availability before making API calls
  - Provider-specific error messaging (e.g., DeepSeek image processing limitation)
  - Provides appropriate error responses for various failure scenarios
  - Graceful degradation when providers are unavailable

### Frontend (HTML/CSS/JavaScript)

The frontend consists of:

#### HTML (`templates/index.html`)
- Basic structure for the application interface
- **AI Provider Selection Interface**: Dropdown and controls for provider switching
- Tab system for different conversion modes (file upload and YouTube URL)
- Form for file uploads and YouTube URL input
- **Custom Filename Input**: User can specify custom names for downloads
- Information box for API key requirements
- Loading overlay for processing feedback
- Display areas for file previews and conversion results

#### CSS (`static/styles.css`)
- Dark-themed modern UI
- Responsive design elements
- Tab-based interface styling
- **AI Provider Interface Styling**: Provider selection, status indicators
- **Custom Filename Input Styling**: Form controls and layout
- Loading spinner and overlay animation
- Styling for drag-and-drop functionality
- Button states (normal, hover, disabled)
- Visual feedback for user interactions

#### JavaScript (`static/script.js`)
- Handles tab switching between conversion modes
- **AI Provider Management**: Load available providers, auto-switch on dropdown change, status updates
- **Automatic Provider Switching**: Provider changes instantly when dropdown selection changes
- Manages drag-and-drop file uploads
- **Clipboard Image Paste**: Handles paste events, converts clipboard images to File objects
- **File Accumulation System**: Progressive file addition with duplicate prevention
- **Folder Drop Processing**: Recursively reads directory contents using webkitGetAsEntry() API
- **Custom AI Restructuring**: Modal interface for user-defined prompts, API integration
- **Intelligent .panda Document Processing**: Auto-detection of business consulting documents (.panda files or .md + .png combinations) with specialized default prompts for comprehensive analysis
- Manages file type detection and icon display
- **Custom Filename Handling**: User input validation and custom download logic
- Tracks current YouTube transcript for summarization
- Handles transcript conversion and AI summarization
- Performs asynchronous form submissions
- Implements loading state with UI feedback
- Disables controls during processing
- Updates UI with conversion results
- Facilitates downloading converted files with custom names

## AI Provider Architecture

### Provider System Design

The application implements a modular AI provider system using the Abstract Factory pattern, allowing seamless switching between different AI services.

#### Core Components

1. **AIProvider (Abstract Base Class)**:
   ```python
   class AIProvider(ABC):
       @abstractmethod
       def is_available(self) -> bool
       @abstractmethod 
       def chat_completion(self, messages: list, max_tokens: int = 1500) -> str
       @abstractmethod
       def get_client_for_markitdown(self)
       @abstractmethod
       def get_model_name(self) -> str
       @abstractmethod
       def process_image(self, image_path: str, prompt: str = None) -> str
   ```

2. **Concrete Provider Implementations**:
   - **OpenAIProvider**: Uses GPT-4o model, full MarkItDown integration
   - **DeepSeekProvider**: Uses DeepSeek-V3 model, text-only processing
   - **GoogleProvider**: Uses Gemini 2.5 Flash Preview, native vision support

3. **AIProviderFactory**: Manages provider instantiation and availability checking

#### Provider-Specific Features

| Provider | Model | Image Processing | MarkItDown Support | Special Features |
|----------|-------|------------------|-------------------|------------------|
| OpenAI | GPT-4o | ✅ GPT-4V | ✅ Full | Industry standard, **best for .panda** |
| DeepSeek | DeepSeek-V3 | ❌ Text only* | ✅ Compatible | Cost-effective, fast |
| Google | Gemini 2.5 Flash | ✅ Gemini Vision | ❌ Custom impl. | Native multimodal, **limited .panda support** |

*DeepSeek provides clear error messaging for image processing attempts

**Note for .panda Documents**: OpenAI provider is recommended for optimal business document analysis. Google's safety filters may block complex business content, limiting analysis quality for consulting materials like Gantt charts and process flows.

#### Image Processing Implementation

**OpenAI & DeepSeek**: Uses MarkItDown with LLM client
```python
markitdown = MarkItDown(llm_client=self.client, llm_model=self.model)
result = markitdown.convert(image_path, llm_prompt=prompt)
```

**Google**: Direct Gemini Vision API
```python
import PIL.Image
image = PIL.Image.open(image_path)
response = self.model.generate_content([prompt, image])
```

#### Runtime Provider Management

- **Dynamic Switching**: Users can change providers during session
- **Availability Detection**: Automatic checking of API key presence
- **Graceful Fallback**: Clear error messages when providers unavailable
- **Status Monitoring**: Real-time provider status in UI

## Key Implementation Details

### File Upload Mechanism

The application implements four file upload methods:
1. **Drag and Drop**: Files can be dragged directly to the upload area
2. **Folder Drop**: Entire folders can be dragged to automatically include all contents recursively
3. **Manual Selection**: Clicking the upload area opens a file selection dialog
4. **Clipboard Paste**: Images can be pasted directly from clipboard using Ctrl+V/Cmd+V

All methods populate the same file input element and are seamlessly integrated with the multi-file preview system. The application implements a file accumulation system where new files are added to existing selections without clearing previous choices, with built-in duplicate prevention based on filename and file size.

**Folder Drop Implementation**: Uses the modern File System Access API with `webkitGetAsEntry()` to recursively read directory contents. When a folder is dropped, the system automatically extracts all files from subdirectories, preserving relative path information in filenames to maintain file organization context.

### File Type Detection

The application detects file types using:
1. MIME types from the File API
2. File extensions as a fallback

**Icon System**: The application features a dual-layer icon detection system:
- **Primary**: MIME type matching via `fileIcons` object
- **Fallback**: File extension matching via `extensionIcons` object
- **Default**: Falls back to `default.png` if no match found

Based on the detected type, appropriate icons are displayed:
- Word documents: word.png
- Excel spreadsheets: excel.png
- PowerPoint presentations: powerpoint.png (MIME + extension support)
- PDF files: pdf.png
- Email files (.eml): email.png
- Images: image.png
- .panda files: panda.png (extension-based, treated as archives)
- Other files: default.png

**Note**: `powerpoint.png` and `panda.png` icons need to be added to `/static/icons/` directory. See `/static/icons/README.md` for requirements.

### Conversion Processes

#### File Conversion
1. Files are uploaded to the server using a POST request to `/convert`
2. The server saves the uploaded file to a temporary location with a unique ID
3. For image files, the selected AI provider is used to generate descriptions:
   - **OpenAI**: Uses GPT-4V via MarkItDown integration
   - **Google**: Uses Gemini Vision API directly with Pillow for image loading
   - **DeepSeek**: Returns informative error (vision not supported yet)
4. For archive files (ZIP, .panda, etc.), the application:
   - **Configurable archive support**: Uses ARCHIVE_EXTENSIONS dictionary to define supported formats
   - Extracts all files to a temporary directory
   - **Hidden file filtering**: Automatically excludes hidden files and directories (starting with . or __)
   - Processes each extracted file individually using the MarkItDown library
   - Uses natural sorting algorithm to order files numerically (e.g., "Slide1" before "Slide2")
   - Combines all conversions into a single Markdown file with proper headings
   - Handles errors for individual files without failing the entire process
5. **For .eml email files**: Uses custom email parser built with Python's email module:
   - **Structured Header Extraction**: From, To, CC, BCC, Subject, Date, Message-ID, Reply-To
   - **Smart Body Processing**: Prioritizes plain text over HTML, with basic HTML-to-text conversion
   - **Attachment Detection**: Lists all email attachments with filenames
   - **Encoding Support**: Properly handles UTF-8 and other email encodings
   - **Fallback Support**: Uses MarkItDown if custom parser encounters errors
6. For regular files, the file is processed using the `MarkItDown` library
7. **Content Formatting**: AI image analysis results are formatted into professional callout boxes:
   - HTML comments (`<!-- -->`) → `> [!NOTE] **Image Analysis**` callouts
   - Text markers (`-- Start/End of Image Content`) → Formatted callout blocks
   - Applied during both file processing and download operations
8. The resulting Markdown is saved as a new file with unique identifier in filename
9. The temporary uploaded file is deleted after processing
10. The server returns the Markdown content and a download URL to the client

#### YouTube Transcription
1. YouTube URL is sent to the server using a POST request to `/convert-youtube`
2. The MarkItDown library extracts the transcript using YouTube's API
3. The application adds a header and source URL to the transcript
4. The resulting enhanced transcript is saved as a Markdown file with unique ID
5. The server returns the transcript content and a download URL to the client

#### YouTube Summarization
1. The YouTube URL and transcript are sent to `/summarize-youtube`
2. The server validates the OpenAI API key availability
3. The transcript is sent to OpenAI API with a structured prompt
4. The API generates a comprehensive summary and analysis
5. The application adds a header and source URL to the generated analysis
6. The resulting enhanced analysis is saved as a separate Markdown file with unique ID
7. The server returns the analysis content and a download URL to the client

### Intelligent .panda Document Processing

The application includes specialized processing for business consulting documents stored in .panda format:

#### Auto-Detection System
```javascript
const isPandaDocument = currentMarkdownContent && (
    currentMarkdownContent.includes('.panda') ||
    (currentMarkdownContent.includes('.md') && currentMarkdownContent.includes('.png'))
);
```

#### Specialized Business Prompt Template
When .panda documents or .md + .png combinations are detected, the system automatically loads a comprehensive prompt template designed for:

**Document Types Supported:**
- Gantt charts with timelines, dependencies, and resource allocation
- Process flow diagrams with decision points and workflows  
- Business tables with financial data and metrics
- Organizational charts with roles and reporting structures
- Project dashboards with KPIs and status indicators

**Comprehensive Analysis Features:**
- **Complete Text Transcription**: Extracts all visible text without summarization
- **Business Process Documentation**: Details every step, decision point, and workflow
- **Data Preservation**: Maintains exact numbers, dates, percentages, and metrics
- **Visual Element Description**: Explains arrows, connections, colors, and layouts
- **Professional Output**: Generates consulting-grade documentation with technical details

**Example Output Quality:**
- Gantt charts: Include all task names, timelines, critical paths, dependencies, resource assignments
- Process flows: Document each decision matrix, SLA commitments, exception handling procedures
- Financial tables: Transcribe complete data sets with growth metrics and regional breakdowns

#### User Experience
- **Intelligent Defaults**: Pre-populated prompt appears automatically for .panda files or .md + .png combinations
- **Full Customization**: Users can modify or replace the default prompt entirely  
- **Seamless Integration**: Works with existing restructure workflow and all AI providers
- **Professional Standards**: Ensures output meets consulting documentation requirements

### Error Handling

- **Frontend**:
  - Displays error messages returned from the server
  - Shows appropriate alerts for client-side validation
  - Disables buttons when operations are invalid
  - Provides visual feedback during long-running operations

- **Backend**:
  - Validates API keys before making external API calls
  - Catches exceptions during conversion and API interactions
  - Returns appropriate HTTP status codes and error messages
  - Handles missing files and invalid formats gracefully

## File Structure

```
markdown-project/
├── app.py                     # Main Flask application
├── ai_providers.py            # AI provider abstraction layer
├── prompt_library.json        # Centralized AI prompt storage
├── prompt_templates.json      # Legacy file-specific templates
├── requirements.txt           # Python dependencies:\n│                              #   - google-generativeai==0.8.3\n│                              #   - Pillow==11.1.0\n│                              #   - (existing: Flask, markitdown, openai, python-dotenv)
├── .env                       # Environment variables (multiple API keys) - not in git
├── .gitignore                 # Git ignore configuration
├── README.md                  # Project documentation
├── technical.md               # Technical documentation
├── static/
│   ├── icons/                 # File type icons
│   │   ├── default.png        # Default file icon
│   │   ├── excel.png          # Excel file icon
│   │   ├── image.png          # Image file icon
│   │   ├── pdf.png            # PDF file icon
│   │   └── word.png           # Word file icon
│   ├── script.js              # Frontend JavaScript (enhanced)
│   └── styles.css             # CSS styles (enhanced)
├── templates/
│   └── index.html             # Main HTML template (enhanced)
```

## Security Considerations

- The application uses Flask's built-in security features for file uploads
- API keys are stored in a .env file and not committed to version control
- All files are processed in temporary locations before being removed
- All generated Markdown files have unique identifiers in their filenames
- Original input files are never stored permanently in the uploads directory
- UUID is used to prevent filename collisions for all generated files
- No authentication is implemented, making it suitable only for personal or internal use
- Error messages from exceptions are directly exposed to the client

## Performance Optimization

The application is designed for simplicity rather than high-volume processing:
- Files are processed synchronously, blocking the server during conversion
- Loading indicators and disabled controls provide user feedback during long operations
- Button states are managed to prevent multiple concurrent operations
- AI processing calls are made asynchronously with appropriate UX handling
- No caching mechanism is implemented for converted files
- Server resources are freed once the conversion is complete

## Potential Improvements

1. **Security Enhancements**:
   - Implement file type validation
   - Use secure random filenames for all uploads
   - Add rate limiting for conversion and API requests
   - Implement sanitization for transcript content

2. **Performance Optimizations**:
   - Add background processing for large files and API calls
   - Implement caching for converted documents
   - Add progress indicators with percentage completion for long-running conversions
   - Optimize OpenAI prompts for faster responses

3. **Feature Additions**:
   - ✅ **Configurable Archive Support**: ZIP, .panda and extensible support for additional archive formats
   - ✅ **Hidden File Filtering**: Automatic exclusion of hidden files and system files from archives
   - ✅ Natural sorting algorithm for numerical filenames
   - ✅ **Clipboard Image Paste Support**: Direct image paste from clipboard with automatic naming
   - ✅ **File Accumulation System**: Progressive file selection without auto-clearing, duplicate prevention
   - ✅ **Custom AI Restructuring**: User-defined prompts for content restructuring with modal interface
   - ✅ **Intelligent .panda Business Document Analysis**: Auto-detection and specialized processing for consulting materials (.panda files or .md + .png combinations) with comprehensive default prompts for Gantt charts, process flows, and business diagrams
   - ✅ **Folder Drop Support**: Drag and drop entire folders to process all contents recursively
   - Support for additional archive formats (RAR, 7z, etc.)
   - Configurable AI summarization options (brief vs detailed, focus areas)
   - Multiple language support for transcripts and summaries
   - Customization options for Markdown output
   - Account-based file storage
   - Preview of original documents
   - Custom prompt templates for different summarization styles
   - Configurable sorting options for ZIP file contents

4. **AI Enhancements**:
   - ✅ **Multi-Provider Support**: OpenAI, DeepSeek, Google Gemini
   - ✅ **Runtime Provider Switching**: Dynamic AI provider selection
   - ✅ **Provider-Specific Optimizations**: Tailored processing for each AI service
   - Add sentiment analysis for YouTube videos
   - Implement topic extraction and categorization
   - Create visualization options for transcript analysis
   - Advanced model selection for different use cases
   - **Additional Provider Support**: Claude, Llama, etc.

5. **Code Structure**:
   - ✅ **Modular AI Provider System**: Abstract factory pattern implementation
   - ✅ **API Service Classes**: Dedicated provider classes for external services
   - ✅ **Enhanced Error Handling**: Provider-specific error management
   - Implement logging
   - Add unit and integration tests
   - Create environment-specific configuration files
   - **Provider Plugin System**: Easy addition of new AI providers
