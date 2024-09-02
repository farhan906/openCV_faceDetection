from flask import Flask, render_template
from imgenter import imgenter
from facerecog import facerecog


app = Flask(__name__)


# Register Blueprints
app.register_blueprint(imgenter, url_prefix='/imgenter')
app.register_blueprint(facerecog, url_prefix='/facerecog')

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=True)
