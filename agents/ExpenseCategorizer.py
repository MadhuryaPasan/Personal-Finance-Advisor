import spacy
import re
import logging
from typing import Dict, Tuple

# Set up logging for Responsible AI (explainability and transparency)
logging.basicConfig(
    filename="expense_classifier.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
)

# Simple regex to detect common currency formats like: Rs.1000, Rs 1,000, ₹1000, $100, 1000 INR
money_re = re.compile(r"(?i)\b(?:rs\.?|inr|₹|\$|usd)\s?[0-9][0-9,]*(?:\.[0-9]+)?\b")


class ExpenseCategorizerAgent:
    def __init__(
        self,
        type_model_path: str = "../models/expense_income_type",
        cat_model_path: str = "../models/expense_income_category",
    ):
        """Initialize the agent with the trained spaCy models for type and category."""
        try:
            # Model for Expense/Income type
            self.nlp_type = spacy.load(type_model_path)
            self.nlp_cat = spacy.load(cat_model_path)  # Model for category
            logging.info(
                "Loaded type model from %s and category model from %s",
                type_model_path,
                cat_model_path,
            )
        except Exception as e:
            logging.error("Failed to load spaCy models: %s", str(e))
            raise

    def extract_money(self, text: str) -> str:
        """Extract monetary amount using regex or spaCy NER."""
        # Try regex first
        m = money_re.search(text)
        if m:
            logging.info(
                "Extracted amount '%s' using regex from input '%s'", m.group(0), text
            )
            return m.group(0)
        # Fallback: check spaCy NER (using a default model if available)
        try:
            ner = spacy.load("en_core_web_sm")  # Fallback NER model
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
            pass
        logging.warning("No amount found in input '%s'", text)
        return None

    def predict_category_and_amount(self, text: str) -> Dict[str, str]:
        """Predict type, category, and amount from expense text."""
        try:
            # Predict type using nlp_type
            doc_type = self.nlp_type(text)
            predicted_type = max(doc_type.cats, key=doc_type.cats.get)

            # Predict category using nlp_cat
            doc_cat = self.nlp_cat(text)
            predicted_cat = max(doc_cat.cats, key=doc_cat.cats.get)

            # Extract amount
            amount = self.extract_money(text) or "Unknown"

            # Log decision for explainability
            logging.info(
                f"Input: {text} | Type: {predicted_type} | Category: {predicted_cat} | Amount: {amount} | "
                f"Type scores: {doc_type.cats} | Category scores: {doc_cat.cats}"
            )

            return {"type": predicted_type, "category": predicted_cat, "amount": amount}
        except Exception as e:
            logging.error("Prediction failed for input '%s': %s", text, str(e))
            raise
