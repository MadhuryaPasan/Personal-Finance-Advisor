import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
import math
from sqlalchemy.exc import IntegrityError
from controller.database.database import SessionLocal, SavingGoal
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
        user_id: str,
        goal_name: str,
        target_amount: float,
        deadline: str,  # Format: YYYY-MM-DD
        current_savings: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Create a new saving goal and calculate required periodic savings.
        """
        session = None
        try:
            # Validate and clean inputs
            if not user_id:
                raise ValueError("user_id is required and cannot be empty.")
            user_id = str(user_id).strip()

            if not goal_name:
                raise ValueError("goal_name is required and cannot be empty.")
            goal_name = str(goal_name).strip()

            # Convert target_amount to float
            try:
                target_amount = float(target_amount)
            except (ValueError, TypeError):
                raise ValueError(f"target_amount must be a valid number, got: '{target_amount}'")

            # Convert current_savings to float
            try:
                current_savings = float(current_savings)
            except (ValueError, TypeError):
                raise ValueError(f"current_savings must be a valid number, got: '{current_savings}'")

            if target_amount <= 0:
                raise ValueError("target_amount must be greater than zero.")
            if current_savings < 0:
                raise ValueError("current_savings cannot be negative.")

            # Parse and validate deadline
            try:
                deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
            except ValueError:
                raise ValueError("deadline must be in YYYY-MM-DD format.")

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

            # Initialize database session
            session = SessionLocal()

            # Create a new SavingGoal object
            new_goal = SavingGoal(
                user_id=user_id,
                goal_name=goal_name,
                target_amount=target_amount,
                deadline=deadline,
                current_savings=current_savings,
                monthly_savings_needed=monthly_savings_needed,
                weekly_savings_needed=weekly_savings_needed,
            )

            # Add to database
            session.add(new_goal)
            session.commit()
            session.refresh(new_goal)

            result = {
                "id": new_goal.id,
                "user_id": new_goal.user_id,
                "goal_name": new_goal.goal_name,
                "target_amount": new_goal.target_amount,
                "deadline": new_goal.deadline,
                "current_savings": new_goal.current_savings,
                "remaining_amount": remaining_amount,
                "monthly_savings_needed": new_goal.monthly_savings_needed,
                "weekly_savings_needed": new_goal.weekly_savings_needed,
            }

            logging.info(f"Created and saved goal to DB: {result}")
            return result
        except IntegrityError:
            if session:
                session.rollback()
            logging.error("Failed to create goal due to integrity error.")
            raise ValueError("A goal with this name might already exist for this user.")
        except ValueError as e:
            logging.error(f"Goal creation failed: {str(e)}")
            raise
        except Exception as e:
            if session:
                session.rollback()
            logging.error(f"Goal creation failed: {str(e)}")
            raise
        finally:
            if session:
                session.close()

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
            # Convert additional_savings to float
            try:
                additional_savings = float(additional_savings)
            except (ValueError, TypeError):
                raise ValueError(f"additional_savings must be a valid number, got: '{additional_savings}'")

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
                "suggestion": summary if not on_track else "You're on track!",
            }

            logging.info(f"Tracked progress: {result}")
            return result
        except ValueError as e:
            logging.error(f"Progress tracking failed: {str(e)}")
            raise
        except Exception as e:
            logging.error(f"Progress tracking failed: {str(e)}")
            raise