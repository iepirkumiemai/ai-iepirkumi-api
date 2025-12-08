# ai_comparison.py

import os
from openai import OpenAI


class AIComparisonEngine:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError("OPENAI_API_KEY is missing!")

        # Pareizi! Jaunajai OpenAI bibliotēkai nedrīkst dot 'proxies'
        self.client = OpenAI(api_key=api_key)

    # Vienkārša testa funkcija
    def test(self):
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Hello, test successful?"}
            ]
        )
        return response.choices[0].message["content"]

    # Galvenais salīdzināšanas modulis
    def compare(self, tender_rules_text, candidate_text):
        prompt = f"""
You are an AI expert for procurement document analysis.
Compare candidate submission with tender rules.

Tender rules:
{tender_rules_text}

Candidate submission:
{candidate_text}

Return structured JSON with fields:
- compliance: percentage
- strengths: list
- weaknesses: list
- missing_documents: list
- final_score: 0-100
"""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You analyze tender documents."},
                {"role": "user", "content": prompt}
            ]
        )

        return response.choices[0].message["content"]
