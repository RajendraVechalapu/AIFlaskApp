import re
import openai  # Make sure to install the OpenAI library
import requests
import numpy as np
import nltk
from nltk.tokenize import sent_tokenize

nltk.download('punkt')

# Global Constants
BART_LARGE_CNN_MODEL_NAME = "facebook/bart-large-cnn"
AUTOMATIC_TITLE_GENERATION_MODEL_NAME = "deep-learning-analytics/automatic-title-generation"

# Set the global parameter to choose the summarization method
SUMMARIZATION_METHOD = "HUGGING_FACE"  # Choose from "OPENAI", "HUGGING_FACE", or "LOCAL_MODEL"

# OpenAI API key (replace with your actual OpenAI API key)
OPENAI_API_KEY = "REMOVED_OPENAI_KEY"

def segment_sentences_with_punkt(text):
    # Use NLTK's punkt tokenizer for sentence segmentation
    sentences = sent_tokenize(text)
    return sentences

def summarizeTextHuggingFace(text, max_summary_length):
    # Use Hugging Face model
    HUGGINGFACE_API_KEY = "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"  # Replace with your actual API key
    HUGGINGFACE_SUMMARIZATION_API = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}

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

def summarizeTextOpenAI(text, max_summary_length):
    # Use OpenAI API
    openai.api_key = OPENAI_API_KEY
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=text,
        max_tokens=max_summary_length
    )
    summary = response.choices[0].text.strip()
    return summary

def summarizeText(text, max_summary_length):
    if SUMMARIZATION_METHOD == "HUGGING_FACE":
        return summarizeTextHuggingFace(text, max_summary_length)
    elif SUMMARIZATION_METHOD == "OPENAI":
        return summarizeTextOpenAI(text, max_summary_length)
    else:
        # Use the existing local model
        return summarizeTextHuggingFace(text, max_summary_length)  # You can adjust this if needed

def summarizeShort(text):
    if SUMMARIZATION_METHOD == "HUGGING_FACE":
        model_name = "deep-learning-analytics/automatic-title-generation"
        HUGGINGFACE_API_KEY = "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"  # Replace with your actual API key
        HUGGINGFACE_SUMMARIZATION_API = f"https://api-inference.huggingface.co/models/{model_name}"
        headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}

        try:
            payload = {"inputs": text, "max_summary_length": 50}
            response = requests.post(HUGGINGFACE_SUMMARIZATION_API, headers=headers, json=payload)
            response.raise_for_status()  # Check for HTTP errors
            summary = response.json()[0]['generated_text']
            return summary
        except requests.exceptions.RequestException as e:
            # Handle request errors gracefully
            print(f"Error in summarization request: {e}")
            return None  # Return None in case of an error
    else:
        # Use the existing local model
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=text,
            max_tokens=20,
            temperature=0.7  # Adjust temperature as needed
        )
        predicted_title = response.choices[0].text.strip()
        return predicted_title

def count_tokens(sentence_list):
    total_tokens = 0
    for sentence in sentence_list:
        total_tokens += len(sentence.split())
    return total_tokens

# Reference: https://discuss.huggingface.co/t/summarization-on-long-documents/920/7
def create_nested_sentences(document: str, token_max_length: int = 900):
    nested = []
    sent = []
    length = 0

    for sentence in re.split(r'(?<=[^A-Z].[.?]) +(?=[A-Z])', document.replace("\n", ' ')):
        length += len(sentence.split())
        if length < token_max_length:
            sent.append(sentence)
        else:
            nested.append(sent)
            sent = [sentence]
            length = 0
    if sent:
        nested.append(sent)
    return nested
