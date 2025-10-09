import logging
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from controller.database.database import *

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

    def init(self):
        # Placeholder: In production, connect to SQLite DB for persistent budgets
        pass

    def set_budget(
        self,
        user_id: str,
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

            # Initialize a new session
            session = SessionLocal()

            # Create a new Budget object
            d

            # Add the new budget to the session and commit
            session.add(new_budget)
            session.commit()

            # Optional: Refresh to get the ID if needed
            session.refresh(new_budget)

            result = {
                "id": new_budget.id,
                "user_id": new_budget.user_id,
                "category": new_budget.category,
                "monthly_limit": new_budget.monthly_limit,
                "start_date": new_budget.start_date,
                "current_spent": new_budget.current_spent,
            }
            logging.info(f"Set and saved budget to DB: {result}")
            return result
        except IntegrityError:
            session.rollback()
            logging.error(
                "Failed to set budget due to integrity error (e.g., duplicate entry).")
            raise ValueError(
                "A budget for this category and user might already exist.")
        except ValueError as e:
            logging.error(f"Budget set failed: {str(e)}")
            raise
        except Exception as e:
            # Rollback in case of any other error
            session.rollback()
            logging.error(f"Budget set failed: {str(e)}")
            raise
        finally:
            # Ensure the session is closed
            if 'session' in locals() and session:
                session.close()

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
                "budget_id": budget["budget_id"],
                "category": budget["category"],
                "monthly_limit": budget["monthly_limit"],
                "start_date": budget["start_date"],
                "current_spent": current_spent,
                "remaining_budget": remaining_budget,
                "over_budget": over_budget,
                "suggestion": suggestion,
            }

            # Integrate with SavingGoalPlanner: Check goal impact (enhanced with summarizer if needed)
            # if goal:
            #     if over_budget:
            #         overspend = current_spent - budget["monthly_limit"]
            #         result["goal_impact"] = f"Over budget by {overspend:.2f}, may delay {goal['goal_name']} goal."
            #     else:
            #         result["goal_impact"] = "No negative impact on goal."

            logging.info(f"Tracked budget: {result}")
            return result
        except Exception as e:
            logging.error(f"Budget tracking failed: {str(e)}")
            raise
    
    def get_budgets(self, user_id: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieves budget data for a specific user, optionally filtered by category.
        """
        session = SessionLocal()
        try:
            query = session.query(Budget).filter(Budget.user_id == user_id)
            if category:
                query = query.filter(Budget.category == category)
            
            budgets = query.all()
            
            # Convert SQLAlchemy objects to a list of dictionaries
            result = [
                {
                    "id": b.id,
                    "user_id": b.user_id,
                    "category": b.category,
                    "monthly_limit": b.monthly_limit,
                    "current_spent": b.current_spent,
                    "start_date": b.start_date,
                }
                for b in budgets
            ]
            
            logging.info(f"Retrieved {len(result)} budgets for user {user_id}")
            return result
            
        except Exception as e:
            logging.error(f"Failed to retrieve budgets for user {user_id}: {str(e)}")
            raise
        finally:
            if 'session' in locals() and session:
                session.close()