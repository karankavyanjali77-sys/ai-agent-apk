import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def summarize_text(text: str):
    model = genai.GenerativeModel("gemini-pro")

    prompt = f"Summarize this text in 3-4 lines:\n{text}"

    response = model.generate_content(prompt)
    
    return response.text