# uvicorn main:app --host 0.0.0.0 --port 8000 --reload 

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pydantic import BaseModel
import bleach
import os

from Next.backend.agents.LLMAgent import LLMAgent
LLMAgent = LLMAgent()

SECRET_KEY = "HelloAPI"
ALGORITHM = "HS256"

app = FastAPI(
    title= "Personal Finance Advisor API",
    description= "this is the backend0",
    version="2.0"
)

# Input sanitization
def sanitize_input(text: str) -> str:
    return bleach.clean(text)

class LLMRequest(BaseModel):
    user_request:str

@app.post("/LLMMessage")
async def LLMMessage(request:LLMRequest):
    clean_user_request = sanitize_input(request.user_request)
    try:
        result = LLMAgent.message(clean_user_request)
        

@app.get("/health")
async def health():
    return {"status":"API is running"}