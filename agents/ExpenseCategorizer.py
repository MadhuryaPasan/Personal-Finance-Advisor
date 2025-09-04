import spacy
import re
import logging
from typing import Dict, Tuple

# -------------------------------
# Logging setup for Responsible AI
# -------------------------------
# This ensures all predictions, model loading, and errors are logged for transparency and debugging.
logging.basicConfig(
    filename="expense_classifier.log",  # Log file name
    # Log level (INFO: normal ops, ERROR: failures, WARNING: anomalies)
    level=logging.INFO,
    format="%(asctime)s - %(message)s",  # Format includes timestamp + message
)

# -------------------------------
# Regex for detecting money values
# -------------------------------
# This covers common formats like: Rs.1000, Rs 1,000, ₹1000, $100, 1000 INR, USD 500
money_re = re.compile(
    r"(?i)\b(?:rs\.?|inr|₹|\$|usd)\s?[0-9][0-9,]*(?:\.[0-9]+)?\b"
)


class ExpenseCategorizerAgent:
    """
    Agent that categorizes financial text into Expense/Income type,
    predicts specific category (e.g., Food, Transport), and extracts monetary amounts.
    """

    def __init__(
        self,
        type_model_path: str = "../models/expense_income_type",
        cat_model_path: str = "../models/expense_income_category",
    ):
        """Initialize the agent with trained spaCy models for type and category."""
        try:
            # Load spaCy model for Expense/Income type classification
            self.nlp_type = spacy.load(type_model_path)

            # Load spaCy model for Category classification (Food, Travel, etc.)
            self.nlp_cat = spacy.load(cat_model_path)

            logging.info(
                "Loaded type model from %s and category model from %s",
                type_model_path,
                cat_model_path,
            )
        except Exception as e:
            # Log model loading failure and raise exception
            logging.error("Failed to load spaCy models: %s", str(e))
            raise

    def extract_money(self, text: str) -> str:
        """
        Extract monetary amount from text.
        Uses regex first, then falls back to spaCy NER if needed.
        """
        # First try regex
        m = money_re.search(text)
        if m:
            logging.info(
                "Extracted amount '%s' using regex from input '%s'", m.group(
                    0), text
            )
            return m.group(0)

        # Fallback: try spaCy’s NER model (pretrained en_core_web_sm)
        try:
            ner = spacy.load("en_core_web_sm")  # Load lightweight NER model
            doc = ner(text)
            for ent in doc.ents:
                if ent.label_.upper() == "MONEY":
                    logging.info(
                        "Extracted amount '%s' using NER from input '%s'",
                        ent.text,
                        text,
                    )
                    return ent.text
        except Exception:
            # If even fallback fails, ignore and continue
            pass

        # If no match found
        logging.warning("No amount found in input '%s'", text)
        return None

    def predict_category_and_amount(self, text: str) -> Dict[str, str]:
        """
        Predicts:
          - Type: Expense or Income
          - Category: e.g., Food, Travel, Bills
          - Amount: extracted currency value (if available)
        """
        try:
            # Predict type (Expense/Income)
            doc_type = self.nlp_type(text)
            predicted_type = max(doc_type.cats, key=doc_type.cats.get)

            # Predict category (Food, Travel, etc.)
            doc_cat = self.nlp_cat(text)
            predicted_cat = max(doc_cat.cats, key=doc_cat.cats.get)

            # Extract amount (via regex/NER)
            amount = self.extract_money(text) or "Unknown"

            # Log the entire decision for transparency (Responsible AI)
            logging.info(
                f"Input: {text} | Type: {predicted_type} | Category: {predicted_cat} | Amount: {amount} | "
                f"Type scores: {doc_type.cats} | Category scores: {doc_cat.cats}"
            )

            # Return structured prediction
            return {"type": predicted_type, "category": predicted_cat, "amount": amount}

        except Exception as e:
            # Log failure if prediction fails
            logging.error("Prediction failed for input '%s': %s", text, str(e))
            raise
