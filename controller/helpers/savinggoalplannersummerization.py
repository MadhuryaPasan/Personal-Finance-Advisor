import streamlit as st
from openai import OpenAI
from typing import List, Dict, Any, Optional

# ollama server connection
client = OpenAI(
    base_url="http://localhost:11434/v1",  # URL of the Ollama server
    api_key="dummy_key",  # Add a dummy value
)

def summarize_transactions(
    transactions: List[Dict[str, Any]], 
    goal: Optional[Dict[str, Any]] = None,
    model: str = "gemma3:1b"
) -> str:
    """
    Summarize recent transactions using Ollama LLM via OpenAI API.
    Optionally compares transactions with a saving goal for better insights.
    
    Args:
        transactions (list[dict]): List of transactions like
            [{"type": "Expense", "category": "Food", "amount": 500, "user_request": "Dinner"}, ...]
        goal (dict, optional): Goal information with keys:
            - goal_name: Name of the goal
            - target_amount: Target amount to save
            - current_savings: Current savings amount
            - updated_savings: Updated savings after transactions
            - remaining: Remaining amount to save
            - on_track: Boolean indicating if on track
            - deadline: Deadline for the goal
        model (str): Ollama model name (default = gemma3:1b)
    
    Returns:
        str: Natural language summary with goal comparison
    """
    if not transactions:
        if goal:
            return f"No recent transactions found. Your goal '{goal.get('goal_name', 'N/A')}' status remains unchanged."
        return "No recent transactions found to summarize."
    
    # Convert transactions into a readable text block
    transactions_text = "\n".join([
        f"- {t['type']} | {t['category']} | {t['amount']} | {t['user_request']}"
        for t in transactions
    ])
    
    # Build goal context if provided
    goal_context = ""
    if goal:
        goal_context = f"""
SAVING GOAL CONTEXT:
- Goal Name: {goal.get('goal_name', 'N/A')}
- Target Amount: {goal.get('target_amount', 'N/A')}
- Current Savings (before transactions): {goal.get('current_savings', 0)}
- Updated Savings (after transactions): {goal.get('updated_savings', 0)}
- Remaining to Save: {goal.get('remaining', 0)}
- On Track: {goal.get('on_track', False)}
- Deadline: {goal.get('deadline', 'N/A')}

Analyze how these transactions are impacting the goal and provide actionable advice to help the user reach their saving target."""
    
    # Build system prompt
    system_prompt = """You are a financial assistant. Analyze the transactions and provide practical suggestions.
All currency values must be represented using the ISO 4217 code LKR (Sri Lankan Rupee)
Structure your response as follows:
1. **Transaction Summary**: Brief overview of income vs expenses
2. **Impact on Goal**: How these transactions affect the saving goal (if provided)
3. **Positive Observations**: What's going well
4. **Areas to Improve**: Where spending can be optimized
5. **Actionable Tips**: Specific recommendations to improve savings and reach the goal

Be concise but insightful. Focus on the relationship between spending habits and the goal."""
    
    user_prompt = f"""Here are my recent transactions:
{transactions_text}
{goal_context}

Analyze these transactions in context of my financial situation and goal. Provide a comprehensive but concise summary."""
    
    # Ask Ollama model to summarize
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    
    return response.choices[0].message.content.strip()