import streamlit as st
from openai import OpenAI
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text, Float, inspect
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
import requests

# API base URL (adjust if deployed)
API_BASE_URL = "http://localhost:8000"

# Database setup
Base = declarative_base()

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True)
    title = Column(String, default="Untitled Chat")
    user_id = Column(String, index=True)
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    role = Column(String)  # user or assistant
    content = Column(Text)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    conversation = relationship("Conversation", back_populates="messages")

# New tables for agents' data persistence
class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    type = Column(String)  # Expense/Income
    category = Column(String)
    amount = Column(String)  # e.g., "rs 1000"
    request = Column(Text)  # Original user input
    timestamp = Column(String, default=lambda: datetime.now().isoformat())

class SavingGoal(Base):
    __tablename__ = "saving_goals"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    goal_name = Column(String)
    target_amount = Column(Float)
    deadline = Column(String)
    current_savings = Column(Float, default=0.0)
    remaining_amount = Column(Float)
    monthly_savings_needed = Column(Float)
    weekly_savings_needed = Column(Float)

class Budget(Base):
    __tablename__ = "budgets"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    category = Column(String)
    monthly_limit = Column(Float)
    start_date = Column(String)
    current_spent = Column(Float, default=0.0)

# Create SQLite DB
engine = create_engine("sqlite:///chat_main_db_v1.db", connect_args={"check_same_thread": False})
Base.metadata.create_all(engine)  # Create all tables

# Ensure user_id column exists (as in original)
inspector = inspect(engine)
existing_columns = [col["name"] for col in inspector.get_columns("conversations")]
if "user_id" not in existing_columns:
    with engine.begin() as conn:
        conn.execute("ALTER TABLE conversations ADD COLUMN user_id TEXT")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id)")

SessionLocal = sessionmaker(bind=engine)

# Ollama connection (as in original)
client = OpenAI(base_url="http://localhost:11434/v1", api_key="dummy_key")

# Initialize session state
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "is_new_chat" not in st.session_state:
    st.session_state.is_new_chat = True
if "model_name" not in st.session_state:
    st.session_state["model_name"] = "gemma3:1b"

# Streamlit page config
st.set_page_config(page_title="Personal Finance Advisor", layout="wide")

# Redirect if not logged in
if not st.user.is_logged_in:
    st.switch_page("app.py")
    st.rerun()

# Sidebar
with st.sidebar:
    if st.button("Log out", key="logout", use_container_width=True):
        st.session_state.conversation_id = None
        st.session_state.messages = []
        st.session_state.is_new_chat = True
        st.logout()
        st.rerun()
        st.switch_page("app.py")

    new_chat_disabled = st.session_state.is_new_chat
    if st.button("New Chat", disabled=new_chat_disabled, use_container_width=True):
        st.session_state.conversation_id = None
        st.session_state.messages = []
        st.session_state.is_new_chat = True

    db = SessionLocal()
    conversationsList = db.query(Conversation).filter_by(user_id=st.user.sub).order_by(Conversation.id.desc()).all()
    if conversationsList:
        st.caption("Conversations History")
    else:
        st.caption("No conversations found. Start a new chat!")
    for conv in conversationsList:
        if st.button(conv.title, key=conv.id, use_container_width=True, type="secondary"):
            if conv.user_id == st.user.sub:
                st.session_state.conversation_id = conv.id
                st.session_state.is_new_chat = False
                msgs = db.query(Message).filter_by(conversation_id=conv.id).all()
                st.session_state.messages = [{"role": m.role, "content": m.content} for m in msgs]
                st.rerun()
            else:
                st.warning("You do not have access to this conversation.")

# Main area
st.markdown(st.user.sub)
logedInUserName = st.user.name

if len(st.session_state.messages) == 0:
    st.subheader(f"Welcome {logedInUserName}!")
    st.divider()

if st.session_state.conversation_id is None:
    st.session_state.is_new_chat = True

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# System message with dates
today_date = datetime.now().strftime("%Y-%m-%d")
yesterday_date = (datetime.now() - timedelta(days=1)).strftime("%A, %B %d, %Y")
tomorrow_date = (datetime.now() + timedelta(days=1)).strftime("%A, %B %d, %Y")
SYSTEM_MESSAGE = {
    "role": "system",
    "content": (
        f"You are a Personal Finance Advisor. The current date is {today_date}.  "
        f"Yesterday was {yesterday_date}. "
        f"Tomorrow will be {tomorrow_date}. "
        "Only answer questions about personal finance (budgeting, saving, spending, "
        "investing, retirement, taxes, insurance, debt, credit, financial products, "
        "and financial planning). If a request is outside of personal finance, "
        "respond: 'I can only help with personal finance topics. Please ask about budgeting, saving, "
        "investing, debt, taxes, insurance, or credit.' Keep answers concise and practical."
    ),
}

# User input and agent routing
if prompt := st.chat_input("Ask a question about personal finance..."):
    db = SessionLocal()

    if st.session_state.conversation_id is None:
        new_conv = Conversation(title=prompt[:50] + "...", user_id=st.user.sub)
        db.add(new_conv)
        db.commit()
        st.session_state.conversation_id = new_conv.id
        st.session_state.is_new_chat = False

    # Save user message
    user_msg = Message(role="user", content=prompt, conversation_id=st.session_state.conversation_id)
    db.add(user_msg)
    db.commit()
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    # Headers for API calls
    headers = {"Authorization": f"Bearer {st.session_state['id_token']}"}

    response_content = ""

    # Route to agents based on prompt (simple keyword detection; enhance with LLM later)
    if "categorize" in prompt.lower() or "expense" in prompt.lower() or "income" in prompt.lower():
        # Call ExpenseCategorizer API
        api_response = requests.post(f"{API_BASE_URL}/predict", json={"transaction": prompt}, headers=headers)
        if api_response.status_code == 200:
            tx_data = api_response.json()
            # Save to DB
            new_tx = Transaction(
                user_id=st.user.sub,
                type=tx_data["type"],
                category=tx_data["category"],
                amount=tx_data["amount"],
                request=tx_data["user_request"]
            )
            db.add(new_tx)
            db.commit()
            response_content = f"Categorized: Type={tx_data['type']}, Category={tx_data['category']}, Amount={tx_data['amount']}"
        else:
            response_content = "Failed to categorize transaction."

    elif "saving goal" in prompt.lower() or "plan saving" in prompt.lower():
        # Example parsing (enhance as needed); assume prompt like "Plan saving 5000 for vacation by 2026-01-01 starting with 1000"
        parts = prompt.split()
        try:
            target_amount = float(parts[2])
            goal_name = parts[4]
            deadline = parts[6]
            current_savings = float(parts[-1]) if "starting with" in prompt else 0.0
            api_response = requests.post(f"{API_BASE_URL}/create_goal", json={
                "goal_name": goal_name,
                "target_amount": target_amount,
                "deadline": deadline,
                "current_savings": current_savings
            }, headers=headers)
            if api_response.status_code == 200:
                goal_data = api_response.json()
                # Save to DB
                new_goal = SavingGoal(
                    user_id=st.user.sub,
                    goal_name=goal_data["goal_name"],
                    target_amount=goal_data["target_amount"],
                    deadline=goal_data["deadline"],
                    current_savings=goal_data["current_savings"],
                    remaining_amount=goal_data["remaining_amount"],
                    monthly_savings_needed=goal_data["monthly_savings_needed"],
                    weekly_savings_needed=goal_data["weekly_savings_needed"]
                )
                db.add(new_goal)
                db.commit()
                response_content = f"Goal created: {goal_data}"
            else:
                response_content = "Failed to create saving goal."
        except:
            response_content = "Invalid format for saving goal. Example: 'Plan saving 5000 for vacation by 2026-01-01'"

    elif "budget" in prompt.lower():
        # Example: "Set budget for Transport 500 starting 2025-09-01"
        parts = prompt.split()
        try:
            category = parts[3]
            monthly_limit = float(parts[4])
            start_date = parts[6] if "starting" in prompt else None
            api_response = requests.post(f"{API_BASE_URL}/set_budget", json={
                "category": category,
                "monthly_limit": monthly_limit,
                "start_date": start_date
            }, headers=headers)
            if api_response.status_code == 200:
                budget_data = api_response.json()
                # Save to DB
                new_budget = Budget(
                    user_id=st.user.sub,
                    category=budget_data["category"],
                    monthly_limit=budget_data["monthly_limit"],
                    start_date=budget_data["start_date"],
                    current_spent=budget_data["current_spent"]
                )
                db.add(new_budget)
                db.commit()
                response_content = f"Budget set: {budget_data}"
            else:
                response_content = "Failed to set budget."
        except:
            response_content = "Invalid format for budget. Example: 'Set budget for Transport 500'"

    elif "track goal" in prompt.lower() or "progress" in prompt.lower():
        # Fetch recent transactions and latest goal from DB
        recent_txs = [{"type": t.type, "category": t.category, "amount": t.amount, "user_request": t.request} for t in db.query(Transaction).filter_by(user_id=st.user.sub).order_by(Transaction.id.desc()).limit(10).all()]
        latest_goal = db.query(SavingGoal).filter_by(user_id=st.user.sub).order_by(SavingGoal.id.desc()).first()
        if latest_goal:
            goal_dict = {
                "goal_name": latest_goal.goal_name,
                "target_amount": latest_goal.target_amount,
                "deadline": latest_goal.deadline,
                "current_savings": latest_goal.current_savings,
                "remaining_amount": latest_goal.remaining_amount,
                "monthly_savings_needed": latest_goal.monthly_savings_needed,
                "weekly_savings_needed": latest_goal.weekly_savings_needed
            }
            api_response = requests.post(f"{API_BASE_URL}/track_goal", json={
                "goal": goal_dict,
                "recent_transactions": recent_txs,
                "additional_savings": 0.0
            }, headers=headers)
            if api_response.status_code == 200:
                track_data = api_response.json()
                response_content = f"Goal progress: {track_data}"
            else:
                response_content = "Failed to track goal."
        else:
            response_content = "No saving goal found."

    elif "track budget" in prompt.lower():
        # Fetch recent transactions and latest budget from DB
        recent_txs = [{"type": t.type, "category": t.category, "amount": t.amount, "user_request": t.request} for t in db.query(Transaction).filter_by(user_id=st.user.sub).order_by(Transaction.id.desc()).limit(10).all()]
        latest_budget = db.query(Budget).filter_by(user_id=st.user.sub).order_by(Budget.id.desc()).first()
        latest_goal = db.query(SavingGoal).filter_by(user_id=st.user.sub).order_by(SavingGoal.id.desc()).first()
        if latest_budget:
            budget_dict = {
                "category": latest_budget.category,
                "monthly_limit": latest_budget.monthly_limit,
                "start_date": latest_budget.start_date,
                "current_spent": latest_budget.current_spent
            }
            goal_dict = {
                "goal_name": latest_goal.goal_name,
                "target_amount": latest_goal.target_amount
            } if latest_goal else None
            api_response = requests.post(f"{API_BASE_URL}/track_budget", json={
                "budget": budget_dict,
                "recent_transactions": recent_txs,
                "goal": goal_dict
            }, headers=headers)
            if api_response.status_code == 200:
                track_data = api_response.json()
                # Update DB with new current_spent
                latest_budget.current_spent = track_data["current_spent"]
                db.commit()
                response_content = f"Budget progress: {track_data}"
            else:
                response_content = "Failed to track budget."
        else:
            response_content = "No budget found."

    else:
        # Fall back to Ollama for general queries
        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model=st.session_state["model_name"],
                messages=[SYSTEM_MESSAGE] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                stream=True,
            )
            response = st.write_stream(stream)
        response_content = response

    # Save assistant response
    ai_msg = Message(role="assistant", content=response_content, conversation_id=st.session_state.conversation_id)
    db.add(ai_msg)
    db.commit()
    st.session_state.messages.append({"role": "assistant", "content": response_content})
    db.close()
    st.rerun()