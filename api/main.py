# uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import jwt, JWTError
from agents.ExpenseCategorizer import ExpenseCategorizerAgent
import bleach
import os

app = FastAPI(
    title="Personal Finance Advisor API",
    description="API for expense categorization using a trained spaCy model",
    version="1.0.0",
)

# Resolve model directory relative to this file (works when uvicorn imports the module)
model_dir = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "models", "expense_categorizer_v0")
)

# Use the resolved path when creating the agent
agent = ExpenseCategorizerAgent(model_path=model_dir)

# ! Secret key for JWT (store securely in production)
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

# !Dummy user database (replace with real database in production)
USERS = {"user1": "password1"}


# Pydantic model for request validation
class LoginRequest(BaseModel):
    username: str
    password: str


class ExpenseRequest(BaseModel):
    expense: str


# Security scheme for JWT
security = HTTPBearer()


# JWT authentication dependency
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("username")
        if username not in USERS:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# Input sanitization
def sanitize_input(text: str) -> str:
    return bleach.clean(text)


# Login endpoint
@app.post("/login")
async def login(request: LoginRequest):
    if USERS.get(request.username) == request.password:
        token = jwt.encode(
            {"username": request.username}, SECRET_KEY, algorithm=ALGORITHM
        )
        return {"token": token}
    raise HTTPException(status_code=401, detail="Invalid credentials")


# Prediction endpoint
@app.post("/predict")
async def predict(request: ExpenseRequest, username: str = Depends(verify_token)):
    expense_text = sanitize_input(request.expense)
    try:
        category, amount = agent.predict_category_and_amount(expense_text)
        return {"expense": expense_text, "category": category, "amount": amount}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "API is running"}
