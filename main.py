from fastapi import FastAPI
import requests

app = FastAPI()

HUGGINGFACE_API_KEY = "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"
HUGGINGFACE_SUMMARIZATION_API = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}

@app.get("/")
def generate_summary():
    try:
        payload = {
            "inputs": "wonderful",
        }
        response = requests.post(HUGGINGFACE_SUMMARIZATION_API, headers=headers, json=payload)
        if response.status_code == 200 and isinstance(response.json(), list) and response.json():
            summary = response.json()[0].get('summary_text', "")
            
            # Replace escaped double quotes with regular quotes
            summary = summary.replace('\\"', '"')
            
            # Format as bullet points without outer braces
            formatted_response = f'1. {summary.replace(".", ".\n2. ")}'
            return formatted_response
        else:
            return {"error": f"Error: Unable to summarize. Status code {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}
