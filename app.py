from flask import Flask, render_template, request
import requests

app = Flask(__name__)

# Hugging Face API endpoint for summarization
HUGGINGFACE_SUMMARIZATION_API = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
HUGGINGFACE_API_KEY = "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"  # Replace with your actual API key

headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}

@app.route('/')
def index():
    return render_template('index.html', summary_result=None)

@app.route('/summarize_text', methods=['POST'])
def summarize_text():
    summary_result = None

    if 'text' in request.form:
        text = request.form['text']
        summary_result = summarizeTextHuggingFace(text, max_summary_length=150)

    return render_template('index.html', summary_result=summary_result)

def summarizeTextHuggingFace(text, max_summary_length):
    try:
        payload = {"inputs": text, "max_summary_length": max_summary_length}
        response = requests.post(HUGGINGFACE_SUMMARIZATION_API, headers=headers, json=payload)
        response.raise_for_status()  # Check for HTTP errors
        summary = response.json()[0]['summary_text']
        return summary
    except requests.exceptions.RequestException as e:
        # Handle request errors gracefully
        print(f"Error in summarization request: {e}")
        return None  # Return None in case of an error

if __name__ == '__main__':
    app.run(debug=True)
