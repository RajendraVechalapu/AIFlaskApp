from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', content="", token_count=None)

@app.route('/upload', methods=['POST'])
def upload():
    content = ""
    token_count = None

    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            content = file.read().decode('utf-8')
            token_count = count_words(content)

    if 'free_text' in request.form:
        free_text = request.form['free_text']
        content = free_text
        token_count = count_words(free_text)

    return render_template('index.html', content=content, token_count=token_count)

def count_words(text):
    words = text.split()
    return len(words)

if __name__ == '__main__':
    app.run(debug=True)
