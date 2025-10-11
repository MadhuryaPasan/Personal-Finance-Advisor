import logging
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from controller.database.database import *
from agents.ExpenseCategorizer import ExpenseCategorizerAgent
import os

# Resolve model directories for ExpenseCategorizer
base_dir = os.path.dirname(__file__)
type_model_dir = os.path.normpath(
    os.path.join(base_dir, "..", "models", "expense_income_type")
)
cat_model_dir = os.path.normpath(
    os.path.join(base_dir, "..", "models", "expense_income_category")
)

# Instantiate agents
expense_agent = ExpenseCategorizerAgent(
    type_model_path=type_model_dir, cat_model_path=cat_model_dir
)


# Logging for transparency
logging.basicConfig(
    filename="budget_tracker.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
)


class TransactionsAgent:
    def init(self):
        # Placeholder: In production, connect to SQLite DB for persistent budgets
        pass

    def create_transaction(
        self,
        user_id: str,
        user_request: str,
    ) -> Dict[str, Any]:
        """save transctions"""
        try:
            if not user_request:
                raise ValueError("Empty request")
            else:
                predict_results = expense_agent.predict_category_and_amount(
                    user_request
                )

                amount = 0
                session = SessionLocal()
                if predict_results["amount"] == "Unknown":
                    amount = 0
                else:
                    amount = predict_results["amount"]
                new_transaction = Transaction(
                    user_id=user_id,
                    user_request=user_request,
                    amount=amount,
                    type=predict_results["type"],
                    category=predict_results["category"],
                )
                # Add the new budget to the session and commit
                session.add(new_transaction)
                session.commit()

                result = {
                    "transactions_id": new_transaction.transactions_id,
                    "user_id": new_transaction.user_id,
                    "user_request": new_transaction.user_request,
                    "amount": new_transaction.amount,
                    "type": new_transaction.type,
                    "category": new_transaction.category,
                }

                # Optional: Refresh to get the ID if needed
                session.refresh(new_transaction)

                logging.info(f"Set and saved transactions to DB: {result}")
                return result
        except IntegrityError:
            session.rollback()
            logging.error(
                "Failed to set transaction due to integrity error (e.g., duplicate entry)."
            )
            raise ValueError("A transaction might already exist.")
        except ValueError as e:
            logging.error(f"transaction set failed: {str(e)}")
            raise
        except Exception as e:
            # Rollback in case of any other error
            session.rollback()
            logging.error(f"transaction set failed: {str(e)}")
            raise
        finally:
            # Ensure the session is closed
            if "session" in locals() and session:
                session.close()

    def get_transaction(
        self,
        user_id: str,
        type: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves budget data for a specific user, optionally filtered by category.
        """
        session = SessionLocal()
        try:
            # Start with a base query filtered by user_id
            query = session.query(Transaction).filter(Transaction.user_id == user_id)
            # Apply an optional filter for transaction_type
            if type:
                query = query.filter(Transaction.type == type)

            # Apply an optional filter for category
            if category:
                query = query.filter(Transaction.category == category)

            # Execute the query and get all results
            transactions = query.all()

            # Convert SQLAlchemy objects to a list of dictionaries
            result = [
                {
                    "transactions_id": t.transactions_id,
                    "user_id": t.user_id,
                    "date": t.date,
                    "user_request": t.user_request,
                    "amount": t.amount,
                    "type": t.type,
                    "category": t.category,
                }
                for t in transactions
            ]

            logging.info(f"Retrieved {len(result)} transactions for user {user_id}")
            return result

        except Exception as e:
            logging.error(
                f"Failed to retrieve transactions for user {user_id}: {str(e)}"
            )
            raise
        finally:
            if "session" in locals() and session:
                session.close()