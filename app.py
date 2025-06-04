from flask import Flask, request, render_template, jsonify, send_file
from markitdown import MarkItDown
import os
import uuid
import mimetypes
import json
import zipfile
import tempfile
import shutil
import email
from email.policy import default
from pathlib import Path
from dotenv import load_dotenv
from ai_providers import AIProviderFactory
import re

# .env dosyasından çevre değişkenlerini yükle
load_dotenv()

def clean_markdown_content(content):
    """
    Clean markdown content by removing code blocks and replacing HTML comments
    """
    if not content:
        return content
    
    # Remove markdown code blocks at start and end (various formats)
    cleaned = re.sub(r'^```markdown\s*\n', '', content)
    cleaned = re.sub(r'^```\s*\n', '', cleaned)  # Just ``` without language
    cleaned = re.sub(r'\n\s*```\s*$', '', cleaned)  # Allow whitespace before closing
    
    # Replace HTML comments with callout format
    cleaned = re.sub(r'<!--\s*', '\n> [!NOTE] **Image Analysis**\n> ', cleaned)
    cleaned = re.sub(r'\s*-->', '\n', cleaned)
    
    # Replace Start/End of Image Content markers with callout format
    # This regex captures everything between Start and End markers and formats as callout
    def format_image_content(match):
        content = match.group(1).strip()
        # Split content into lines and prefix each with "> "
        lines = content.split('\n')
        formatted_lines = []
        for line in lines:
            if line.strip():  # Only non-empty lines
                formatted_lines.append(f"> {line}")
            else:
                formatted_lines.append(">")
        return f"\n> [!NOTE] **Image Analysis**\n" + '\n'.join(formatted_lines) + "\n"
    
    cleaned = re.sub(r'-- Start of Image Content\s*\n(.*?)\n-- End of Image Content', 
                     format_image_content, cleaned, flags=re.DOTALL)
    
    return cleaned

def split_markdown_by_files(content):
    """
    Split markdown content by ## File X: filename patterns or H1 headers and return separate files
    Returns a list of tuples: (original_filename, content)
    """
    if not content:
        return []
    
    # Method 1: Try to split by "## File X:" patterns (original method)
    file_pattern = r'## File \d+: (.+?)(?=\n|\r\n)'
    file_matches = list(re.finditer(file_pattern, content))
    
    if len(file_matches) >= 2:
        # Use original logic for ## File X: patterns
        sections = re.split(r'## File \d+: [^\n\r]+', content)
        filenames = [match.group(1).strip() for match in file_matches]
        
        # Skip the first section (usually contains header content before first file)
        if len(sections) > 1:
            sections = sections[1:]
        
        result = []
        for i, section in enumerate(sections):
            if i < len(filenames):
                filename = filenames[i]
                section_content = section.strip()
                section_content = re.sub(r'\n---\n*$', '', section_content)
                section_content = section_content.strip()
                
                if section_content:
                    base_filename = os.path.splitext(filename)[0]
                    final_content = f"# {base_filename}\n\n{section_content}"
                    result.append((filename, final_content))
        
        return result
    
    # Method 2: Try to split by H1 headers (# Title)
    h1_pattern = r'^# (.+)$'
    h1_matches = list(re.finditer(h1_pattern, content, re.MULTILINE))
    
    if len(h1_matches) >= 2:
        result = []
        
        for i, match in enumerate(h1_matches):
            title = match.group(1).strip()
            start_pos = match.start()
            
            # Find the end position (start of next H1 or end of content)
            if i + 1 < len(h1_matches):
                end_pos = h1_matches[i + 1].start()
                section_content = content[start_pos:end_pos].strip()
            else:
                section_content = content[start_pos:].strip()
            
            if section_content:
                # Generate filename from title
                safe_title = re.sub(r'[^\w\s-]', '', title)  # Remove special chars
                safe_title = re.sub(r'\s+', '_', safe_title.strip())  # Replace spaces with underscores
                filename = f"{safe_title}.md"
                
                result.append((filename, section_content))
        
        return result
    
    # If neither method finds multiple sections, return empty
    return []

def load_prompt_library():
    """
    Load complete prompt library from JSON file
    """
    try:
        with open('prompt_library.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Warning: prompt_library.json not found. Using default prompts.")
        return {}
    except Exception as e:
        print(f"Error loading prompt library: {e}")
        return {}

def save_prompt_library(library):
    """
    Save prompt library to JSON file
    """
    try:
        with open('prompt_library.json', 'w', encoding='utf-8') as f:
            json.dump(library, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving prompt library: {e}")
        return False

def get_prompt(prompt_key, variables=None):
    """
    Get a prompt from the library and replace variables if provided
    """
    library = load_prompt_library()
    prompt_data = library.get(prompt_key, {})
    prompt = prompt_data.get('prompt', '')
    
    if variables:
        for key, value in variables.items():
            prompt = prompt.replace(f'{{{key}}}', str(value))
    
    return prompt

def load_prompt_templates():
    """
    Load prompt templates from JSON file (legacy support)
    """
    # First try to load from prompt_library.json
    library = load_prompt_library()
    templates = {}
    
    # Convert file templates from library
    for key, data in library.items():
        if data.get('category') == 'file_templates':
            # Map the prompts to file extensions
            if key == 'panda_document':
                templates['.panda'] = data['prompt']
            elif key == 'excel_extract':
                templates['.xlsx'] = data['prompt']
            elif key == 'pdf_extract':
                templates['.pdf'] = data['prompt']
            elif key == 'docx_convert':
                templates['.docx'] = data['prompt']
            elif key == 'eml_extract':
                templates['.eml'] = data['prompt']
    
    # If no templates found in library, try legacy file
    if not templates:
        try:
            with open('prompt_templates.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
            print(f"Error loading prompt_templates.json: {e}")
    
    return templates

def get_template_for_extension(filename):
    """
    Get appropriate prompt template based on file extension
    """
    templates = load_prompt_templates()
    file_extension = os.path.splitext(filename.lower())[1]
    return templates.get(file_extension, None)

def convert_eml_to_markdown(eml_path):
    """
    Convert .eml file to structured markdown using Python's email module
    """
    try:
        # Parse the email file
        with open(eml_path, 'rb') as f:
            msg = email.message_from_binary_file(f, policy=default)
        
        # Build markdown content
        markdown_content = "# Email Message\n\n"
        
        # Email headers
        markdown_content += "## Headers\n\n"
        
        # Essential headers
        headers = [
            ('From', 'From'),
            ('To', 'To'),
            ('CC', 'CC'),
            ('BCC', 'BCC'),
            ('Subject', 'Subject'),
            ('Date', 'Date'),
            ('Message-ID', 'Message ID'),
            ('Reply-To', 'Reply-To')
        ]
        
        for header_key, header_display in headers:
            header_value = msg.get(header_key)
            if header_value:
                # Handle encoded headers
                if header_key in ['From', 'To', 'CC', 'BCC', 'Reply-To']:
                    # These might have encoded names
                    markdown_content += f"**{header_display}:** {header_value}\n\n"
                else:
                    markdown_content += f"**{header_display}:** {header_value}\n\n"
        
        # Email body
        markdown_content += "---\n\n## Message Body\n\n"
        
        # Extract body content
        body_content = ""
        
        if msg.is_multipart():
            # Handle multipart messages
            for part in msg.walk():
                content_type = part.get_content_type()
                
                # Prioritize plain text
                if content_type == 'text/plain':
                    body_content = part.get_content()
                    break
                elif content_type == 'text/html' and not body_content:
                    # Use HTML if no plain text found (we could improve this by converting HTML to markdown)
                    html_content = part.get_content()
                    # Simple HTML tag removal for basic conversion
                    body_content = re.sub(r'<[^>]+>', '', html_content)
                    body_content = body_content.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        else:
            # Simple message
            body_content = msg.get_content()
        
        if body_content:
            # Clean and format body content
            body_content = body_content.strip()
            markdown_content += body_content
        else:
            markdown_content += "*No readable content found in email body.*"
        
        # Attachments info
        attachments = []
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_disposition() == 'attachment':
                    filename = part.get_filename()
                    if filename:
                        attachments.append(filename)
        
        if attachments:
            markdown_content += "\n\n---\n\n## Attachments\n\n"
            for attachment in attachments:
                markdown_content += f"- {attachment}\n"
        
        # Create a result object similar to MarkItDown's output
        class EmailResult:
            def __init__(self, text):
                self.text_content = text
        
        return EmailResult(markdown_content)
        
    except Exception as e:
        # Fallback to MarkItDown if our custom parser fails
        markitdown = MarkItDown()
        return markitdown.convert(eml_path)

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Archive extensions that should be extracted like ZIP files
ARCHIVE_EXTENSIONS = {
    '.zip': 'zip',
    '.panda': 'zip',  # .panda files are treated as ZIP archives
    # Add more extensions here as needed
    # '.rar': 'rar',
    # '.7z': '7z',
}

def is_archive_file(filename):
    """
    Check if a file is an archive that should be extracted
    """
    file_extension = os.path.splitext(filename.lower())[1]
    return file_extension in ARCHIVE_EXTENSIONS

def get_archive_type(filename):
    """
    Get the archive type for a given filename
    """
    file_extension = os.path.splitext(filename.lower())[1]
    return ARCHIVE_EXTENSIONS.get(file_extension, 'unknown')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ai-providers', methods=['GET'])
def get_ai_providers():
    """Get available AI providers and their status"""
    try:
        providers = AIProviderFactory.get_available_providers()
        current_provider = os.getenv('AI_PROVIDER', 'openai').lower()
        
        return jsonify({
            "providers": providers,
            "current": current_provider
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/prompt-library', methods=['GET'])
def get_prompt_library():
    """Get the complete prompt library"""
    try:
        library = load_prompt_library()
        return jsonify({"prompts": library})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/prompt-library', methods=['POST'])
def update_prompt_library():
    """Update a specific prompt in the library"""
    data = request.json
    if not data or 'key' not in data or 'prompt' not in data:
        return jsonify({"error": "Prompt key and content are required!"}), 400
    
    try:
        library = load_prompt_library()
        
        # Update the prompt if it exists
        if data['key'] in library:
            library[data['key']]['prompt'] = data['prompt']
            if save_prompt_library(library):
                return jsonify({"message": "Prompt updated successfully", "prompt": library[data['key']]})
            else:
                return jsonify({"error": "Failed to save prompt library"}), 500
        else:
            return jsonify({"error": f"Prompt key '{data['key']}' not found"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/prompt-templates', methods=['GET'])
def get_prompt_templates():
    """Get available prompt templates (legacy endpoint)"""
    try:
        templates = load_prompt_templates()
        return jsonify({"templates": templates})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ai-providers', methods=['POST'])
def set_ai_provider():
    """Set the AI provider to use"""
    data = request.json
    if not data or 'provider' not in data:
        return jsonify({"error": "Provider name is required!"}), 400
    
    provider_name = data['provider'].lower()
    
    try:
        # Test if the provider is available
        ai_provider = AIProviderFactory.get_provider(provider_name)
        if not ai_provider.is_available():
            return jsonify({"error": f"Provider '{provider_name}' is not properly configured. Please check your API keys."}), 400
        
        # Set environment variable for this session
        os.environ['AI_PROVIDER'] = provider_name
        
        return jsonify({
            "message": f"AI provider set to '{provider_name}'",
            "provider": provider_name
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/convert', methods=['POST'])
def convert_file():
    if 'files' not in request.files:
        return jsonify({"error": "No files uploaded!"}), 400

    files = request.files.getlist('files')
    if not files or all(f.filename == '' for f in files):
        return jsonify({"error": "No files selected!"}), 400

    # Process multiple files
    if len(files) == 1:
        # Single file processing (existing logic)
        file = files[0]
        # Geçici bir dosya yolu oluştur
        temp_id = str(uuid.uuid4())
        
        # Dosya adında klasör yapısı varsa oluştur
        if '/' in file.filename:
            # Klasör yapısını korumak için güvenli bir yol oluştur
            safe_filename = file.filename.replace('/', '_')
            temp_filepath = os.path.join(UPLOAD_FOLDER, f"temp_{temp_id}_{safe_filename}")
        else:
            temp_filepath = os.path.join(UPLOAD_FOLDER, f"temp_{temp_id}_{file.filename}")
        
        file.save(temp_filepath)

        try:
            # Dosya türünü kontrol et
            mime_type, _ = mimetypes.guess_type(temp_filepath)
            is_image = mime_type and mime_type.startswith('image/')
            is_eml = file.filename.lower().endswith('.eml') or mime_type == 'message/rfc822'
            
            # EML dosyası ise özel parser kullan
            if is_eml:
                result = convert_eml_to_markdown(temp_filepath)
            # Archive dosyası ise içeriğini işle
            elif is_archive_file(file.filename):
                archive_type = get_archive_type(file.filename)
                if archive_type == 'zip':
                    return process_zip_file(temp_filepath, file.filename)
                # Gelecekte diğer archive türleri için buraya eklenebilir
            # Görüntü dosyası ise AI ile işle
            elif is_image:
                # AI provider'ın ayarlanıp ayarlanmadığını kontrol et
                try:
                    ai_provider = AIProviderFactory.get_provider()
                    if not ai_provider.is_available():
                        return jsonify({"error": "AI provider is not configured. Please set API keys in the .env file."}), 400

                    # Image analysis prompt for professional presentation visuals
                    custom_prompt = get_prompt('image_analysis')
                    
                    # AI provider'ın process_image metodunu kullan
                    result_text = ai_provider.process_image(temp_filepath, custom_prompt)
                    
                    # MarkItDown result format'ına uygun olarak sarmalama
                    class ImageResult:
                        def __init__(self, text):
                            self.text_content = text
                    
                    result = ImageResult(result_text)
                    
                except Exception as e:
                    return jsonify({"error": f"AI provider error: {str(e)}. Please check your API key."}), 400
            else:
                markitdown = MarkItDown()
                result = markitdown.convert(temp_filepath)

            # Dosya adı için benzersiz bir ID oluştur
            unique_id = str(uuid.uuid4())
            output_filename = f"{os.path.splitext(file.filename)[0]}_{unique_id}.md"
            output_filepath = os.path.join(UPLOAD_FOLDER, output_filename)

            # Markdown içeriğini temizle ve kaydet
            cleaned_content = clean_markdown_content(result.text_content)
            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)

            # Geçici dosyayı temizle
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)

            # Markdown içeriğini JSON olarak döndür
            return jsonify({
                "markdown": result.text_content,
                "download_url": f"/download/{output_filename}"
            })

        except Exception as e:
            # Hata durumunda geçici dosyayı temizle
            if 'temp_filepath' in locals() and os.path.exists(temp_filepath):
                os.remove(temp_filepath)
            return jsonify({"error": str(e)}), 500
    
    else:
        # Multiple files processing
        return process_multiple_files(files)

def process_zip_file(zip_filepath, original_filename):
    """
    ZIP dosyasının içindeki tüm dosyaları ayıklayıp her birini Markdown'a dönüştüren fonksiyon
    """
    # Sonuç içeriğini tutacak olan string
    markdown_content = f"# {original_filename} içindeki dosyalar\n\n"

    # ZIP dosyasını geçici bir dizine çıkar
    with tempfile.TemporaryDirectory() as temp_dir:
        # ZIP dosyasını açıp içeriğini geçici dizine çıkar
        with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        # ZIP dosyasını artık silebiliriz
        if os.path.exists(zip_filepath):
            os.remove(zip_filepath)

        # Çıkarılan dosyaları işle (gizli dosyaları hariç tut)
        extracted_files = []
        for root, _, files in os.walk(temp_dir):
            for filename in files:
                # Gizli dosyaları (. ile başlayanları) ve sistem dosyalarını atla
                if filename.startswith('.') or filename.startswith('__'):
                    continue
                
                file_path = os.path.join(root, filename)
                relative_path = os.path.relpath(file_path, temp_dir)
                
                # Relative path'te gizli klasör var mı kontrol et
                path_parts = relative_path.split(os.sep)
                if any(part.startswith('.') or part.startswith('__') for part in path_parts):
                    continue
                    
                extracted_files.append((file_path, relative_path))

        # Dosyaları doğal sıralamaya göre sırala (numaralandırılmış dosyalar için)
        def natural_sort_key(s):
            # Sıralama anahtarı oluştur: "abc123def456" -> ["abc", 123, "def", 456]
            # Bu, dosya adlarındaki sayıları sayısal olarak sıralamaya olanak tanır
            return [int(text) if text.isdigit() else text.lower()
                   for text in re.split(r'(\d+)', s[1])]

        # Dosyaları doğal sıralama ile sırala
        extracted_files.sort(key=natural_sort_key)

        # Her çıkarılan dosyayı Markdown'a dönüştür
        for file_path, relative_path in extracted_files:
            try:
                # Dosya türünü kontrol et
                mime_type, _ = mimetypes.guess_type(file_path)
                is_image = mime_type and mime_type.startswith('image/')
                is_eml = relative_path.lower().endswith('.eml') or mime_type == 'message/rfc822'

                # EML dosyası ise özel parser kullan
                if is_eml:
                    result = convert_eml_to_markdown(file_path)
                # Görüntü dosyası ise AI ile işle
                elif is_image:
                    # AI provider'ın varlığını kontrol et
                    try:
                        ai_provider = AIProviderFactory.get_provider()
                        if not ai_provider.is_available():
                            markdown_content += f"\n## {relative_path}\n\n*Bu bir görüntü dosyasıdır ve dönüştürmek için AI provider ayarlanmış olmalıdır.*\n\n"
                            continue
                            
                        # Image analysis prompt for professional presentation visuals
                        custom_prompt = get_prompt('image_analysis')
                        
                        # Google provider için direkt process_image kullan, diğerleri için MarkItDown
                        client = ai_provider.get_client_for_markitdown()
                        if client is not None:
                            # OpenAI/DeepSeek - MarkItDown kullan
                            markitdown = MarkItDown(llm_client=client, llm_model=ai_provider.get_model_name())
                            result = markitdown.convert(file_path, llm_prompt=custom_prompt)
                        else:
                            # Google - direkt process_image kullan
                            result_text = ai_provider.process_image(file_path, custom_prompt)
                            # MarkItDown result format'ına uygun olarak sarmalama
                            class ImageResult:
                                def __init__(self, text):
                                    self.text_content = text
                            result = ImageResult(result_text)
                            
                    except Exception:
                        markdown_content += f"\n## {relative_path}\n\n*Bu bir görüntü dosyasıdır ve dönüştürmek için AI provider ayarlanmış olmalıdır.*\n\n"
                        continue
                else:
                    # Normal dosya - MarkItDown ile işle
                    markitdown = MarkItDown()
                    result = markitdown.convert(file_path)

                # Dönüştürülmüş içeriği sonuç dosyasına ekle
                markdown_content += f"\n## {relative_path}\n\n{result.text_content}\n\n---\n\n"

            except Exception as e:
                # Dönüştürme hatası durumunda hatayı içeriğe ekle
                markdown_content += f"\n## {relative_path}\n\n*Dönüştürme hatası: {str(e)}*\n\n---\n\n"

    # Tüm içerik için benzersiz bir ID oluştur
    unique_id = str(uuid.uuid4())
    output_filename = f"{os.path.splitext(original_filename)[0]}_zip_{unique_id}.md"
    output_filepath = os.path.join(UPLOAD_FOLDER, output_filename)

    # Markdown içeriğini temizle ve kaydet
    cleaned_content = clean_markdown_content(markdown_content)
    with open(output_filepath, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)

    # Markdown içeriğini JSON olarak döndür
    return jsonify({
        "markdown": markdown_content,
        "download_url": f"/download/{output_filename}"
    })

def process_multiple_files(files):
    """
    Process multiple files and combine them into a single Markdown file
    """
    markdown_content = "# Converted Files\n\n"
    temp_files = []
    
    try:
        # Process each file
        for i, file in enumerate(files, 1):
            if file.filename == '':
                continue
                
            # Create temporary file path
            temp_id = str(uuid.uuid4())
            
            # Dosya adında klasör yapısı varsa güvenli hale getir
            if '/' in file.filename:
                safe_filename = file.filename.replace('/', '_')
                temp_filepath = os.path.join(UPLOAD_FOLDER, f"temp_{temp_id}_{safe_filename}")
            else:
                temp_filepath = os.path.join(UPLOAD_FOLDER, f"temp_{temp_id}_{file.filename}")
            
            file.save(temp_filepath)
            temp_files.append(temp_filepath)
            
            try:
                # Check file type
                mime_type, _ = mimetypes.guess_type(temp_filepath)
                is_image = mime_type and mime_type.startswith('image/')
                is_eml = file.filename.lower().endswith('.eml') or mime_type == 'message/rfc822'
                
                # Handle EML files with custom parser
                if is_eml:
                    result = convert_eml_to_markdown(temp_filepath)
                # Handle archive files
                elif is_archive_file(file.filename):
                    archive_type = get_archive_type(file.filename)
                    if archive_type == 'zip':
                        # Extract and process ZIP contents
                        zip_result = process_zip_file(temp_filepath, file.filename)
                        zip_data = json.loads(zip_result.get_data(as_text=True))
                        markdown_content += f"\n## File {i}: {file.filename}\n\n{zip_data['markdown']}\n\n---\n\n"
                        continue
                # Handle images with AI
                elif is_image:
                    try:
                        ai_provider = AIProviderFactory.get_provider()
                        if not ai_provider.is_available():
                            markdown_content += f"\n## File {i}: {file.filename}\n\n*This is an image file and requires AI provider configuration for conversion.*\n\n---\n\n"
                            continue
                            
                        custom_prompt = get_prompt('image_analysis')
                        
                        # AI provider'ın process_image metodunu kullan (single file ile aynı)
                        result_text = ai_provider.process_image(temp_filepath, custom_prompt)
                        
                        # MarkItDown result format'ına uygun olarak sarmalama
                        class ImageResult:
                            def __init__(self, text):
                                self.text_content = text
                        
                        result = ImageResult(result_text)
                        
                    except Exception as e:
                        markdown_content += f"\n## File {i}: {file.filename}\n\n*AI processing error: {str(e)}*\n\n---\n\n"
                        continue
                else:
                    markitdown = MarkItDown()
                    result = markitdown.convert(temp_filepath)
                
                # Add to combined markdown
                markdown_content += f"\n## File {i}: {file.filename}\n\n{result.text_content}\n\n---\n\n"
                
            except Exception as e:
                markdown_content += f"\n## File {i}: {file.filename}\n\n*Conversion error: {str(e)}*\n\n---\n\n"
        
        # Save combined markdown
        unique_id = str(uuid.uuid4())
        output_filename = f"multiple_files_{unique_id}.md"
        output_filepath = os.path.join(UPLOAD_FOLDER, output_filename)
        
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(clean_markdown_content(markdown_content))
        
        return jsonify({
            "markdown": markdown_content,
            "download_url": f"/download/{output_filename}"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up temporary files
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)

@app.route('/convert-youtube', methods=['POST'])
def convert_youtube():
    data = request.json
    if not data or 'url' not in data:
        return jsonify({"error": "No YouTube URL provided!"}), 400

    youtube_url = data['url']
    if not youtube_url:
        return jsonify({"error": "YouTube URL is empty!"}), 400

    try:
        # Create a unique filename for the YouTube transcript
        unique_id = str(uuid.uuid4())
        output_filename = f"youtube_{unique_id}.md"
        output_filepath = os.path.join(UPLOAD_FOLDER, output_filename)

        # Use MarkItDown to convert YouTube URL to markdown
        markitdown = MarkItDown()
        result = markitdown.convert(youtube_url)

        # Transcript'e YouTube URL'ini ekle
        enhanced_content = f"# Transcript from YouTube\n\n**Source:** {youtube_url}\n\n---\n\n{result.text_content}"

        # Save the enhanced markdown result
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(clean_markdown_content(enhanced_content))

        return jsonify({
            "markdown": enhanced_content,
            "download_url": f"/download/{output_filename}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/summarize-youtube', methods=['POST'])
def summarize_youtube():
    data = request.json
    if not data or 'url' not in data or 'transcript' not in data:
        return jsonify({"error": "YouTube URL and transcript are required!"}), 400

    youtube_url = data['url']
    transcript = data['transcript']

    if not youtube_url or not transcript:
        return jsonify({"error": "YouTube URL or transcript is empty!"}), 400

    try:
        # AI provider'ın ayarlanıp ayarlanmadığını kontrol et
        ai_provider = AIProviderFactory.get_provider()
        if not ai_provider.is_available():
            return jsonify({"error": "AI provider is not configured. Please set API keys in the .env file."}), 400

        # Get prompt from library and replace variables
        prompt = get_prompt('youtube_single_summary', {
            'youtube_url': youtube_url,
            'transcript': transcript
        })

        # AI API çağrısı
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        summary = ai_provider.chat_completion(messages, max_tokens=1500)

        # URL ekleme
        enhanced_summary = f"# AI Summary of YouTube Video\n\n**Source:** {youtube_url}\n\n---\n\n{summary}"

        # Özeti bir dosyaya kaydet
        unique_id = str(uuid.uuid4())
        output_filename = f"youtube_summary_{unique_id}.md"
        output_filepath = os.path.join(UPLOAD_FOLDER, output_filename)

        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(clean_markdown_content(enhanced_summary))

        return jsonify({
            "markdown": enhanced_summary,
            "download_url": f"/download/{output_filename}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/convert-youtube-multiple', methods=['POST'])
def convert_youtube_multiple():
    data = request.json
    if not data or 'urls' not in data:
        return jsonify({"error": "No YouTube URLs provided!"}), 400

    urls = data['urls']
    if not urls or not isinstance(urls, list):
        return jsonify({"error": "URLs must be a list!"}), 400

    markdown_content = "# YouTube Video Transcripts\n\n"
    transcripts = []
    
    try:
        # Process each YouTube URL
        for i, url in enumerate(urls, 1):
            if not url:
                continue
            
            try:
                # Use MarkItDown to convert YouTube URL to markdown
                markitdown = MarkItDown()
                result = markitdown.convert(url)
                
                # Add to transcripts list
                transcript_data = {
                    "url": url,
                    "content": result.text_content
                }
                transcripts.append(transcript_data)
                
                # Add to combined markdown
                markdown_content += f"## Video {i}: {url}\n\n{result.text_content}\n\n---\n\n"
                
            except Exception as e:
                markdown_content += f"## Video {i}: {url}\n\n*Error converting video: {str(e)}*\n\n---\n\n"
        
        # Save combined transcripts
        unique_id = str(uuid.uuid4())
        output_filename = f"youtube_multiple_{unique_id}.md"
        output_filepath = os.path.join(UPLOAD_FOLDER, output_filename)
        
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(clean_markdown_content(markdown_content))
        
        return jsonify({
            "markdown": markdown_content,
            "download_url": f"/download/{output_filename}",
            "transcripts": transcripts
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/summarize-youtube-multiple', methods=['POST'])
def summarize_youtube_multiple():
    data = request.json
    if not data or 'transcripts' not in data:
        return jsonify({"error": "No transcripts provided!"}), 400

    transcripts = data['transcripts']
    if not transcripts or not isinstance(transcripts, list):
        return jsonify({"error": "Transcripts must be a list!"}), 400

    try:
        # Check AI provider
        ai_provider = AIProviderFactory.get_provider()
        if not ai_provider.is_available():
            return jsonify({"error": "AI provider is not configured. Please set API keys in the .env file."}), 400

        # Prepare videos content
        videos_content = ""
        for i, transcript in enumerate(transcripts, 1):
            videos_content += f"Video {i} ({transcript['url']}):\n{transcript['content']}\n\n"
        
        # Get prompt from library and replace variables
        prompt = get_prompt('youtube_multiple_summary', {
            'videos_content': videos_content
        })

        # AI API call
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        summary = ai_provider.chat_completion(messages, max_tokens=2000)
        
        # Add URLs to summary
        enhanced_summary = "# AI Summary of Multiple YouTube Videos\n\n**Sources:**\n"
        for i, transcript in enumerate(transcripts, 1):
            enhanced_summary += f"- Video {i}: {transcript['url']}\n"
        enhanced_summary += f"\n---\n\n{summary}"

        # Save summary
        unique_id = str(uuid.uuid4())
        output_filename = f"youtube_summary_multiple_{unique_id}.md"
        output_filepath = os.path.join(UPLOAD_FOLDER, output_filename)

        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(clean_markdown_content(enhanced_summary))

        return jsonify({
            "markdown": enhanced_summary,
            "download_url": f"/download/{output_filename}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/restructure', methods=['POST'])
def restructure_content():
    """
    Restructure existing content using custom user prompt
    """
    data = request.json
    if not data or 'content' not in data or 'prompt' not in data:
        return jsonify({"error": "Content and custom prompt are required!"}), 400

    content = data['content']
    custom_prompt = data['prompt']

    if not content or not custom_prompt:
        return jsonify({"error": "Content or prompt is empty!"}), 400

    try:
        # AI provider'ın ayarlanıp ayarlanmadığını kontrol et
        ai_provider = AIProviderFactory.get_provider()
        if not ai_provider.is_available():
            return jsonify({"error": "AI provider is not configured. Please set API keys in the .env file."}), 400

        # Detect document type and use appropriate prompt
        is_panda_document = ('.panda' in content or 
                           (('.md' in content or 'markdown' in content) and 
                            ('.png' in content or '.PNG' in content)))
        
        is_excel_document = '.xlsx' in content or '.xls' in content
        is_pdf_document = '.pdf' in content
        is_docx_document = '.docx' in content or '.doc' in content
        is_eml_document = '.eml' in content
        
        if is_panda_document:
            # Use panda document prompt for business documents
            prompt = get_prompt('panda_document', {
                'custom_prompt': custom_prompt,
                'content': content
            })
        elif is_excel_document:
            # Use Excel-specific prompt
            prompt = get_prompt('excel_extract', {
                'custom_prompt': custom_prompt,
                'content': content
            })
        elif is_pdf_document:
            # Use PDF-specific prompt
            prompt = get_prompt('pdf_extract', {
                'custom_prompt': custom_prompt,
                'content': content
            })
        elif is_docx_document:
            # Use Word-specific prompt
            prompt = get_prompt('docx_convert', {
                'custom_prompt': custom_prompt,
                'content': content
            })
        elif is_eml_document:
            # Use EML-specific prompt
            prompt = get_prompt('eml_extract', {
                'custom_prompt': custom_prompt,
                'content': content
            })
        else:
            # Use general content restructure prompt
            prompt = get_prompt('content_restructure', {
                'custom_prompt': custom_prompt,
                'content': content
            })

        # AI API çağrısı
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        restructured_content = ai_provider.chat_completion(messages, max_tokens=2000)

        # Use only the AI-generated content without showing the user prompt
        enhanced_content = restructured_content

        # Save restructured content
        unique_id = str(uuid.uuid4())
        output_filename = f"restructured_{unique_id}.md"
        output_filepath = os.path.join(UPLOAD_FOLDER, output_filename)

        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(clean_markdown_content(enhanced_content))

        return jsonify({
            "markdown": enhanced_content,
            "download_url": f"/download/{output_filename}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download-custom', methods=['POST'])
def download_custom():
    data = request.json
    if not data or 'content' not in data or 'filename' not in data:
        return jsonify({"error": "Content and filename are required!"}), 400

    content = data['content']
    filename = data['filename']

    if not content or not filename:
        return jsonify({"error": "Content or filename is empty!"}), 400

    try:
        # Clean filename
        filename = re.sub(r'[^\w\-_.]', '_', filename)
        if not filename.endswith('.md'):
            filename += '.md'

        # Create temporary file
        temp_filepath = os.path.join(UPLOAD_FOLDER, f"custom_{uuid.uuid4()}_{filename}")
        
        with open(temp_filepath, 'w', encoding='utf-8') as f:
            f.write(clean_markdown_content(content))

        # Return file as download
        response = send_file(temp_filepath, as_attachment=True, download_name=filename)
        
        # Clean up the temporary file after sending
        def remove_file():
            try:
                if os.path.exists(temp_filepath):
                    os.remove(temp_filepath)
            except Exception:
                pass
        
        response.call_on_close(remove_file)
        
        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download-separate', methods=['POST'])
def download_separate_files():
    """
    Download content as separate files in a ZIP archive
    Only works for content that has multiple file sections (## File X: filename patterns)
    """
    data = request.json
    if not data or 'content' not in data:
        return jsonify({"error": "Content is required!"}), 400

    content = data['content']
    if not content:
        return jsonify({"error": "Content is empty!"}), 400

    try:
        # Split content by file sections
        file_sections = split_markdown_by_files(content)
        
        if len(file_sections) < 2:
            return jsonify({"error": "Content must contain multiple file sections (## File X: filename) to download separately. Use regular download for single files."}), 400

        # Create a temporary directory for the files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create individual markdown files
            for original_filename, file_content in file_sections:
                # Clean filename for safe filesystem use
                safe_filename = re.sub(r'[^\w\-_.]', '_', original_filename)
                
                # Ensure .md extension
                if not safe_filename.lower().endswith('.md'):
                    base_name = os.path.splitext(safe_filename)[0]
                    safe_filename = f"{base_name}.md"
                
                # Write individual file
                file_path = os.path.join(temp_dir, safe_filename)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(clean_markdown_content(file_content))
            
            # Create ZIP file
            zip_filename = f"separate_files_{uuid.uuid4()}.zip"
            zip_filepath = os.path.join(UPLOAD_FOLDER, zip_filename)
            
            with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add all markdown files to the ZIP
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Add file to ZIP with relative path
                        arcname = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, arcname)

        # Return the ZIP file
        response = send_file(zip_filepath, as_attachment=True, download_name=f"separate_markdown_files_{uuid.uuid4().hex[:8]}.zip")
        
        # Clean up the ZIP file after sending
        def remove_file():
            try:
                if os.path.exists(zip_filepath):
                    os.remove(zip_filepath)
            except Exception:
                pass
        
        response.call_on_close(remove_file)
        
        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5003)