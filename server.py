
from flask import Flask, render_template, make_response
from config import Config

app = Flask(__name__, template_folder='gui/web/templates', static_folder='gui/web/frontend')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/version')
def get_version():
    config = Config()
    response = make_response(config.get_version(), 200)
    response.mimetype = "text/plain"
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
