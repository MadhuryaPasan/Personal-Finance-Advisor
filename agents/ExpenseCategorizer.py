import spacy
import re
import logging
from typing import Tuple


# Set up logging for Responsible AI (explainability and transparency)
logging.basicConfig(
    filename="expense_classifier.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
)

# Simple regex to detect common currency formats like: Rs.1000, Rs 1,000, ₹1000, $100, 1000 INR
money_re = re.compile(r"(?i)\b(?:rs\.?|inr|₹|\$|usd)\s?[0-9][0-9,]*(?:\.[0-9]+)?\b")


class ExpenseCategorizerAgent:
    def __init__(self, model_path: str = "../models/expense_categorizer_v0"):
        """Initialize the agent with the trained spaCy model."""
        try:
            self.nlp = spacy.load(model_path)  # Load your trained model
            logging.info("Loaded trained spaCy model from %s", model_path)
        except Exception as e:
            logging.error("Failed to load spaCy model: %s", str(e))
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
        # Fallback: check spaCy NER
        doc = self.nlp(text)
        for ent in doc.ents:
            if ent.label_.upper() == "MONEY":
                logging.info(
                    "Extracted amount '%s' using NER from input '%s'", ent.text, text
                )
                return ent.text
        logging.warning("No amount found in input '%s'", text)
        return None

    def predict_category_and_amount(self, text: str) -> Tuple[str, str]:
        """Predict category and amount from expense text."""
        try:
            doc = self.nlp(text)
            category = max(
                doc.cats, key=doc.cats.get
            )  # Get highest-probability category
            amount = self.extract_money(text) or "Unknown"

            # Log decision for explainability
            logging.info(
                f"Input: {text} | Category: {category} | Amount: {amount} | "
                f"Category scores: {doc.cats}"
            )

            return (category, amount)
        except Exception as e:
            logging.error("Prediction failed for input '%s': %s", text, str(e))
            raise
