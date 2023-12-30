from fastapi import Depends, FastAPI, Form, File, UploadFile, Request
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
import fitz
import requests
import chardet
import spacy
from model import *
from tempfile import NamedTemporaryFile
import uuid

app = FastAPI()
templates = Jinja2Templates(directory="templates")

max_tokens = 900
min_tokens = 10
folder_path = "generatedfiles"


def write_summary_to_temp_file(summary: str):
    os.makedirs(folder_path, exist_ok=True)
    with NamedTemporaryFile(mode="w+", delete=False, suffix=".txt", prefix="summary_", dir=folder_path) as temp_file:
        temp_file.write(summary)
        return temp_file.name


def generate_request_id():
    return str(uuid.uuid4())


def write_summary_to_file(request_id: str, summary: str):
    file_name = f"summary_{request_id}.txt"
    with open(os.path.join(folder_path, file_name), "w") as file:
        file.write(summary)
    return file_name


def read_summary_from_file(file_path: str):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        print(f"Error reading summary from file: {str(e)}")
        return None


def delete_old_files(time_threshold_seconds: int = 300):
    current_time = datetime.now()
    for file_name in os.listdir(folder_path):
        if file_name.startswith("summary_") and file_name.endswith(".txt"):
            file_path = os.path.join(folder_path, file_name)
            created_timestamp = datetime.fromtimestamp(os.path.getctime(file_path))
            time_difference = current_time - created_timestamp
            if time_difference.total_seconds() > time_threshold_seconds:
                os.remove(file_path)


def process_text_and_display(piece_text, max_summary_length):
    summary = summarizeText(piece_text, max_summary_length)

    title = summarizeShort(piece_text)

    nlp = spacy.load("en_core_web_sm")
    sentences = [sentence.text.strip() for sentence in nlp(summary).sents]

    return sentences


def add_slide(prs, title, sentences):
    slide_layout = prs.slide_layouts[5]
    slide = prs.slides.add_slide(slide_layout)

    title_shape = slide.shapes.title
    title_shape.text = title
    title_shape.text_frame.text = title
    title_shape.text_frame.paragraphs[0].font.size = Pt(20)
    title_shape.fill.solid()
    title_shape.fill.fore_color.rgb = RGBColor(91, 155, 213)

    content_box = slide.shapes.add_textbox(left=Inches(1), top=Inches(2), width=Inches(8), height=Inches(4))
    content_frame = content_box.text_frame
    content_frame.word_wrap = True

    for i, sentence in enumerate(sentences, start=1):
        p = content_frame.add_paragraph()
        p.text = f"{i}. {sentence}"

        p.font.size = Pt(15)
        content_frame.add_paragraph().space_after = Pt(5)


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
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving HTML content from URL: {url}\nError: {str(e)}")
        return None


@app.get('/')
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post('/generate_summary')
async def generate_summary(
    request: Request,
    max_summary_length: int = Form(...),
    input_choice: str = Form(None),
    uploaded_file: UploadFile = File(...),
    pasted_text: str = Form(None),
    request_id: str = Depends(generate_request_id),
):
    try:
        if input_choice == "Upload File":
            file_bytes = await uploaded_file.read()
            file_extension = os.path.splitext(uploaded_file.filename)[-1].lower()

            if file_extension == ".pdf":
                page_texts = extract_page_pdf_text(file_bytes)

                summary_file_path = write_summary_to_temp_file("")  # Create an empty temporary file

                with open(summary_file_path, "a", encoding="utf-8") as file:
                    for page_num, page_text in enumerate(page_texts, start=1):
                        nested_sentences = create_nested_sentences(page_text, token_max_length=900)

                        for idx, nested in enumerate(nested_sentences):
                            concatenated_text = " ".join(nested)
                            sentences = process_text_and_display(concatenated_text, max_summary_length)

                            for i, sentence in enumerate(sentences, start=1):
                                file.write(f"  {i}. {sentence}\n")

                summary_content = read_summary_from_file(summary_file_path)

                if summary_content is not None:
                    return templates.TemplateResponse(
                        "result.html", {"request": request, "summary_content": summary_content, "success_message": "Content processed successfully"}
                    )
                    
                    # Use the summary_file_path as needed

            elif file_extension == ".docx":
                page_text = extract_text_from_docx(file_bytes)
                nested_sentences = create_nested_sentences(page_text, token_max_length=max_tokens)
                summary = ""

                for idx, nested in enumerate(nested_sentences):
                    concatenated_text = " ".join(nested)
                    sentences = process_text_and_display(concatenated_text, max_summary_length)

                    for i, sentence in enumerate(sentences, start=1):
                        summary += f"{i}. {sentence}\n"

                summary_file_path = write_summary_to_temp_file(summary)

                summary_content = read_summary_from_file(summary_file_path)

                if summary_content is not None:
                    return templates.TemplateResponse(
                        "result.html", {"request": request, "summary_content": summary_content, "success_message": "Content processed successfully"}
                    )
                else:
                    error_message = "Error reading summary from file."
                    return templates.TemplateResponse(
                        "result.html", {"request": request, "error_message": error_message}
                    )
                
                # Use the summary_file_path as needed

            elif file_extension == ".txt":
                file_encoding = chardet.detect(file_bytes)['encoding'] or 'utf-8'

                text = file_bytes.decode(file_encoding)
                nested_sentences = create_nested_sentences(text, token_max_length=max_tokens)
                summary = ""

                for idx, nested in enumerate(nested_sentences):
                    concatenated_text = " ".join(nested)
                    sentences = process_text_and_display(concatenated_text, max_summary_length)

                    for i, sentence in enumerate(sentences, start=1):
                        summary += f"{i}. {sentence}\n"

                summary_file_path = write_summary_to_temp_file(summary)

                summary_content = read_summary_from_file(summary_file_path)

                if summary_content is not None:
                    return templates.TemplateResponse(
                        "result.html", {"request": request, "summary_content": summary_content, "success_message": "Content processed successfully"}
                    )
                else:
                    error_message = "Error reading summary from file."
                    return templates.TemplateResponse(
                        "result.html", {"request": request, "error_message": error_message}
                    )
                # Use the summary_file_path as needed

        elif input_choice == "Paste Text":
            nested_sentences = create_nested_sentences(pasted_text, token_max_length=max_tokens)
            summary = ""

            for idx, nested in enumerate(nested_sentences):
                concatenated_text = " ".join(nested)
                sentences = process_text_and_display(concatenated_text, max_summary_length)

                for i, sentence in enumerate(sentences, start=1):
                    summary += f"  {i}. {sentence}\n"

            summary_file_path = write_summary_to_temp_file(summary)
            # Use the summary_file_path as needed
            # Inside the generate_summary function
            summary_content = read_summary_from_file(summary_file_path)

            if summary_content is not None:
                return templates.TemplateResponse(
                    "result.html", {"request": request, "summary_content": summary_content, "success_message": "Content processed successfully"}
                )
            else:
                error_message = "Error reading summary from file."
                return templates.TemplateResponse(
                    "result.html", {"request": request, "error_message": error_message}
                )

        
    except Exception as e:
        error_message = f"Error: {str(e)}"
        return templates.TemplateResponse(
            "result.html", {"request": request, "error_message": error_message}
        )
