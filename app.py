from flask import Flask, request, render_template, jsonify, send_file
from markitdown import MarkItDown
import os
import uuid
import mimetypes
import json
import zipfile
import tempfile
import shutil
from pathlib import Path
from dotenv import load_dotenv
from ai_providers import AIProviderFactory

# .env dosyasından çevre değişkenlerini yükle
load_dotenv()

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
            
            # Archive dosyası ise içeriğini işle
            if is_archive_file(file.filename):
                archive_type = get_archive_type(file.filename)
                if archive_type == 'zip':
                    return process_zip_file(temp_filepath, file.filename)
                # Gelecekte diğer archive türleri için buraya eklenebilir

            # Görüntü dosyası ise AI ile işle
            if is_image:
                # AI provider'ın ayarlanıp ayarlanmadığını kontrol et
                try:
                    ai_provider = AIProviderFactory.get_provider()
                    if not ai_provider.is_available():
                        return jsonify({"error": "AI provider is not configured. Please set API keys in the .env file."}), 400

                    # Görüntü açıklaması için özelleştirilmiş prompt kullan (convert metodunda)
                    custom_prompt = """Bu bir profesyonel sunum görseli. Lütfen aşağıdaki yapıda analiz et:

**GÖRSEL TİPİ**: [Gantt Chart / Tablo / SmartArt / Flow Chart / Organizasyon Şeması / Matris / Timeline / Process Diagram / Diğer - hangisi olduğunu belirt]

**BAŞLIK/KONU**: [Görselin ana konusu veya başlığı]

**İÇERİK DETAYI**:
- Tüm metin içeriğini kelimesi kelimesine yaz
- Tablolarda: Tüm satır ve sütun başlıklarını ve hücre içeriklerini
- Flow/Process'lerde: Her kutunun içeriğini ve okların yönünü
- Gantt'larda: Görev adları, tarihler, süreler
- SmartArt'larda: Her bileşenin metnini hiyerarşik sırayla

**ANAHTAR KELİMELER**: [Bu görseli aramak için kullanılabilecek kelimeler - proje adları, departmanlar, tarihler, KPI'lar, metrikler]

**BAĞLAM/KULLANIM ALANI**: [Bu görselin hangi bağlamda kullanıldığı - strateji sunumu, proje planı, organizasyon yapısı, vs.]

**ÖNEMLİ DETAYLAR**: [Vurgulanan noktalar, renklerle belirtilen öncelikler, kritik tarihler]"""
                    
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

            # Markdown içeriğini kaydet
            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write(result.text_content)

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
            import re
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

                # Görüntü dosyası ise AI ile işle
                if is_image:
                    # AI provider'ın varlığını kontrol et
                    try:
                        ai_provider = AIProviderFactory.get_provider()
                        if not ai_provider.is_available():
                            markdown_content += f"\n## {relative_path}\n\n*Bu bir görüntü dosyasıdır ve dönüştürmek için AI provider ayarlanmış olmalıdır.*\n\n"
                            continue
                    except Exception:
                        markdown_content += f"\n## {relative_path}\n\n*Bu bir görüntü dosyasıdır ve dönüştürmek için AI provider ayarlanmış olmalıdır.*\n\n"
                        continue

                    # Görüntü açıklaması için özelleştirilmiş prompt kullan (convert metodunda)
                    custom_prompt = """Bu bir profesyonel sunum görseli. Lütfen aşağıdaki yapıda analiz et:

**GÖRSEL TİPİ**: [Gantt Chart / Tablo / SmartArt / Flow Chart / Organizasyon Şeması / Matris / Timeline / Process Diagram / Diğer - hangisi olduğunu belirt]

**BAŞLIK/KONU**: [Görselin ana konusu veya başlığı]

**İÇERİK DETAYI**:
- Tüm metin içeriğini kelimesi kelimesine yaz
- Tablolarda: Tüm satır ve sütun başlıklarını ve hücre içeriklerini
- Flow/Process'lerde: Her kutunun içeriğini ve okların yönünü
- Gantt'larda: Görev adları, tarihler, süreler
- SmartArt'larda: Her bileşenin metnini hiyerarşik sırayla

**ANAHTAR KELİMELER**: [Bu görseli aramak için kullanılabilecek kelimeler - proje adları, departmanlar, tarihler, KPI'lar, metrikler]

**BAĞLAM/KULLANIM ALANI**: [Bu görselin hangi bağlamda kullanıldığı - strateji sunumu, proje planı, organizasyon yapısı, vs.]

**ÖNEMLİ DETAYLAR**: [Vurgulanan noktalar, renklerle belirtilen öncelikler, kritik tarihler]"""
                    markitdown = MarkItDown(llm_client=ai_provider.get_client_for_markitdown(), llm_model=ai_provider.get_model_name())
                else:
                    markitdown = MarkItDown()

                # Dosyayı dönüştür - Görüntüyse özelleştirilmiş promptu convert metoduna geçir
                if is_image and ai_provider.is_available():
                    result = markitdown.convert(file_path, llm_prompt=custom_prompt)
                else:
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

    # Markdown içeriğini kaydet
    with open(output_filepath, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

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
                
                # Handle archive files
                if is_archive_file(file.filename):
                    archive_type = get_archive_type(file.filename)
                    if archive_type == 'zip':
                        # Extract and process ZIP contents
                        zip_result = process_zip_file(temp_filepath, file.filename)
                        zip_data = json.loads(zip_result.get_data(as_text=True))
                        markdown_content += f"\n## File {i}: {file.filename}\n\n{zip_data['markdown']}\n\n---\n\n"
                    continue
                
                # Handle images with AI
                if is_image:
                    try:
                        ai_provider = AIProviderFactory.get_provider()
                        if not ai_provider.is_available():
                            markdown_content += f"\n## File {i}: {file.filename}\n\n*This is an image file and requires AI provider configuration for conversion.*\n\n---\n\n"
                            continue
                            
                        custom_prompt = """Bu bir profesyonel sunum görseli. Lütfen aşağıdaki yapıda analiz et:

**GÖRSEL TİPİ**: [Gantt Chart / Tablo / SmartArt / Flow Chart / Organizasyon Şeması / Matris / Timeline / Process Diagram / Diğer - hangisi olduğunu belirt]

**BAŞLIK/KONU**: [Görselin ana konusu veya başlığı]

**İÇERİK DETAYI**:
- Tüm metin içeriğini kelimesi kelimesine yaz
- Tablolarda: Tüm satır ve sütun başlıklarını ve hücre içeriklerini
- Flow/Process'lerde: Her kutunun içeriğini ve okların yönünü
- Gantt'larda: Görev adları, tarihler, süreler
- SmartArt'larda: Her bileşenin metnini hiyerarşik sırayla

**ANAHTAR KELİMELER**: [Bu görseli aramak için kullanılabilecek kelimeler - proje adları, departmanlar, tarihler, KPI'lar, metrikler]

**BAĞLAM/KULLANIM ALANI**: [Bu görselin hangi bağlamda kullanıldığı - strateji sunumu, proje planı, organizasyon yapısı, vs.]

**ÖNEMLİ DETAYLAR**: [Vurgulanan noktalar, renklerle belirtilen öncelikler, kritik tarihler]"""
                        
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
            f.write(markdown_content)
        
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
            f.write(enhanced_content)

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

        # OpenAI API'yi kullanarak transcript'i özetle
        prompt = f"""
        You are an expert video summarizer and analyzer. Summarize and analyze the following YouTube video transcript.

        Video URL: {youtube_url}

        Transcript:
        {transcript}

        Please provide:
        1. A concise 2-3 sentence summary of the video content
        2. The main topics covered
        3. Key takeaways or insights
        4. Any notable quotes or statements
        5. An overall analysis of the content

        Format your response in Markdown with appropriate headings, bullet points, and formatting.
        """

        # AI API çağrısı
        messages = [
            {"role": "system", "content": "You are an expert video summarizer that creates well-structured markdown summaries."},
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
            f.write(enhanced_summary)

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
            f.write(markdown_content)
        
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

        # Prepare prompt for multiple videos
        prompt = "You are an expert video summarizer and analyzer. Below are transcripts from multiple YouTube videos. Please provide:\n\n"
        prompt += "1. A brief overview of all videos (2-3 sentences)\n"
        prompt += "2. Individual summaries for each video\n"
        prompt += "3. Common themes across all videos\n"
        prompt += "4. Key takeaways from the collection\n"
        prompt += "5. Any connections or contrasts between the videos\n\n"
        prompt += "Videos:\n\n"
        
        for i, transcript in enumerate(transcripts, 1):
            prompt += f"Video {i} ({transcript['url']}):\n{transcript['content']}\n\n"
        
        prompt += "\nFormat your response in Markdown with appropriate headings, bullet points, and formatting."

        # AI API call
        messages = [
            {"role": "system", "content": "You are an expert video summarizer that creates well-structured markdown summaries for multiple videos."},
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
            f.write(enhanced_summary)

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

        # Custom prompt ile AI API çağrısı
        prompt = f"""
        You are an AI assistant that helps restructure and reformat content based on user requirements.
        
        User's custom request: {custom_prompt}
        
        Content to restructure:
        {content}
        
        Please follow the user's request exactly and format your response in Markdown with appropriate headings, bullet points, and formatting.
        """

        # AI API çağrısı
        messages = [
            {"role": "system", "content": "You are an expert content restructurer that follows user instructions precisely and creates well-structured markdown content."},
            {"role": "user", "content": prompt}
        ]
        
        restructured_content = ai_provider.chat_completion(messages, max_tokens=2000)

        # Add header with user prompt
        enhanced_content = f"# AI Restructured Content\n\n**User Request:** {custom_prompt}\n\n---\n\n{restructured_content}"

        # Save restructured content
        unique_id = str(uuid.uuid4())
        output_filename = f"restructured_{unique_id}.md"
        output_filepath = os.path.join(UPLOAD_FOLDER, output_filename)

        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(enhanced_content)

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
        import re
        filename = re.sub(r'[^\w\-_.]', '_', filename)
        if not filename.endswith('.md'):
            filename += '.md'

        # Create temporary file
        temp_filepath = os.path.join(UPLOAD_FOLDER, f"custom_{uuid.uuid4()}_{filename}")
        
        with open(temp_filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        # Return file as download
        response = send_file(temp_filepath, as_attachment=True, download_name=filename)
        
        # Clean up the temporary file after sending
        def remove_file():
            try:
                if os.path.exists(temp_filepath):
                    os.remove(temp_filepath)
            except:
                pass
        
        response.call_on_close(remove_file)
        
        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5005)