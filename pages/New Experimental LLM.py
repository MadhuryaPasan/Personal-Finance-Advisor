import streamlit as st
from openai import OpenAI
from controller.database.database import *
from controller.helpers.agentClassifier import agent_responce
import time
from controller.helpers.auth import *

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="dummy_key",  # Ollama doesn't require real API key
)

if "experimental_finance_model" not in st.session_state:
    st.session_state["experimental_finance_model"] = "FinanceModelV1.6"

if "experimental_messages" not in st.session_state:
    st.session_state["experimental_messages"] = []

st.set_page_config(page_title="Personal Finance Advisor", layout="wide")

SYSTEM_MESSAGE = {
    "role": "system",
    "content": (
        "You are Personal Finance Advisor. Only answer questions about personal finance "
    ),
}

if st.user.is_logged_in:
    def render_welcome_message():
        if len(st.session_state["experimental_messages"]) == 0:
            st.subheader("💡 Experimental LLM")
            st.subheader(f"Welcome {st.user.name}!")
            st.markdown("This is an **experimental model** we're currently testing.")
            st.markdown(
                """
                I'm your *Personal Finance Advisor*, here to help you make informed financial decisions.
                """
            )
            st.warning(
                "⚠️ This model may occasionally produce inaccurate or incomplete results. "
                "If you encounter any issues, please [open a GitHub issue](https://github.com/MadhuryaPasan/Personal-Finance-Advisor/issues) to let us know. Also, this chat will not be saved in the database."
            )
            st.divider()

    render_welcome_message()

    for message in st.session_state["experimental_messages"]:
        with st.container():
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if prompt := st.chat_input("Ask a question about personal finance..."):
        # Add user message to session state
        st.session_state["experimental_messages"].append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate and display AI response
        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model=st.session_state["experimental_finance_model"],
                messages=[
                    SYSTEM_MESSAGE,
                    *[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state["experimental_messages"]
                    ],
                ],
                stream=True,
            )
            response = st.write_stream(stream)
            st.session_state["experimental_messages"].append({"role": "assistant", "content": response})

else:
    email = st.user.email
    token = generate_email_jwt(email)
    st.session_state["id_token"] = token
    st.switch_page("app.py")
    st.rerun()