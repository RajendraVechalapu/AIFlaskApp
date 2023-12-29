from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import fitz  # PyMuPDF
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import requests

app = FastAPI()

# Enable CORS (customize origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup templates
templates = Jinja2Templates(directory="templates")

HUGGINGFACE_API_KEY = "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"  # Replace with your key
HUGGINGFACE_SUMMARIZATION_API = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}

class ChatPDF:
    def __init__(self):
        pass

    def process_message(self, messages: list) -> dict:
        return {"messages": messages, "summaries": self.generate_summaries(messages)}

    def generate_summaries(self, messages: list) -> list:
        summaries = []
        for message in messages:
            summary = self.request_summarization_api(message)
            summaries.append(summary)
        return summaries

    def request_summarization_api(self, text: str) -> str:
        payload = {"text": text}
        response = requests.post(HUGGINGFACE_SUMMARIZATION_API, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json().get("summary", "")
        else:
            return f"Error: Unable to summarize. Status code {response.status_code}"

chat_pdf_instance = ChatPDF()

@app.get("/")
async def upload_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "zip": zip})  # Change zip to your actual data

@app.post("/chatpdf")
async def chatpdf(file: UploadFile = File(...), message: Optional[str] = None):
    if not file.filename.lower().endswith((".pdf")):
        return HTMLResponse(content="<h3>Error: Invalid file format. Must be a PDF.</h3>", status_code=400)

    pdf_data = await file.read()
    messages = extract_text_from_pdf(pdf_data)
    response_dict = {"pages": []}

    for i, message in enumerate(messages, start=1):
        page_response = chat_pdf_instance.process_message([message])
        response_dict["pages"].append({
            "page_number": i,
            "text": message,
            "summary": page_response["summaries"][0]
        })

    return HTMLResponse(content=render_response(response_dict), status_code=200)

def render_response(response_dict: dict) -> str:
    pages = response_dict["pages"]
    html_content = "<h3>Response:</h3>\n"
    for page in pages:
        html_content += f"<h2>Page {page['page_number']}:</h2>\n"
        html_content += f"<p>{page['text']}</p>\n"
        html_content += f"<h3>Summary:</h3>\n"
        html_content += f"<p>{page['summary']}</p>\n"
    return html_content

def extract_text_from_pdf(pdf_data: bytes) -> list:
    pdf_document = fitz.Document(stream=pdf_data, filetype="pdf")
    messages = []
    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        messages.append(page.get_text())
    return messages

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
