"""
Database models and initialization for Personal Finance Advisor application.
"""

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
import datetime

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
    start_date = Column(String)  # Store as YYYY-MM-DD


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


class Transaction(Base):
    """
    Represents a single financial transaction (expense or income).
    """
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True, nullable=False)
    date = Column(String, default=lambda: datetime.date.today().isoformat(), nullable=False)
    description = Column(String, nullable=False)
    amount = Column(Integer, nullable=False)  # Consider Float or Numeric for production
    type = Column(String, nullable=False) # e.g., 'Expense', 'Income'
    category = Column(String, nullable=False)

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