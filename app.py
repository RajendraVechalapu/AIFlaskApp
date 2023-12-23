from flask import Flask, render_template, request
import os
from datetime import datetime, timedelta
from io import BytesIO
import base64
from docx import Document
from pptx.util import Pt, Inches
from pptx import Presentation
from pptx.dml.color import RGBColor
from PyPDF2 import PdfReader
from bs4 import BeautifulSoup
import validators
import fitz
import requests
#import torch
#import chardet
import spacy
#import streamlit as st
from model import *

app = Flask(__name__)
#app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # Set the maximum file size to 32 MB (adjust as needed)

# Initialize presentation globally

# Call the function to delete old files
#delete_old_files(folder_path)

def process_text_and_display(piece_text, max_summary_length):
    summary = summarizeText(piece_text, max_summary_length)
    title = summarizeShort(piece_text)

    # Use spaCy for sentence tokenization
    # nlp = spacy.load("en_core_web_sm")
    # sentences = [sentence.text.strip() for sentence in nlp(summary).sents]
    #sentences = segment_sentences_with_punkt(summary)
    sentences="rajendra simhadri"

    
def delete_old_files(folder_path, time_threshold_seconds=120):
    current_time = datetime.now()

    for filename in os.listdir(folder_path):
        if filename.startswith("Text_Summary_Presentation_") and filename.endswith(".pptx"):
            file_path = os.path.join(folder_path, filename)

            # Get the file creation timestamp
            created_timestamp = datetime.fromtimestamp(os.path.getctime(file_path))

            # Calculate the time difference
            time_difference = current_time - created_timestamp

            # If the file is older than the threshold, delete it
            if time_difference.total_seconds() > time_threshold_seconds:
                os.remove(file_path)

def add_slide(prs, title, sentences):
    slide_layout = prs.slide_layouts[5]  # Use a blank slide layout
    slide = prs.slides.add_slide(slide_layout)

    # Add title with background color
    title_shape = slide.shapes.title
    title_shape.text = title
    title_shape.text_frame.text = title
    title_shape.text_frame.paragraphs[0].font.size = Pt(20)  # Set font size for the title
    title_shape.fill.solid()
    title_shape.fill.fore_color.rgb = RGBColor(91, 155, 213)  # Set background color for the title

    # Add content
    content_box = slide.shapes.add_textbox(left=Inches(1), top=Inches(2), width=Inches(8), height=Inches(4))
    content_frame = content_box.text_frame
    content_frame.word_wrap = True

    for i, sentence in enumerate(sentences, start=1):
        p = content_frame.add_paragraph()
        p.text = f"{i}. {sentence}"

        p.font.size = Pt(15)  # Set font size for the content
        # Add an empty line after each sentence
        content_frame.add_paragraph().space_after = Pt(5)



def get_pptx_download_link(file_path):
    with open(file_path, 'rb') as f:
        pptx_data = f.read()
    encoded_pptx = base64.b64encode(pptx_data).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.presentationml.presentation;base64,{encoded_pptx}" download="Text_Summary_Presentation.pptx">Download PowerPoint Presentation</a>'
    return href

def get_html_content(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving HTML content from URL: {url}\nError: {str(e)}")
        return None
    
def extract_page_pdf_text(file_bytes):
    doc = fitz.open("pdf", file_bytes)
    page_texts = []

    for page in doc:
        page_text = page.get_text()
        page_texts.append(page_text)

    doc.close()
    return page_texts

def extract_text_from_docx(file_bytes):
    doc = Document(BytesIO(file_bytes))
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"

    return text

def process_url(url, max_summary_length, max_tokens):
    if not validators.url(url):
        st.error("Invalid URL. Please enter a valid URL.")
        return None

    html_content = get_html_content(url)

    if html_content:
        nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
        soup = BeautifulSoup(html_content, "html.parser")
        title = soup.title.string
        web_text = soup.get_text()

        nested_sentences = create_nested_sentences(web_text, token_max_length=max_tokens)

        return {
            'url': url,
            'title': title,
            'cleaned_text': web_text
        }
    else:
        st.error(f"Timeout occurred for URL: {url}. Skipping...")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_summary', methods=['POST'])
def generate_summary():
    max_summary_length = int(request.form['max_summary_length'])
    input_choice = request.form['input_choice']

    if input_choice == "Website URL":
        url_input = request.form['url_input']

        if url_input:
            # Call the function to delete old files

            

            return render_template('result.html', download_link=get_pptx_download_link(pptx_filepath))

    elif input_choice == "Upload File":
        uploaded_file = request.files['uploaded_file']

        if uploaded_file:
            # Call the function to delete old files

            file_bytes = uploaded_file.read()
            file_extension = os.path.splitext(uploaded_file.filename)[-1].lower()


            if file_extension == ".pdf":
                page_texts = extract_page_pdf_text(file_bytes)

                for page_num, page_text in enumerate(page_texts, start=1):
                    nested_sentences = create_nested_sentences(page_text, token_max_length=900)
                    for idx, nested in enumerate(nested_sentences):
                        concatenated_text = " ".join(nested)
                        process_text_and_display(concatenated_text, max_summary_length)

            elif file_extension == ".docx":
                page_text = extract_text_from_docx(file_bytes)

                nested_sentences = create_nested_sentences(page_text, token_max_length=900)

                for idx, nested in enumerate(nested_sentences):
                    concatenated_text = " ".join(nested)
                    process_text_and_display(concatenated_text, max_summary_length)

            elif file_extension == ".txt":
                text = file_bytes.decode('utf-8')
                nested_sentences = create_nested_sentences(text, token_max_length=900)

                for idx, nested in enumerate(nested_sentences):
                    concatenated_text = " ".join(nested)
                    process_text_and_display(concatenated_text, max_summary_length)

            timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            pptx_filename = f"Text_Summary_Presentation_{timestamp}.pptx"
            pptx_filepath = os.path.join("docs", pptx_filename)

            return render_template('result.html', download_link=get_pptx_download_link(pptx_filepath))

    elif input_choice == "Paste Text":
        pasted_text = request.form['pasted_text']

        if pasted_text:
            # Call the function to delete old files

            nested_sentences = create_nested_sentences(pasted_text, token_max_length=max_tokens)

            for idx, nested in enumerate(nested_sentences):
                concatenated_text = " ".join(nested)
                process_text_and_display(concatenated_text, max_summary_length)

            timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            pptx_filename = f"Text_Summary_Presentation_{timestamp}.pptx"
            pptx_filepath = os.path.join("docs", pptx_filename)

            return render_template('result.html', download_link=get_pptx_download_link(pptx_filepath))

    # Handle other cases or display an error message if necessary
    return "Invalid input choice or missing data."

if __name__ == '__main__':
    app.run(debug=True)
