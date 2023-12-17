from flask import Flask, render_template, request
import requests

app = Flask(__name__)

# Hugging Face API endpoint for sentiment analysis
HUGGINGFACE_SENTIMENT_API = "https://api-inference.huggingface.co/models/lxyuan/distilbert-base-multilingual-cased-sentiments-student"
HUGGINGFACE_API_KEY = "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"  # Replace with your actual API key

headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}

@app.route('/')
def index():
    return render_template('index.html', sentiment_result=None)

@app.route('/analyze_sentiment', methods=['POST'])
def analyze_sentiment():
    sentiment_result = None

    if 'text' in request.form:
        text = request.form['text']
        sentiment_result = query_sentiment(text)

    return render_template('index.html', sentiment_result=sentiment_result)

def query_sentiment(text):
    try:
        payload = {"inputs": text}
        response = requests.post(HUGGINGFACE_SENTIMENT_API, headers=headers, json=payload)
        response.raise_for_status()  # Check for HTTP errors
        sentiment_result = response.json()[0]
        return sentiment_result
    except requests.exceptions.RequestException as e:
        # Handle request errors gracefully
        print(f"Error in sentiment analysis request: {e}")
        return None  # Return None in case of an error

if __name__ == '__main__':
    app.run(debug=True)
