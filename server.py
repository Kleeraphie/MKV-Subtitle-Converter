from flask import Flask, render_template, make_response, request
from config import Config
import json
import os
import logging
import requests
from packaging.version import Version

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

@app.route('/theme', methods=['GET', 'POST'])
def get_theme():
    config = Config()
    if request.method == 'POST':
        # Assuming the theme is in plain text format
        theme = request.data.decode('utf-8')
        settings = {
            Config.Settings.THEME: theme
        }
        print(f"Setting theme to: {theme}")
        config.save_settings(settings)
        config.save_config()
        return make_response("Theme updated successfully", 200)  # Add this line
    else:
        response = make_response(config.get_theme(), 200)
        response.mimetype = "text/plain"
        return response

@app.route('/checkForUpdate')
def check_for_update():
    config = Config()
    logging.info("Checking for updates.")

    try:
        response = requests.get("https://api.github.com/repos/Kleeraphie/MKV-Subtitle-Converter/releases/latest")
        latest_version = response.json()["tag_name"]

        update_available = Version(latest_version) > Version(config.get_version())
    except: # if there is no internet connection or the request fails
        update_available = False

        if update_available:
            print(f"Update available: {latest_version}")
        else:
            print("No update available or unable to check for updates.")

    response = {
        'updateAvailable': update_available,
        'latestVersion': latest_version if update_available else None
    }
    return make_response(json.dumps(response), 200, {'Content-Type': 'application/json'})

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
