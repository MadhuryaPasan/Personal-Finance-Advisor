"""
Personal Finance Advisor - Streamlit Chat Application
A conversational AI application for personal finance guidance with conversation history.
"""

import streamlit as st
from openai import OpenAI
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    ForeignKey,
    Text,
    text,
    inspect,
)
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

# ============================================================================
# DATABASE MODELS
# ============================================================================

Base = declarative_base()


class Conversation(Base):
    """
    Represents a chat conversation.

    Attributes:
        id: Primary key
        title: Conversation title (defaults to first message preview)
        user_id: ID of the user who owns this conversation
        messages: Relationship to all messages in this conversation
    """
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True)
    title = Column(String, default="Untitled Chat")
    user_id = Column(String, index=True)
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan"  # Delete messages when conversation is deleted
    )


class Message(Base):
    """
    Represents a single message in a conversation.

    Attributes:
        id: Primary key
        role: Either 'user' or 'assistant'
        content: The message text
        conversation_id: Foreign key to parent conversation
        conversation: Relationship back to the conversation
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    role = Column(String)
    content = Column(Text)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    conversation = relationship("Conversation", back_populates="messages")


class Budget(Base):
    """
    Represents a single budget entry for a user and category.
    """
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    category = Column(String, index=True, nullable=False)
    monthly_limit = Column(Integer, nullable=False)
    current_spent = Column(Integer, default=0)
    start_date = Column(String)  # Store as YYYY-MM-DD
    
    
class SavingGoal(Base):
    """
    Represents a saving goal for a user.
    """
    __tablename__ = "saving_goals"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    goal_name = Column(String, nullable=False)
    target_amount = Column(Integer, nullable=False)
    deadline = Column(String, nullable=False)  # Stored as YYYY-MM-DD
    current_savings = Column(Integer, default=0)
    monthly_savings_needed = Column(Integer, default=0)
    weekly_savings_needed = Column(Integer, default=0)

# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================


def initialize_database():
    """
    Create database engine, tables, and ensure schema is up to date.
    Handles migration for user_id column if needed.
    """
    engine = create_engine(
        "sqlite:///chat_main_db_v1.db",
        connect_args={"check_same_thread": False}
    )

    # Create all tables defined in Base
    Base.metadata.create_all(engine)

    # Migration: Ensure user_id column exists and is indexed
    try:
        inspector = inspect(engine)
        existing_columns = [
            col["name"] for col in inspector.get_columns("conversations")
        ]

        if "user_id" not in existing_columns:
            with engine.begin() as conn:
                conn.execute(
                    text("ALTER TABLE conversations ADD COLUMN user_id TEXT"))
                conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id)")
                )
    except Exception:
        pass  # Column already exists or other error

    return engine


# Initialize database and create session factory
engine = initialize_database()
SessionLocal = sessionmaker(bind=engine)


# ============================================================================
# AI CLIENT CONFIGURATION
# ============================================================================

def get_ai_client():
    """
    Initialize and return OpenAI-compatible client for Ollama server.
    """
    return OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="dummy_key"  # Ollama doesn't require real API key
    )


client = get_ai_client()


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def initialize_session_state():
    """
    Initialize all required session state variables if they don't exist.
    """
    defaults = {
        "conversation_id": None,
        "messages": [],
        "is_new_chat": True,
        "model_name": "gemma3:270m"
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


initialize_session_state()


# ============================================================================
# SYSTEM PROMPT
# ============================================================================

SYSTEM_MESSAGE = {
    "role": "system",
    "content": (
        "You are Personal Finance Advisor. Only answer questions about personal finance "
        "(budgeting, saving, spending, investing, retirement, taxes, insurance, debt, credit, "
        "financial products, and financial planning). If a request is outside of personal finance, "
        "respond: 'I can only help with personal finance topics. Please ask about budgeting, saving, "
        "investing, debt, taxes, insurance, or credit.' Keep answers concise and practical."
    ),
}


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Personal Finance Advisor",
    layout="wide"
)


# ============================================================================
# AUTHENTICATION CHECK
# ============================================================================

if not st.user.is_logged_in:
    st.switch_page("app.py")
    st.rerun()


# ============================================================================
# SIDEBAR - USER CONTROLS & CONVERSATION HISTORY
# ============================================================================

def render_sidebar():
    """
    Render sidebar with logout, new chat button, and conversation history.
    """
    with st.sidebar:
        # Logout button
        if st.button("Log out", key="logout", use_container_width=True, icon="👋"):
            reset_session_state()
            st.logout()
            st.switch_page("app.py")
            st.rerun()

        # New chat button (disabled if already on new chat)
        new_chat_disabled = st.session_state.is_new_chat
        if st.button(
            "New Chat",
            icon="🗨️",
            disabled=new_chat_disabled,
            use_container_width=True
        ):
            reset_session_state()
            # Debug info - remove in production
            st.markdown(
                f"for testing (new chat): {st.session_state.conversation_id}")

        # Load and display conversation history
        render_conversation_history()


def reset_session_state():
    """
    Reset session state to start a new chat.
    """
    st.session_state.conversation_id = None
    st.session_state.messages = []
    st.session_state.is_new_chat = True


def render_conversation_history():
    """
    Load and display all conversations for the current user.
    """
    db = SessionLocal()

    try:
        conversations = (
            db.query(Conversation)
            .filter_by(user_id=st.user.sub)
            .order_by(Conversation.id.desc())
            .all()
        )

        # Debug info - remove in production
        # st.markdown(f"for testing (current chat): {st.session_state.conversation_id}")

        # Display header
        if conversations:
            st.caption("Conversations History")
        else:
            st.caption("No conversations found. Start a new chat!")

        # Render conversation buttons
        for conv in conversations:
            if st.button(
                conv.title,
                key=conv.id,
                use_container_width=True,
                type="secondary"
            ):
                load_conversation(conv, db)
    finally:
        db.close()


def load_conversation(conv, db):
    """
    Load a selected conversation into the current session.

    Args:
        conv: Conversation object to load
        db: Database session
    """
    if conv.user_id == st.user.sub:
        st.session_state.conversation_id = conv.id
        st.session_state.is_new_chat = False

        # Load all messages from the conversation
        messages = db.query(Message).filter_by(conversation_id=conv.id).all()
        st.session_state.messages = [
            {"role": msg.role, "content": msg.content} for msg in messages
        ]
        st.rerun()
    else:
        st.warning("You do not have access to this conversation.")


render_sidebar()


# ============================================================================
# MAIN CHAT INTERFACE
# ============================================================================

def render_welcome_message():
    """
    Display welcome message for new chats.
    """
    if len(st.session_state.messages) == 0:
        st.subheader(f"Welcome {st.user.name}!")
        st.markdown(
            """I'm your **Personal Finance Advisor**, here to help you make informed financial decisions.""")
        st.divider()


def render_chat_history():
    """
    Display all messages in the current conversation.
    """
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def create_new_conversation(prompt, db):
    """
    Create a new conversation in the database.

    Args:
        prompt: First user message (used to generate title)
        db: Database session

    Returns:
        ID of the newly created conversation
    """
    new_conv = Conversation(
        title=prompt[:50] + "...",  # Use first 50 chars as title
        user_id=st.user.sub
    )
    db.add(new_conv)
    db.commit()

    st.session_state.conversation_id = new_conv.id
    st.session_state.is_new_chat = False

    return new_conv.id


def save_message(role, content, conversation_id, db):
    """
    Save a message to the database.

    Args:
        role: 'user' or 'assistant'
        content: Message text
        conversation_id: ID of the conversation
        db: Database session
    """
    message = Message(
        role=role,
        content=content,
        conversation_id=conversation_id
    )
    db.add(message)
    db.commit()


def get_ai_response(user_prompt):
    """
    Get streaming response from AI model.

    Args:
        user_prompt: User's message

    Returns:
        AI response text
    """
    stream = client.chat.completions.create(
        model=st.session_state["model_name"],
        messages=[
            SYSTEM_MESSAGE,
            *[
                {"role": msg["role"], "content": msg["content"]}
                for msg in st.session_state.messages
            ],
        ],
        stream=True,
    )
    return st.write_stream(stream)


def handle_user_input(prompt):
    """
    Process user input, generate AI response, and save to database.

    Args:
        prompt: User's input message
    """
    db = SessionLocal()

    try:
        # Create new conversation if needed
        if st.session_state.conversation_id is None:
            create_new_conversation(prompt, db)

        # Save user message to database
        save_message("user", prompt, st.session_state.conversation_id, db)

        # Add to session state
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate and display AI response
        with st.chat_message("assistant"):
            response = get_ai_response(prompt)

        # Save assistant message
        save_message("assistant", response,
                     st.session_state.conversation_id, db)
        st.session_state.messages.append(
            {"role": "assistant", "content": response})

    finally:
        db.close()

    # Refresh UI to update sidebar
    st.rerun()


# ============================================================================
# RENDER MAIN INTERFACE
# ============================================================================

render_welcome_message()

# Ensure we're ready for a new chat if no conversation is selected
if st.session_state.conversation_id is None:
    st.session_state.is_new_chat = True

render_chat_history()

# Chat input
if prompt := st.chat_input("Ask a question about personal finance..."):
    handle_user_input(prompt)
