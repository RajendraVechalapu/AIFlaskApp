from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
import requests

app = FastAPI()

HUGGINGFACE_API_KEY = "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"
HUGGINGFACE_SUMMARIZATION_API = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}

@app.get("/")
def get_main_page(request: Request):
    return HTMLResponse(content=open("templates/index.html").read(), status_code=200)

@app.post("/summarize")
def generate_summary(text: str = Form(...)):
    try:
        payload = {"inputs": text}
        response = requests.post(HUGGINGFACE_SUMMARIZATION_API, headers=headers, json=payload)
        if response.status_code == 200:
            summary_text = response.json()[0].get('summary_text', "")
            formatted_summary = f"{summary_text.replace('.', '.\n')}"
            return HTMLResponse(content=formatted_summary, status_code=200)
        else:
            return {"error": f"Error: Unable to summarize. Status code {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}
