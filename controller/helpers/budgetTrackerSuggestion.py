import streamlit as st
from openai import OpenAI
from typing import Dict, List, Optional, Any  # Add this import

# ollama server connection
client = OpenAI(
    base_url="http://localhost:11434/v1",  # URL of the Ollama server
    api_key="dummy_key",  # Add a dummy value
)


def summarize_budget_suggestions(budget: Dict[str, Any], recent_transactions: List[Dict[str, Any]], goal: Optional[Dict[str, Any]] = None, model: str = "gemma3:1b") -> str:
    """
    Generate suggestions for budget tracking using Ollama LLM via OpenAI API.

    Args:
        budget (dict): The budget details like {"category": "Food", "monthly_limit": 500, "current_spent": 600, ...}
        recent_transactions (list[dict]): List of transactions filtered or relevant to the category.
        goal (optional dict): Optional saving goal for integrated suggestions.
        model (str): Ollama model name (default = gemma3:270m)

    Returns:
        str: Natural language suggestions, including summary and tips.
    """
    if not recent_transactions:
        return "No recent transactions found. Stay within your budget to meet goals."

    # Filter transactions to the specific category and expenses only (as in track_budget)
    category_transactions = [
        t for t in recent_transactions
        if t.get("category") == budget["category"] and t.get("type") == "Expense"
    ]

    if not category_transactions:
        return "No expenses in this category yet. You're on track!"

    # Convert relevant transactions into a readable text block
    transactions_text = "\n".join([
        f"- {t['type']} | {t['category']} | {t['amount']} | {t['user_request']}"
        for t in category_transactions
    ])

    # Prepare budget status text
    over_budget = budget.get(
        "current_spent", 0) > budget.get("monthly_limit", 0)
    remaining = budget.get("monthly_limit", 0) - budget.get("current_spent", 0)
    budget_text = f"Category: {budget['category']}\nMonthly Limit: {budget['monthly_limit']}\nCurrent Spent: {budget.get('current_spent', 0)}\nRemaining: {remaining}\nOver Budget: {'Yes' if over_budget else 'No'}"

    # Optional goal text
    goal_text = ""
    if goal:
        goal_text = f"\nRelated Goal: {goal['goal_name']}\nTarget: {goal.get('target_amount', 'N/A')}\nThis budget impacts your progress toward this goal."

    # Ask Ollama model to generate suggestions
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a financial assistant. Provide practical suggestions based on the budget status and transactions. Summarize in a few bullet points, include tips to improve, and consider any goal impact."},
            {"role": "user", "content": f"Budget Status:\n{budget_text}{goal_text}\n\nRecent Transactions in Category:\n{transactions_text}\n\nGenerate suggestions to stay on or get back on track."}
        ]
    )
    return response.choices[0].message.content.strip()