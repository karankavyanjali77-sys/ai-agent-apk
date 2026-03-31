from fastapi import FastAPI
from pydantic import BaseModel
from agent import summarize_text

app = FastAPI()

class Request(BaseModel):
    text: str

@app.post("/summarize")
def summarize(req: Request):
    result = summarize_text(req.text)
    return {"summary": result}