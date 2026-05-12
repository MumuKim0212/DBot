import json
import re
from typing import List, Dict, Any
from llm import get_llm

class Visualizer:
    def __init__(self):
        self.llm = get_llm()

    def generate_chart_config(self, query: str, columns: List[str]) -> Dict[str, Any]:
        """
        Analyze the query and column names to suggest a chart configuration.
        Does NOT process raw row data, only column names.
        """
        if not columns:
            return {"type": "none"}
            
        prompt = f"""
You are a UI Visualization Configurator.
The user asked a data question, and the database returned a set of columns.
You need to decide if a chart can be drawn and which columns to use for X and Y axes.

User Query: "{query}"
Available Columns: {', '.join(columns)}

Instructions:
1. Determine the best chart type: "bar", "line", "pie", or "none" (if it's just a raw table or text answer).
2. Identify which column should be the "x_axis" (usually categorical or date).
3. Identify which column(s) should be the "y_axis" (usually numeric).
4. Return ONLY valid JSON in the following format:
{{
  "type": "bar" | "line" | "pie" | "none",
  "x_axis": "column_name",
  "y_axis": ["column_name_1"]
}}
"""
        try:
            response = self.llm.generate(prompt)
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                response = match.group(0)
            return json.loads(response)
        except Exception as e:
            return {"type": "none"}
