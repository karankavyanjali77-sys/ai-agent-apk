from fastapi import FastAPI
from pydantic import BaseModel
from agent import summarize_text

app = FastAPI()

class Request(BaseModel):
    text: str

@app.get("/")
def home():
    return {"message": "AI Agent Running 🚀"}

@app.post("/summarize")
def summarize(req: Request):
    result = summarize_text(req.text)
    return {"summary": result}