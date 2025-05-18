from flask import Flask, request, render_template, jsonify, send_file
from markitdown import MarkItDown
from openai import OpenAI
import os
import uuid
import mimetypes
import json
import zipfile
import tempfile
import shutil
from pathlib import Path
from dotenv import load_dotenv

# .env dosyasından çevre değişkenlerini yükle
load_dotenv()

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# OpenAI istemcisini yapılandır - API anahtarını .env dosyasından al
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded!"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected!"}), 400

    # Geçici bir dosya yolu oluştur
    temp_filepath = os.path.join(UPLOAD_FOLDER, f"temp_{uuid.uuid4()}_{file.filename}")
    file.save(temp_filepath)

    try:
        # Dosya türünü kontrol et
        mime_type, _ = mimetypes.guess_type(temp_filepath)
        is_image = mime_type and mime_type.startswith('image/')
        is_zip = mime_type == 'application/zip' or file.filename.lower().endswith('.zip')

        # ZIP dosyası ise içeriğini işle
        if is_zip:
            return process_zip_file(temp_filepath, file.filename)

        # Görüntü dosyası ise OpenAI ile işle
        if is_image:
            # API anahtarının ayarlanıp ayarlanmadığını kontrol et
            try:
                # API anahtarı ayarlanmamışsa hata verir
                if not openai_client.api_key:
                    return jsonify({"error": "OpenAI API key is not set. For image conversion, please set the OPENAI_API_KEY environment variable."}), 400

                # Görüntü açıklaması için özelleştirilmiş prompt kullan (convert metodunda)
                custom_prompt = "Bu görselde ne olduğunu detaylı olarak ve Türkçe açıkla. Ana unsurları, renkler ve kompozisyonu belirt. Metin varsa, metni de belirt."
                markitdown = MarkItDown(llm_client=openai_client, llm_model="gpt-4o")
            except Exception as e:
                return jsonify({"error": f"OpenAI error: {str(e)}. Please check your API key."}), 400
        else:
            markitdown = MarkItDown()

        # Görüntüyse özelleştirilmiş promptu convert metoduna geçir
        if is_image and openai_client.api_key:
            result = markitdown.convert(temp_filepath, llm_prompt=custom_prompt)
        else:
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

        # Çıkarılan dosyaları işle
        extracted_files = []
        for root, _, files in os.walk(temp_dir):
            for filename in files:
                file_path = os.path.join(root, filename)
                relative_path = os.path.relpath(file_path, temp_dir)
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

                # Görüntü dosyası ise OpenAI ile işle
                if is_image:
                    # API anahtarının varlığını kontrol et
                    if not openai_client.api_key:
                        markdown_content += f"\n## {relative_path}\n\n*Bu bir görüntü dosyasıdır ve dönüştürmek için OpenAI API anahtarı gereklidir.*\n\n"
                        continue

                    # Görüntü açıklaması için özelleştirilmiş prompt kullan (convert metodunda)
                    custom_prompt = "Bu görselde ne olduğunu detaylı olarak ve Türkçe açıkla. Ana unsurları, renkler ve kompozisyonu belirt. Metin varsa, metni de belirt."
                    markitdown = MarkItDown(llm_client=openai_client, llm_model="gpt-4o")
                else:
                    markitdown = MarkItDown()

                # Dosyayı dönüştür - Görüntüyse özelleştirilmiş promptu convert metoduna geçir
                if is_image and openai_client.api_key:
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
        # API anahtarının ayarlanıp ayarlanmadığını kontrol et
        if not openai_client.api_key:
            return jsonify({"error": "OpenAI API key is not set. Please set it in the .env file."}), 400

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

        # ChatGPT API çağrısı
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # veya "gpt-3.5-turbo" gibi bir modeli kullanabilirsiniz
            messages=[
                {"role": "system", "content": "You are an expert video summarizer that creates well-structured markdown summaries."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500
        )

        # AI tarafından oluşturulan özet
        summary = response.choices[0].message.content

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

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5002)