import spacy
import re
import logging
from typing import Dict, Optional
from openai import OpenAI
import json

# ============================================
# Fixed Labels (DO NOT MODIFY)
# ============================================
type_labels = ["Expense", "Income"]
expense_cats = ["Food", "Transport", "Rent", "Entertainment", "Shopping", "Bills", "Other"]
income_cats = ["Salary", "Freelance", "Sale", "Investment", "Refund", "Other"]
all_categories = expense_cats + income_cats

# ============================================
# Logging Setup for Transparency & Debugging
# ============================================
logging.basicConfig(
    filename="expense_classifier.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# ============================================
# Regex for Money Extraction
# ============================================
# Matches: Rs.1000, Rs 1,000, ₹1000, $100, 1000 INR, USD 500, etc.
MONEY_PATTERN = re.compile(
    r"\b(?:rs\.?|inr|₹|\$|usd)\s?([0-9][0-9,]*(?:\.[0-9]+)?)\b",
    re.IGNORECASE
)


class ExpenseCategorizerAgent:
    """
    Two-stage categorization system:
    1. spaCy models predict type (Expense/Income) and category
    2. LLM verifies and corrects predictions if needed
    """

    def __init__(
        self,
        type_model_path: str = "../models/expense_income_type",
        cat_model_path: str = "../models/expense_income_category",
    ):
        """Load spaCy models and initialize LLM client."""
        try:
            self.nlp_type = spacy.load(type_model_path)
            self.nlp_cat = spacy.load(cat_model_path)
            logging.info(
                f"Successfully loaded models from {type_model_path} and {cat_model_path}"
            )
        except Exception as e:
            logging.error(f"Failed to load spaCy models: {str(e)}")
            raise

        # Initialize LLM client (using Ollama with Gemma)
        self.client = OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="dummy_key",
        )
        self.llm_model = "gemma3:1b"

    def extract_money(self, text: str) -> Optional[str]:
        """
        Extract monetary amount from text.
        Tries regex first, falls back to spaCy NER if needed.
        Returns cleaned number (e.g., "1000") or None.
        """
        # Attempt regex extraction
        match = MONEY_PATTERN.search(text)
        if match:
            amount = match.group(1).replace(",", "")  # Remove commas
            logging.info(f"Extracted amount '{amount}' via regex from: {text}")
            return amount

        # Fallback: Use spaCy's NER model
        try:
            ner_model = spacy.load("en_core_web_sm")
            doc = ner_model(text)
            for ent in doc.ents:
                if ent.label_ == "MONEY":
                    # Clean the amount
                    cleaned = ent.text.replace(",", "").strip()
                    logging.info(f"Extracted amount '{cleaned}' via NER from: {text}")
                    return cleaned
        except Exception as e:
            logging.warning(f"NER fallback failed: {str(e)}")

        logging.warning(f"No amount found in: {text}")
        return None

    def _validate_labels(self, type_val: str, cat_val: str) -> tuple[str, str]:
        """
        Validate that type and category are in the allowed labels.
        If not, default to safe values: "Expense" and "Other".
        """
        if type_val not in type_labels:
            logging.warning(f"Invalid type '{type_val}', defaulting to 'Expense'")
            type_val = "Expense"

        if cat_val not in all_categories:
            logging.warning(f"Invalid category '{cat_val}', defaulting to 'Other'")
            cat_val = "Other"

        return type_val, cat_val

    def _verify_with_llm(self, text: str, spacy_prediction: Dict) -> Dict:
        """
        Use LLM to verify spaCy's prediction.
        Returns corrected categorization if needed.
        """
        system_prompt = f"""
        You are a Financial Transaction Categorizer.
        Your task is to validate and, if needed, correct the provided transaction categorization.

        ALLOWED VALUES:
        - Type: {type_labels}
        - Category: {all_categories}

        You MUST respond with a valid JSON object containing the following fields:
        - "is_correct": A boolean indicating whether the provided prediction is correct.
        - "corrected_type": The correct Type (must be one of {type_labels}).
        - "corrected_category": The correct Category (must be one of {all_categories}).
        - "corrected_amount": The transaction amount as a clean number (e.g., "1000"). 
        The user may provide the amount with or without currency symbols. 
        You must extract and return only the numeric value.
        - "reason": A brief explanation of any corrections made.

        If the prediction is correct, set "is_correct" to true and return the same values for the corrected_* fields as the original prediction.

        Transaction Text: "{text}"
        Current Prediction: {json.dumps(spacy_prediction)}"""

        try:
            response = self.client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Verify this transaction: {text}"},
                ],
                temperature=0.0,
                response_format={"type": "json_object"},
            )

            # Parse LLM response
            raw_content = response.choices[0].message.content.strip()
            content = raw_content.lstrip("`").lstrip("json").lstrip("\n").rstrip("`")
            llm_result = json.loads(content)

            logging.info(
                f"LLM verification for '{text}': is_correct={llm_result.get('is_correct')}"
            )

            # Validate and sanitize the LLM output
            corrected_type, corrected_cat = self._validate_labels(
                llm_result.get("corrected_type", "Expense"),
                llm_result.get("corrected_category", "Other"),
            )

            return {
                "type": corrected_type,
                "category": corrected_cat,
                "amount": llm_result.get("corrected_amount", spacy_prediction.get("amount", "Unknown")),
                "is_correct": llm_result.get("is_correct", False),
                "was_corrected": not llm_result.get("is_correct", False),
                "reason": llm_result.get("reason", ""),
            }

        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse LLM JSON response: {str(e)}")
            return {
                "type": spacy_prediction["type"],
                "category": spacy_prediction["category"],
                "amount": spacy_prediction.get("amount", "Unknown"),
                "is_correct": True,  # Trust spaCy if LLM fails
                "was_corrected": False,
                "reason": "LLM verification failed, using spaCy prediction",
            }
        except Exception as e:
            logging.error(f"LLM verification error: {str(e)}")
            return {
                "type": spacy_prediction["type"],
                "category": spacy_prediction["category"],
                "amount": spacy_prediction.get("amount", "Unknown"),
                "is_correct": True,
                "was_corrected": False,
                "reason": "LLM verification error",
            }

    def predict_category_and_amount(self, text: str) -> Dict:
        """
        Main prediction method:
        1. spaCy predicts type and category
        2. Extract monetary amount
        3. LLM verifies and corrects if needed
        4. Return final categorization
        """
        try:
            # Step 1: Get spaCy predictions
            doc_type = self.nlp_type(text)
            predicted_type = max(doc_type.cats, key=doc_type.cats.get)

            doc_cat = self.nlp_cat(text)
            predicted_cat = max(doc_cat.cats, key=doc_cat.cats.get)

            # Validate spaCy outputs
            predicted_type, predicted_cat = self._validate_labels(predicted_type, predicted_cat)

            # Step 2: Extract amount
            amount = self.extract_money(text) or "Unknown"

            spacy_prediction = {
                "type": predicted_type,
                "category": predicted_cat,
                "amount": amount,
            }

            logging.info(f"spaCy prediction for '{text}': {spacy_prediction}")

            # Step 3: Verify with LLM and get corrections
            final_result = self._verify_with_llm(text, spacy_prediction)

            logging.info(
                f"Final result for '{text}': type={final_result['type']}, "
                f"category={final_result['category']}, corrected={final_result['was_corrected']}"
            )

            return {
                "type": final_result["type"],
                "category": final_result["category"],
                "amount": final_result["amount"]
            }

        except Exception as e:
            logging.error(f"Prediction failed for '{text}': {str(e)}")
            raise