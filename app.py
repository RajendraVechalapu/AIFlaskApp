from flask import Flask, render_template, request
from transformers import AutoTokenizer

app = Flask(__name__)

# Replace 'bert-base-uncased' with the specific model you are using
tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')

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
            token_count = count_tokens(content)

    if 'free_text' in request.form:
        free_text = request.form['free_text']
        content = free_text
        token_count = count_tokens(free_text)

    return render_template('index.html', content=content, token_count=token_count)

def count_tokens(text):
    # Use 'return_tensors' argument to ensure the output is a tensor
    tokens = tokenizer.encode(text, return_tensors="pt")
    return len(tokens[0])  # Extract the number of tokens using len()

if __name__ == '__main__':
    app.run(debug=True)
