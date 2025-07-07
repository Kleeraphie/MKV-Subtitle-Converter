from flask import Flask, render_template, make_response, request
from config import Config
import json
import os

app = Flask(__name__, template_folder='gui/web/templates', static_folder='gui/web/frontend')

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/version')
def get_version():
    config = Config()
    response = make_response(config.get_version(), 200)
    response.mimetype = "text/plain"
    return response

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return make_response("No file part", 400)
    file = request.files['file']
    if file.filename == '':
        return make_response("No selected file", 400)
    if file:
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return make_response("File uploaded successfully", 200)

@app.route('/convert', methods=['POST'])
def convert():
    data = json.loads(request.data)
    if not data:
        return make_response("No data provided", 400)

    uploaded_files = data.get('uploadedFiles', [])
    brightness = data.get('brightness', 0)
    edit_before_muxing = data.get('edit', False)
    save_pgs_images = data.get('saveImages', False)
    keep_original_mkv = data.get('keepFiles', False)
    keep_copy_old = data.get('keepOldSubs', False)
    keep_copy_new = data.get('keepNewSubs', False)
    use_different_languages = data.get('useDiffLang', False)

    print(uploaded_files)
    
    response = json.dumps({
        'success': True
    })
    return make_response(response, 200, {'Content-Type': 'application/json'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
