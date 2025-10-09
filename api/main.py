
# uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import jwt, JWTError
from typing import Dict, List, Any, Optional
import bleach
import os

from agents.ExpenseCategorizer import ExpenseCategorizerAgent
from agents.SavingGoalPlanner import SavingGoalPlannerAgent
from agents.BudgetTracker import BudgetTrackerAgent

app = FastAPI(
    title="Personal Finance Advisor API",
    description="API for personal finance agents: expense categorization, saving goal planning, and budget tracking",
    version="1.0.0",
)

# Resolve model directories for ExpenseCategorizer
base_dir = os.path.dirname(__file__)
type_model_dir = os.path.normpath(os.path.join(base_dir, "..", "models", "expense_income_type"))
cat_model_dir = os.path.normpath(os.path.join(base_dir, "..", "models", "expense_income_category"))

# Instantiate agents
expense_agent = ExpenseCategorizerAgent(type_model_path=type_model_dir, cat_model_path=cat_model_dir)
saving_agent = SavingGoalPlannerAgent()
budget_agent = BudgetTrackerAgent()

# JWT configuration (must match auth.py)
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

# Security scheme for JWT
security = HTTPBearer()

# JWT authentication dependency
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("username")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token: no username")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# Input sanitization
def sanitize_input(text: str) -> str:
    return bleach.clean(text)

# Pydantic model for ExpenseCategorizer
class TransactionRequest(BaseModel):
    transaction: str

# Pydantic models for SavingGoalPlanner
class GoalCreateRequest(BaseModel):
    user_id:str
    goal_name: str
    target_amount: float
    deadline: str  # YYYY-MM-DD
    current_savings: Optional[float] = 0.0

class GoalTrackRequest(BaseModel):
    goal: Dict[str, Any]
    recent_transactions: List[Dict[str, Any]]  # From ExpenseCategorizer
    additional_savings: Optional[float] = 0.0

# Pydantic models for BudgetTracker
class BudgetSetRequest(BaseModel):
    user_id:str
    category: str
    monthly_limit: float
    start_date: Optional[str] = None  # YYYY-MM-01

class BudgetTrackRequest(BaseModel):
    budget: Dict[str, Any]
    recent_transactions: List[Dict[str, Any]]  # From ExpenseCategorizer
    goal: Optional[Dict[str, Any]] = None  # From SavingGoalPlanner

# ExpenseCategorizer endpoint
@app.post("/predict")
async def predict(request: TransactionRequest, username: str = Depends(verify_token)):
    transaction_text = sanitize_input(request.transaction)
    try:
        result = expense_agent.predict_category_and_amount(transaction_text)
        return {**result, "user_request": transaction_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

# SavingGoalPlanner endpoints
@app.post("/create_goal")
async def create_goal(request: GoalCreateRequest, username: str = Depends(verify_token)):
    try:
        # TODO: Store in DB with user_id = username (st.user.sub)
        result = saving_agent.create_goal(
            request.user_id,
            request.goal_name,
            request.target_amount,
            request.deadline,
            request.current_savings
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Goal creation failed: {str(e)}")

@app.post("/track_goal")
async def track_goal(request: GoalTrackRequest, username: str = Depends(verify_token)):
    try:
        # TODO: Validate goal belongs to user via DB
        result = saving_agent.track_progress(
            request.goal,
            request.recent_transactions,
            request.additional_savings
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Goal tracking failed: {str(e)}")

# BudgetTracker endpoints
@app.post("/set_budget")
async def set_budget(request: BudgetSetRequest, username: str = Depends(verify_token)):
    try:
        # TODO: Store in DB with user_id = username (st.user.sub)
        result = budget_agent.set_budget(
            request.user_id,
            request.category,
            request.monthly_limit,
            request.start_date
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Budget set failed: {str(e)}")

@app.post("/track_budget")
async def track_budget(request: BudgetTrackRequest, username: str = Depends(verify_token)):
    try:
        # TODO: Validate budget and goal belong to user via DB
        result = budget_agent.track_budget(
            request.budget,
            request.recent_transactions,
            request.goal
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Budget tracking failed: {str(e)}")

# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "API is running"}