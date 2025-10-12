import logging
import math
import re
import json
from typing import Dict, List, Optional, Any
import datetime as dt
from sqlalchemy.exc import IntegrityError
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

    def _extract_track_progress_details_from_llm(
        self, user_request: str, available_goals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Use LLM to match goal and extract tracking details from user request.
        
        Args:
            user_request: Natural language request for tracking progress
            available_goals: List of dicts with 'id' and 'goal_name' from database
        
        Returns:
            Dictionary with keys: goal_id, additional_savings
        """
        # Format available goals for LLM
        goals_text = "\n".join([f"- ID: {g['id']}, Name: {g['goal_name']}" for g in available_goals])
        
        system_prompt = f"""You are a financial assistant that matches saving goals and extracts tracking details from user requests.

        Available goals in the database:
{goals_text}

        Extract and return a JSON object with these fields:
        - "goal_id": The ID of the most suitable matching goal (integer)
        - "additional_savings": Any new savings amount mentioned (float, defaults to 0 if not mentioned)

        Rules:
        1. Semantically match the user's goal mention to the most suitable available goal
        2. The user's goal name may be slightly different from the database goal name
        3. Return the goal_id (not the goal name) of the best match
        4. If user mentions saving, contribution, or deposit amount, extract as additional_savings
        5. Extract only numeric values for amounts (no currency symbols)
        6. If additional_savings is not mentioned, set it to 0
        7. Return ONLY valid JSON, no additional text"""

        try:
            response = self.client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"Extract tracking details: {user_request}",
                    },
                ],
                temperature=0.0,
                response_format={"type": "json_object"},
            )
            
            # Parse LLM response
            raw_content = response.choices[0].message.content.strip()
            content = raw_content.lstrip("`").lstrip("json").lstrip("\n").rstrip("`")
            extracted_data = json.loads(content)

            logging.info(f"LLM extracted tracking details: {extracted_data}")

            return extracted_data

        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse LLM JSON response: {str(e)}")
            raise ValueError("Failed to parse tracking details from LLM response")
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
            session = SessionLocal()
            new_goal = SavingGoal(
                user_id=user_id,
                goal_name=goal_name,
                target_amount=target_amount,
                deadline=deadline,
                current_savings=current_savings,
                monthly_savings_needed=monthly_savings_needed,
                weekly_savings_needed=weekly_savings_needed,
            )


            session.add(new_goal)
            session.commit()

            # Optional: Refresh to get the ID if needed
            session.refresh(new_goal)
            # Step 6: Prepare result
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

            logging.info(f"Successfully created goal: {result}")
            return result

        except IntegrityError:
            session.rollback()
            logging.error(
                "Failed to set goal due to integrity error (e.g., duplicate entry)."
            )
            raise ValueError("A goal for this already exist.")
        except ValueError as e:
            logging.error(f"Goal set failed: {str(e)}")
            raise
        except Exception as e:
            # Rollback in case of any other error
            session.rollback()
            logging.error(f"Goal set failed: {str(e)}")
            raise
        finally:
            # Ensure the session is closed
            if "session" in locals() and session:
                session.close()

    def track_progress(
        self,
        user_id: str,
        user_request: str,
        recent_transactions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Track progress, integrating transaction data to adjust savings.
        Uses LLM to semantically match goal and extract additional savings from user request.
        
        Args:
            user_id: User identifier
            user_request: Natural language request for tracking (e.g., "I saved 500 for my vacation")
            recent_transactions: List of recent transactions
        
        Returns:
            Dictionary with updated progress information
        """
        session = SessionLocal()
        try:
            # Step 1: Get all available goals for the user from database
            available_goals_db = (
                session.query(SavingGoal).filter(SavingGoal.user_id == user_id).all()
            )
            
            if not available_goals_db:
                raise ValueError(f"No saving goals found for user {user_id}")
            
            # Convert to format for LLM (ID and goal_name)
            available_goals = [
                {"id": g.id, "goal_name": g.goal_name}
                for g in available_goals_db
            ]
            
            logging.info(f"Available goals for user {user_id}: {available_goals}")
            
            # Step 2: Use LLM to match goal and extract tracking details
            tracking_details = self._extract_track_progress_details_from_llm(
                user_request, available_goals
            )
            
            goal_id = tracking_details.get("goal_id")
            if not goal_id:
                raise ValueError("Could not match any goal from user request")
            
            try:
                goal_id = int(goal_id)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid goal_id returned from LLM: {goal_id}")
            
            try:
                additional_savings = float(tracking_details.get("additional_savings", 0))
            except (ValueError, TypeError):
                additional_savings = 0
                logging.info("additional_savings not specified, defaulting to 0")
            
            # Step 3: Fetch the goal from database using goal_id
            goal = session.query(SavingGoal).filter(SavingGoal.id == goal_id).first()
            
            if not goal:
                raise ValueError(f"Goal with ID {goal_id} not found in database")
            
            if goal.user_id != user_id:
                raise ValueError(f"Goal {goal_id} does not belong to user {user_id}")
            
            logging.info(f"Matched goal: {goal.goal_name} (ID: {goal.id})")
            
            # Step 4: Calculate net impact from transactions
            net_impact = 0.0
            for tx in recent_transactions:
                amount_value = tx.get("amount", "0")
                amount_str = str(amount_value)
                match = amount_re.search(amount_str)
                if match:
                    amount = float(match.group(0).replace(",", ""))
                else:
                    amount = 0.0
                    logging.warning(
                        f"Failed to parse amount '{amount_str}' in tx: {tx}"
                    )

                if tx.get("type") == "Expense":
                    net_impact -= amount
                elif tx.get("type") == "Income":
                    net_impact += amount
            
            # Step 5: Calculate updated savings
            updated_savings = goal.current_savings + additional_savings + net_impact
            remaining = goal.target_amount - updated_savings
            
            # 90% threshold check
            on_track = remaining <= 0 or updated_savings >= goal.target_amount * 0.9
            
            # Step 6: Generate summary with goal context
            goal_info = {
                "goal_name": goal.goal_name,
                "target_amount": goal.target_amount,
                "current_savings": goal.current_savings,
                "updated_savings": updated_savings,
                "remaining": remaining,
                "on_track": on_track,
                "deadline": goal.deadline,
            }
            summary = summarize_transactions(recent_transactions, goal=goal_info)
            
            result_markdown = f"""
                \n\n
                ---
                Goal Id: {goal.id}\n
                Goal Name: {goal.goal_name}\n
                Current Savings: {goal.current_savings}\n
                Additional Savings: {additional_savings}\n
                Transaction Impact: {net_impact}\n
                Updated Savings: {updated_savings}\n
                Target Amount: {goal.target_amount}\n
                Remaining: {remaining}\n
                On Track: {on_track}\n
                \n\n
            """
            
            result = {
                "goal_id": goal.id,
                "goal_name": goal.goal_name,
                "current_savings": goal.current_savings,
                "additional_savings": additional_savings,
                "transaction_impact": net_impact,
                "updated_savings": updated_savings,
                "target_amount": goal.target_amount,
                "remaining": remaining,
                "on_track": on_track,
                "suggestion": result_markdown+"\n\n"+(summary if not on_track else "You're on track!"),
            }

            logging.info(f"Tracked progress: {result}")
            return result
            
        except ValueError as e:
            logging.error(f"Progress tracking failed: {str(e)}")
            raise
        except Exception as e:
            logging.error(f"Progress tracking failed: {str(e)}")
            raise
        finally:
            if "session" in locals() and session:
                session.close()

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
