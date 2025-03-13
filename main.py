from flask import Flask, render_template
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello World! Aplikasi berjalan."

@app.route('/test')
def test():
    return "Test endpoint berfungsi."

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)