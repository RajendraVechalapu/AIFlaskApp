from fastapi import FastAPI, Form, File, UploadFile, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
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
from model import *

app = FastAPI()
templates = Jinja2Templates(directory="templates")

max_tokens = 900
min_tokens = 10

# Initialize presentation globally
presentation = Presentation()
folder_path = "docs"

def process_text_and_display(piece_text, max_summary_length):
    # Example: Summarize the piece_text and display it
    summary = summarizeText(piece_text, max_summary_length)
    title = summarizeShort(piece_text)

    # Example: Split the summary into sentences (replace this with your logic)
    sentences = summary.split('.')

    add_slide(presentation, title, sentences)


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

def get_pptx_download_link(file_path):
    with open(file_path, 'rb') as f:
        pptx_data = f.read()
    encoded_pptx = base64.b64encode(pptx_data).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.presentationml.presentation;base64,{encoded_pptx}" download="Text_Summary_Presentation.pptx">Download PowerPoint Presentation</a>'
    return href


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
    try:
        # Step 1: Validate the URL
        if not validators.url(url):
            # Handle the case of an invalid URL
            return None

        # Step 2: Retrieve HTML content from the URL
        html_content = get_html_content(url)

        if html_content:
            # Step 3: Process the HTML content and extract relevant information
            nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
            soup = BeautifulSoup(html_content, "html.parser")
            title = soup.title.string
            web_text = soup.get_text()

            # Example: Create nested sentences (replace this with your logic)
            nested_sentences = create_nested_sentences(web_text, token_max_length=max_tokens)

            return {
                'url': url,
                'title': title,
                'cleaned_text': web_text
            }
        else:
            # Handle the case of a timeout or error while retrieving HTML content
            return None
    except Exception as e:
        # Handle other exceptions
        print(f"Error processing URL: {str(e)}")
        return None

def get_html_content(url):
    try:
        # Step 4: Make an HTTP request to the URL to retrieve HTML content
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        return response.text
    except requests.exceptions.RequestException as e:
        # Handle exceptions related to the HTTP request
        print(f"Error retrieving HTML content from URL: {url}\nError: {str(e)}")
        return None

# Routes
@app.get('/')
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post('/generate_summary')
async def generate_summary(
    request: Request,
    max_summary_length: int = Form(...),
    input_choice: str = Form(...),
    uploaded_file: UploadFile = File(...),
    pasted_text: str = Form(...),
):
    try:
        if input_choice == "Upload File":
            # Call the function to delete old files
            delete_old_files(folder_path)

            file_bytes = await uploaded_file.read()

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
            presentation.save(pptx_filepath)

            return templates.TemplateResponse(
                "result.html", {"request": request, "download_link": get_pptx_download_link(pptx_filepath)}
            )

        elif input_choice == "Paste Text":
            # Call the function to delete old files
            delete_old_files(folder_path)

            nested_sentences = create_nested_sentences(pasted_text, token_max_length=max_tokens)

            for idx, nested in enumerate(nested_sentences):
                concatenated_text = " ".join(nested)
                process_text_and_display(concatenated_text, max_summary_length)

            timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            pptx_filename = f"Text_Summary_Presentation_{timestamp}.pptx"
            pptx_filepath = os.path.join("docs", pptx_filename)
            presentation.save(pptx_filepath)

            return templates.TemplateResponse(
                "result.html", {"request": request, "download_link": get_pptx_download_link(pptx_filepath)}
            )

    except Exception as e:
        return HTMLResponse(content=f"Error: {str(e)}", status_code=500)