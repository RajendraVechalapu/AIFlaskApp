from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import fitz  # PyMuPDF
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import requests

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World, Rajendra Simhadri Appala Naidu Vechalapu! First App?"}
