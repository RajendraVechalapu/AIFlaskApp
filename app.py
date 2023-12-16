from flask import Flask, request, jsonify
from transformers import pipeline

app = Flask(__name__)

# Choose a pre-trained model for text generation
text_generator = pipeline("text-generation", model="distilbert-base-uncased")

@app.route('/')
def hello_world():
    return 'ఓం నమో విఘ్నేశ్వరాయ నమః'

@app.route('/generate_caption', methods=['POST'])
def generate_caption():
    # Get the image file from the request
    image = request.files['image']

    # Read the image data
    image_data = image.read()

    # Generate a caption using the pre-trained model
    generated_caption = text_generator("a description of the image", max_length=50, num_return_sequences=1)[0]['generated_text'].strip()

    return jsonify({'generated_caption': generated_caption})

if __name__ == '__main__':
    app.run(debug=True)
