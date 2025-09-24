import logging
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import the new helper
from controller.helpers.budgetTrackerSuggestion import summarize_budget_suggestions

# Logging for transparency
logging.basicConfig(
    filename="budget_tracker.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
)

# Regex for extracting numeric amount (handles "rs 1,000", "$500", etc.)
amount_re = re.compile(r"([0-9][0-9,]*(\.[0-9]+)?)")


class BudgetTrackerAgent:
    """
    Agent for setting and tracking budgets per category.
    Integrates with ExpenseCategorizer (sums expenses) and SavingGoalPlanner (checks impact on goals).
    """

    def _init_(self):
        # Placeholder: In production, connect to SQLite DB for persistent budgets
        pass

    def set_budget(
        self,
        category: str,
        monthly_limit: float,
        start_date: str = None,  # Default to current month start
    ) -> Dict[str, Any]:
        """
        Set a monthly budget for a category.
        """
        try:
            if monthly_limit < 0:
                raise ValueError("Monthly limit must be non-negative.")
            if start_date is None:
                start_date = datetime.now().strftime("%Y-%m-01")  # First of current month

            result = {
                "category": category,
                "monthly_limit": monthly_limit,
                "start_date": start_date,
                "current_spent": 0.0,  # Initial
            }
            logging.info(f"Set budget: {result}")
            return result
        except ValueError as e:
            logging.error(f"Budget set failed: {str(e)}")
            raise
        except Exception as e:
            logging.error(f"Budget set failed: {str(e)}")
            raise

    def track_budget(
        self,
        budget: Dict[str, Any],
        recent_transactions: List[Dict[str, Any]],  # From ExpenseCategorizer
        # Optional: From SavingGoalPlanner
        goal: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Track spending against budget, integrating transactions and optional goal check.
        Example: recent_transactions = [{"type": "Expense", "category": "Transport", "amount": "rs 1000", ...}]
        """
        try:
            current_spent = 0.0
            for tx in recent_transactions:
                if tx.get("category") == budget["category"] and tx.get("type") == "Expense":
                    amount_str = tx.get("amount", "0")
                    match = amount_re.search(amount_str)
                    if match:
                        amount = float(match.group(0).replace(",", ""))
                        current_spent += amount
                    else:
                        logging.warning(
                            f"Failed to parse amount '{amount_str}' in tx: {tx}")

            over_budget = current_spent > budget["monthly_limit"]
            remaining_budget = budget["monthly_limit"] - current_spent

            # Update budget dict temporarily for summarizer (to include current_spent)
            budget_with_spent = {**budget, "current_spent": current_spent}

            # Generate dynamic suggestions using the helper
            suggestion = summarize_budget_suggestions(
                budget_with_spent, recent_transactions, goal)

            result = {
                "category": budget["category"],
                "monthly_limit": budget["monthly_limit"],
                "start_date": budget["start_date"],
                "current_spent": current_spent,
                "remaining_budget": remaining_budget,
                "over_budget": over_budget,
                "suggestion": suggestion,
            }

            # Integrate with SavingGoalPlanner: Check goal impact (enhanced with summarizer if needed)
            if goal:
                if over_budget:
                    overspend = current_spent - budget["monthly_limit"]
                    result["goal_impact"] = f"Over budget by {overspend:.2f}, may delay {goal['goal_name']} goal."
                else:
                    result["goal_impact"] = "No negative impact on goal."

            logging.info(f"Tracked budget: {result}")
            return result
        except Exception as e:
            logging.error(f"Budget tracking failed: {str(e)}")
            raise