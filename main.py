from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
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

class ChatSummarizer:
    def __init__(self):
        pass

    def generate_summary(self, text: str) -> str:
        payload = {"text": text}
        response = requests.post(HUGGINGFACE_SUMMARIZATION_API, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json().get("summary", "")
        else:
            return f"Error: Unable to summarize. Status code {response.status_code}"

chat_summarizer = ChatSummarizer()

@app.get("/")
async def upload_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate_summary")
async def generate_summary(text: str = Form(...)):
    summary = chat_summarizer.generate_summary(text)
    return {"text": text, "summary": summary}
