from fastapi import FastAPI
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Anime AI Backend is running!"}

@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    # TODO: Integrate Groq API here
    return {"response": f"Echo: {request.message} (AI integration pending)"}
