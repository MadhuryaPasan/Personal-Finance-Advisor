import streamlit as st
from openai import OpenAI
from controller.helpers.llmTools import *

# edit code and save it
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

# Database setup
Base = declarative_base()  # <--- This line creates a base class for declarative models
# base class is used to define the structure of the database tables


class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True)
    title = Column(String, default="Untitled Chat")
    messages = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )
    # relationship() is used to define a relationship between two database tables
    # In this case, it establishes a one-to-many relationship between Conversation and Message
    # Each conversation can have multiple messages associated with it
    # back_populates is used to specify the reverse relationship from Message to Conversation
    # cascade is used to define the behavior when a Conversation is deleted
    # In this case, all associated messages will be deleted as well


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    role = Column(String)  # user or assistant
    content = Column(Text)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    conversation = relationship("Conversation", back_populates="messages")


# create sqlite DB

engine = create_engine(
    "sqlite:///chat_main_db_v1.db", connect_args={"check_same_thread": False}
)
Base.metadata.create_all(engine)  # Create tables in the database
SessionLocal = sessionmaker(
    bind=engine
)  # Create a session factory for database operations

# ollama server connection
client = OpenAI(
    base_url="http://localhost:11434/v1",  # URL of the Ollama server
    api_key="dummy_key",  # Add a dummy value
)

# Initialize session state
# st.session_state is a dictionary-like object that stores session state variables
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "is_new_chat" not in st.session_state:
    st.session_state.is_new_chat = True
if "model_name" not in st.session_state:
    st.session_state["model_name"] = "gemma3:270m"


# streamlit app page configs for set the page title
st.set_page_config(page_title="Personal Finance Advisor", layout="wide")


# rederect if not logged in
if not st.user.is_logged_in:
    st.switch_page("app.py")
    st.rerun()

# page sidebare
with st.sidebar:
    # logout btn
    if st.button("Log out", key="logout", use_container_width=True, icon="👋"):
        st.logout()
        st.rerun()
        st.switch_page("app.py")
    
    # st.title("Options")
    new_chat_disabled = st.session_state.is_new_chat
    if st.button("New Chat",icon="🗨️", disabled=new_chat_disabled, use_container_width=True):
        # if we were on an existing conv and have unsaved messages? they are saved as we go.
        st.session_state.conversation_id = None
        # ! delete this for final production
        st.markdown(f"for testing (new chat) : {st.session_state.conversation_id}")
        st.session_state.messages = []
        st.session_state.is_new_chat = True

    db = SessionLocal()
    # load conversation history
    conversationsList = db.query(Conversation).order_by(Conversation.id.desc()).all()
    # ! delete this for final production
    st.markdown(f"for testing (current chat) : {st.session_state.conversation_id}")
    if conversationsList:
        st.caption("Conversations History")
    else:
        st.caption("No conversations found. Start a new chat!")
    for conv in conversationsList:
        if st.button(conv.title, key=conv.id, use_container_width=True , type="secondary"):
            # set the selected conversation id to the session state
            st.session_state.conversation_id = conv.id
            # set the is_new_chat flag to False
            st.session_state.is_new_chat = False
            # add messages to the session state
            msgs = db.query(Message).filter_by(conversation_id=conv.id).all()
            st.session_state.messages = [
                {"role": m.role, "content": m.content} for m in msgs
            ]
            st.rerun()
    


# main area
logedInUserName = st.user.name
# st.markdown(st.user.sub)
st.markdown(st.session_state["id_token"])
# st.markdown(st.user.to_dict())
# st.markdown(st.secrets["auth"].client_id)

if len(st.session_state.messages) == 0:
    st.subheader(f"Welcome {logedInUserName}!")
    st.divider()


# If not on an existing conv, ensure a temp session for a new chat
if st.session_state.conversation_id is None:
    st.session_state.is_new_chat = True

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.markdown(message["content"])
        else:
            st.markdown(message["content"])


# give instructions to assistance
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


# user input
if prompt := st.chat_input("Ask a question about personal finance..."):
    db = SessionLocal()

    if st.session_state.conversation_id is None:
        # create a new conversation
        new_conv = Conversation(title=prompt[:50] + "...")
        db.add(new_conv)
        db.commit()
        st.session_state.conversation_id = new_conv.id
        st.session_state.is_new_chat = False

    # save user message to database
    user_msg = Message(
        role="user", content=prompt, conversation_id=st.session_state.conversation_id
    )
    db.add(user_msg)
    db.commit()

    # set the session state for the new message
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Show the user's message immediately (no manual rerun needed)
    with st.chat_message("user"):
        st.markdown(prompt)

    # * assistant response
    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model=st.session_state["model_name"],
            messages=[  # prepend system instruction to every request
                SYSTEM_MESSAGE,
                *[
                    {"role": message["role"], "content": message["content"]}
                    for message in st.session_state.messages
                ],
            ],
            stream=True,
        )
        response = st.write_stream(stream)

    # save assistant message to database
    ai_msg = Message(
        role="assistant",
        content=response,
        conversation_id=st.session_state.conversation_id,
    )
    db.add(ai_msg)
    db.commit()
    # add assistant message to session state
    st.session_state.messages.append({"role": "assistant", "content": response})
    db.close()
    # rerun the app
    # * this is to mainly refresh the sidebare every time and .etc
    st.rerun()
