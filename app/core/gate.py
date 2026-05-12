import json
import re
from pathlib import Path
from typing import Dict, Any
from llm import get_llm
from app.core.metrics_filter import load_metrics, filter_relevant_metrics

class GateChecker:
    def __init__(self, metrics_path: str):
        self.metrics_path = Path(metrics_path)
        self.all_metrics = load_metrics(self.metrics_path)
        self.llm = get_llm()

    def check_query(self, query: str) -> Dict[str, Any]:
        """
        Check if the query meets the required parameters based on the metric registry.
        Returns a dictionary: {"status": "PASS" | "INCOMPLETE", "message": "..."}
        """
        if not self.all_metrics:
            return {"status": "PASS"}

        relevant = filter_relevant_metrics(query, self.all_metrics)
        if not relevant:
            return {"status": "PASS"}

        metrics_str = json.dumps(relevant, ensure_ascii=False, indent=2)
        
        prompt = f"""
You are a Data Request Gatekeeper. Your job is to check if the user's query contains all the required parameters based on the predefined metrics dictionary.

Metrics Dictionary:
{metrics_str}

User Query: "{query}"

Instructions:
1. Determine if the user's query relates to any of the metrics in the dictionary.
2. If it relates to a metric, check if the query explicitly contains all the "required_parameters".
3. If parameters are missing (e.g., date range is required but missing), return status "INCOMPLETE" and write a polite "message" asking the user for the missing information.
4. If no parameters are missing, or if the query doesn't match any strict metrics, return status "PASS".
5. IMPORTANT: Output ONLY valid JSON in the following format:
{{
  "status": "PASS" | "INCOMPLETE",
  "message": "Reason or question to the user if INCOMPLETE"
}}
"""
        try:
            response = self.llm.generate(prompt)
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                response = match.group(0)
            result = json.loads(response)
            return result
        except Exception as e:
            # Fallback to pass if LLM fails
            return {"status": "PASS"}
