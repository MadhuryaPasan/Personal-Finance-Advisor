import streamlit as st
from openai import OpenAI

# ollama server connection
client = OpenAI(
    base_url="http://localhost:11434/v1",  # URL of the Ollama server
    api_key="dummy_key",  # Add a dummy value
)


# already configured in your app
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="dummy_key",
)


def summarize_transactions(transactions, model="gemma3:270m"):
    """
    Summarize recent transactions using Ollama LLM via OpenAI API.

    Args:
        transactions (list[dict]): List of transactions like
            [{"type": "Expense", "category": "Food", "amount": 500, "user_request": "Dinner"}, ...]
        model (str): Ollama model name (default = gemma3:270m)

    Returns:
        str: Natural language summary
    """
    if not transactions:
        return "No recent transactions found to summarize."

    # Convert transactions into a readable text block
    transactions_text = "\n".join([
        f"- {t['type']} | {t['category']} | {t['amount']} | {t['user_request']}"
        for t in transactions
    ])

    # Ask Ollama model to summarize
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a financial assistant. Summarize the transactions into a short, clear financial report."},
            {"role": "user", "content": f"Here are my recent transactions:\n{transactions_text}\n\nSummarize them in a few bullet points and give me a short insight."}
        ]
    )
    return response.choices[0].message.content.strip()
