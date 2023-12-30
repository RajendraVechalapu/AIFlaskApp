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
import chardet
import spacy
from model import *


app = FastAPI()
templates = Jinja2Templates(directory="templates")

max_tokens = 900
min_tokens = 10

# Initialize presentation globally
#presentation = Presentation()
#folder_path = "docs"

def process_text_and_display(piece_text, max_summary_length):
    
    summary = summarizeText(piece_text, max_summary_length)
    
    #st.write(f"\nSummary \n\n {summary}")
    #formatted_summary = format_summary_with_numbers(summary)
    
    title = summarizeShort(piece_text)
    #st.write(f"Title ({title})")
    # Use spaCy for sentence tokenization
    
    # Load the spaCy English model
    nlp = spacy.load("en_core_web_sm")
    sentences = [sentence.text.strip() for sentence in nlp(summary).sents]

    return sentences
    # for sentence in sentences:
    #     st.write(f"- {sentence}")
        
    #add_slide(presentation, title, sentences)


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



@app.get('/')
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post('/generate_summary')
async def generate_summary(
    request: Request,
    max_summary_length: int = Form(...),
    #input_choice: str = Form(...),
    input_choice: str = Form(None),
    uploaded_file: UploadFile = File(...),
    #pasted_text: str = Form(...),
    pasted_text: str = Form(None),  # Make pasted_text optional
):
    try:
        # Initialize presentation globally
        global presentation

        if input_choice == "Upload File":
            file_bytes = await uploaded_file.read()
            file_extension = os.path.splitext(uploaded_file.filename)[-1].lower()

            if file_extension == ".pdf":
                page_texts = extract_page_pdf_text(file_bytes)

                concateddata = ""
                for page_num, page_text in enumerate(page_texts, start=1):
                    nested_sentences = create_nested_sentences(page_text, token_max_length=900)
                    concateddata += f"Page: {page_num}: <br><br>"

                    for idx, nested in enumerate(nested_sentences):
                        concatenated_text = " ".join(nested)
                        sentences = process_text_and_display(concatenated_text, max_summary_length)

                        for i, sentence in enumerate(sentences, start=1):
                            concateddata += f"  {i}. {sentence}<br><br>"

            elif file_extension == ".docx":
                # ... (similar logic for other file types)
                page_text = extract_text_from_docx(file_bytes)
                nested_sentences = create_nested_sentences(page_text, token_max_length=max_tokens)
                concateddata = ""

                for idx, nested in enumerate(nested_sentences):
                    concatenated_text = " ".join(nested)
                    sentences = process_text_and_display(concatenated_text, max_summary_length)

                    # Accumulate sentences for each concatenated_text
                    for i, sentence in enumerate(sentences, start=1):
                        concateddata += f"{i}. {sentence}<br><br>"

                # # Return a response indicating success
                # return templates.TemplateResponse(
                #     "result.html", {"request": request, "concateddata": concateddata, "success_message": "Content processed successfully"}
                # )
                # pass

            elif file_extension == ".txt":
                    # Process TXT file
                # Determine the file encoding (assuming UTF-8 if not specified)
                file_encoding = chardet.detect(file_bytes)['encoding'] or 'utf-8'

                text = file_bytes.decode(file_encoding)
                #text = file_bytes.decode('utf-8')
                nested_sentences = create_nested_sentences(text, token_max_length=max_tokens)
                concateddata = ""

                for idx, nested in enumerate(nested_sentences):
                    concatenated_text = " ".join(nested)
                    sentences = process_text_and_display(concatenated_text, max_summary_length)

                    # Accumulate sentences for each concatenated_text
                    for i, sentence in enumerate(sentences, start=1):
                        concateddata += f"{i}. {sentence}<br><br>"

                    # Return a response indicating success
                # return templates.TemplateResponse(
                #     "result.html", {"request": request, "concateddata": concateddata, "success_message": "Content processed successfully"}
                # )
        
                # pass

        elif input_choice == "Paste Text":
            nested_sentences = create_nested_sentences(pasted_text, token_max_length=max_tokens)

            concateddata = ""
            for idx, nested in enumerate(nested_sentences):
                concatenated_text = " ".join(nested)
                sentences = process_text_and_display(concatenated_text, max_summary_length)

                for i, sentence in enumerate(sentences, start=1):
                    concateddata += f"  {i}. {sentence}<br><br>"

        return templates.TemplateResponse(
            "result.html", {"request": request, "concateddata": concateddata, "success_message": "Content processed successfully"}
        )

    except Exception as e:
        error_message = f"Error: {str(e)}"
        return templates.TemplateResponse(
            "result.html", {"request": request, "concateddata": error_message}
        )