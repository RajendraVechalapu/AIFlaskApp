from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return "No file part"

    file = request.files['file']

    if file.filename == '':
        return "No selected file"

    content = file.read().decode('utf-8')

    return render_template('index.html', content=content)

if __name__ == '__main__':
    app.run(debug=True)
