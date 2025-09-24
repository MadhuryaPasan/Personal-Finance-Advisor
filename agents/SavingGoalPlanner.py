import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
import math
from controller.helpers.savinggoalplannersummerization import summarize_transactions


# Logging for transparency
logging.basicConfig(
    filename="saving_goal_planner.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
)

# Regex for extracting numeric amount (handles formats like "rs 1,000", "$500", "1000 INR")
amount_re = re.compile(r"([0-9][0-9,]*(\.[0-9]+)?)")


class SavingGoalPlannerAgent:
    """
    Agent for planning and tracking saving goals.
    Integrates with ExpenseCategorizer by using categorized transaction data to estimate progress.
    """

    def __init__(self):
        # Placeholder: In production, connect to SQLite DB for user-specific data
        pass

    def create_goal(
        self,
        goal_name: str,
        target_amount: float,
        deadline: str,  # Format: YYYY-MM-DD
        current_savings: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Create a new saving goal and calculate required periodic savings.
        """
        try:
            deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
            today = datetime.now()
            if deadline_date <= today:
                raise ValueError("Deadline must be in the future.")

            days_to_deadline = (deadline_date - today).days
            months_to_deadline = days_to_deadline / 30  # Approximate

            remaining_amount = target_amount - current_savings
            monthly_savings_needed = math.ceil(
                remaining_amount / months_to_deadline) if months_to_deadline > 0 else 0
            weekly_savings_needed = math.ceil(
                remaining_amount / (days_to_deadline / 7)) if days_to_deadline > 0 else 0

            result = {
                "goal_name": goal_name,
                "target_amount": target_amount,
                "deadline": deadline,
                "current_savings": current_savings,
                "remaining_amount": remaining_amount,
                "monthly_savings_needed": monthly_savings_needed,
                "weekly_savings_needed": weekly_savings_needed,
            }

            logging.info(f"Created goal: {result}")
            return result
        except ValueError as e:
            logging.error(f"Goal creation failed: {str(e)}")
            raise
        except Exception as e:
            logging.error(f"Goal creation failed: {str(e)}")
            raise

    def track_progress(
        self,
        goal: Dict[str, Any],
        # List of ExpenseCategorizer outputs
        recent_transactions: List[Dict[str, Any]],
        additional_savings: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Track progress, integrating transaction data to adjust savings.
        Example: recent_transactions = [{"type": "Expense", "category": "Transport", "amount": "rs 1000", ...}]
        """
        try:
            # Calculate net impact from transactions (expenses subtract, income adds)
            net_impact = 0.0
            for tx in recent_transactions:
                amount_str = tx.get("amount", "0")
                match = amount_re.search(amount_str)
                if match:
                    amount = float(match.group(0).replace(",", ""))
                else:
                    amount = 0.0  # Default if parsing fails
                    logging.warning(
                        f"Failed to parse amount '{amount_str}' in tx: {tx}")

                if tx.get("type") == "Expense":
                    net_impact -= amount  # Expenses reduce savings
                elif tx.get("type") == "Income":
                    net_impact += amount  # Income increases savings

            updated_savings = goal["current_savings"] + \
                additional_savings + net_impact
            remaining = goal["target_amount"] - updated_savings
            # 90% threshold
            on_track = remaining <= 0 or updated_savings >= goal["target_amount"] * 0.9

            summary = summarize_transactions(recent_transactions)

            result = {
                "goal_name": goal["goal_name"],
                "updated_savings": updated_savings,
                "remaining": remaining,
                "on_track": on_track,
                "suggestion": {summary} if not on_track else "You're on track!",
            }

            logging.info(f"Tracked progress: {result}")
            return result
        except Exception as e:
            logging.error(f"Progress tracking failed: {str(e)}")
            raise
