import logging
import math
import re
import json
from typing import Dict, List, Optional, Any
import datetime as dt
from openai import OpenAI
from controller.database.database import *
from controller.helpers.savinggoalplannersummerization import summarize_transactions
# ============================================
# Logging Setup
# ============================================
logging.basicConfig(
    filename="saving_goal_planner.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Regex for extracting numeric amount (handles formats like "rs 1,000", "$500", "1000 INR")
amount_re = re.compile(r"([0-9][0-9,]*(\.[0-9]+)?)")

class SavingGoalPlannerAgent:
    """
    Agent for planning and tracking saving goals.
    Uses LLM to extract and validate goal details from user requests.
    """

    def __init__(self):
        """Initialize LLM client."""
        self.client = OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="dummy_key",
        )
        self.llm_model = "gemma3:1b"

    def _extract_goal_details_from_llm(self, user_request: str) -> Dict[str, Any]:
        """
        Use LLM to extract goal details from natural language user request.

        Returns:
            Dictionary with keys: goal_name, target_amount, deadline, current_savings
            current_savings defaults to 0 if not specified by user.
        """
        system_prompt = """You are a financial assistant that extracts saving goal details from user requests.
        
Extract and return a JSON object with these fields:
- "goal_name": The name/description of the saving goal (string)
- "target_amount": The target amount to save (float, numeric only)
- "deadline": The deadline date (string in YYYY-MM-DD format)
- "current_savings": Amount already saved (float, defaults to 0 if not mentioned)

Rules:
1. If user doesn't mention current_savings, set it to 0
2. Extract only numeric values for amounts (no currency symbols)
3. Parse dates flexibly (e.g., "next year", "in 6 months") to YYYY-MM-DD format
4. Ensure all fields are present in the response
5. Return ONLY valid JSON, no additional text"""

        try:
            response = self.client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"Extract goal details: {user_request}",
                    },
                ],
                temperature=0.0,
                response_format={"type": "json_object"},
            )

            # Parse LLM response
            raw_content = response.choices[0].message.content.strip()
            content = raw_content.lstrip("`").lstrip("json").lstrip("\n").rstrip("`")
            extracted_data = json.loads(content)

            logging.info(f"LLM extracted goal details: {extracted_data}")

            return extracted_data

        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse LLM JSON response: {str(e)}")
            raise ValueError("Failed to parse goal details from LLM response")
        except Exception as e:
            logging.error(f"LLM extraction error: {str(e)}")
            raise

    def create_goal(
        self,
        user_id: str,
        user_request: str,
    ) -> Dict[str, Any]:
        """
        Create a new saving goal from user's natural language request.

        Args:
            user_id: Unique user identifier
            user_request: Natural language description of the saving goal
                         (e.g., "I want to save 5000 for a vacation by next year")

        Returns:
            Dictionary with goal details and savings calculations
        """
        try:
            # Validate user_id
            if not user_id:
                raise ValueError("user_id is required and cannot be empty.")
            user_id = str(user_id).strip()

            # Validate user_request
            if not user_request:
                raise ValueError("user_request is required and cannot be empty.")
            user_request = str(user_request).strip()

            logging.info(
                f"Creating goal for user '{user_id}' with request: {user_request}"
            )

            # Step 1: Use LLM to extract goal details from user request
            goal_details = self._extract_goal_details_from_llm(user_request)

            # Step 2: Extract and validate fields
            goal_name = goal_details.get("goal_name", "").strip()
            if not goal_name:
                raise ValueError("goal_name could not be extracted from user request")

            try:
                target_amount = float(goal_details.get("target_amount", 0))
            except (ValueError, TypeError):
                raise ValueError(
                    f"target_amount must be a valid number, got: '{goal_details.get('target_amount')}'"
                )

            try:
                current_savings = float(goal_details.get("current_savings", 0))
            except (ValueError, TypeError):
                current_savings = 0
                logging.info("current_savings not specified, defaulting to 0")

            deadline = goal_details.get("deadline", "").strip()
            if not deadline:
                raise ValueError("deadline could not be extracted from user request")

            # Step 3: Validate values
            if target_amount <= 0:
                raise ValueError("target_amount must be greater than zero.")
            if current_savings < 0:
                raise ValueError("current_savings cannot be negative.")

            # Step 4: Parse and validate deadline
            try:
                deadline_date = dt.datetime.strptime(deadline, "%Y-%m-%d")
            except ValueError:
                raise ValueError(
                    f"deadline must be in YYYY-MM-DD format, got: '{deadline}'"
                )

            today = dt.datetime.now()
            if deadline_date <= today:
                raise ValueError("Deadline must be in the future.")

            # Step 5: Calculate savings needed
            days_to_deadline = (deadline_date - today).days
            months_to_deadline = days_to_deadline / 30  # Approximate

            remaining_amount = target_amount - current_savings
            if remaining_amount <= 0:
                monthly_savings_needed = 0
                weekly_savings_needed = 0
            else:
                monthly_savings_needed = (
                    math.ceil(remaining_amount / months_to_deadline)
                    if months_to_deadline > 0
                    else 0
                )
                weekly_savings_needed = (
                    math.ceil(remaining_amount / (days_to_deadline / 7))
                    if days_to_deadline > 0
                    else 0
                )

            # Step 6: Prepare result
            result = {
                "goal_name": goal_name,
                "target_amount": target_amount,
                "deadline": deadline,
                "current_savings": current_savings,
                "remaining_amount": remaining_amount,
                "monthly_savings_needed": monthly_savings_needed,
                "weekly_savings_needed": weekly_savings_needed,
            }

            logging.info(f"Successfully created goal: {result}")
            return result

        except ValueError as e:
            logging.error(f"Goal creation validation failed: {str(e)}")
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
            # Convert additional_savings to float
            try:
                additional_savings = float(additional_savings)
            except (ValueError, TypeError):
                raise ValueError(
                    f"additional_savings must be a valid number, got: '{additional_savings}'"
                )

            # Calculate net impact from transactions (expenses subtract, income adds)
            net_impact = 0.0
            for tx in recent_transactions:
                amount_value = tx.get("amount", "0")
                amount_str = str(amount_value)
                match = amount_re.search(amount_str)
                if match:
                    amount = float(match.group(0).replace(",", ""))
                else:
                    amount = 0.0  # Default if parsing fails
                    logging.warning(
                        f"Failed to parse amount '{amount_str}' in tx: {tx}"
                    )

                if tx.get("type") == "Expense":
                    net_impact -= amount  # Expenses reduce savings
                elif tx.get("type") == "Income":
                    net_impact += amount  # Income increases savings

            updated_savings = goal["current_savings"] + additional_savings + net_impact
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

    def get_goals(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all saving goals for a specific user.
        """
        session = SessionLocal()
        try:
            goals = (
                session.query(SavingGoal).filter(SavingGoal.user_id == user_id).all()
            )

            # Convert SQLAlchemy objects to a list of dictionaries
            result = [
                {
                    "id": g.id,
                    "user_id": g.user_id,
                    "goal_name": g.goal_name,
                    "target_amount": g.target_amount,
                    "deadline": g.deadline,
                    "current_savings": g.current_savings,
                    "monthly_savings_needed": g.monthly_savings_needed,
                    "weekly_savings_needed": g.weekly_savings_needed,
                }
                for g in goals
            ]

            logging.info(f"Retrieved {len(result)} goals for user {user_id}")
            return result

        except Exception as e:
            logging.error(f"Failed to retrieve goals for user {user_id}: {str(e)}")
            raise
        finally:
            if "session" in locals() and session:
                session.close()
