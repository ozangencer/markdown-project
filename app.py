from flask import Flask, request, render_template, jsonify, send_file
from markitdown import MarkItDown
import os
import uuid

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    try:
        markitdown = MarkItDown()
        result = markitdown.convert(filepath)

        output_file = filepath + '.md'
        with open(output_file, 'w') as f:
            f.write(result.text_content)

        # Markdown içeriğini JSON olarak döndür
        return jsonify({
            "markdown": result.text_content,
            "download_url": f"/download/{os.path.basename(output_file)}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

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

        # Save the markdown result
        with open(output_filepath, 'w') as f:
            f.write(result.text_content)

        return jsonify({
            "markdown": result.text_content,
            "download_url": f"/download/{output_filename}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5001)