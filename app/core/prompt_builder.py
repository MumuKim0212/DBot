def build_sql_prompt(schema_text: str, user_query: str, previous_sql: str = None, error_msg: str = None, history: list = None) -> str:
    base_prompt = f"""Database Schema:
{schema_text}
"""

    if history:
        base_prompt += "\n[Chat History]\n"
        for h in history:
            base_prompt += f"User: {h['user']}\nAssistant (SQL): {h['sql']}\n\n"

    base_prompt += f"""User Request:
{user_query}

Rules:

[General]
- Only SELECT queries
- Always include LIMIT 100

[Aggregation Rules]
- Use aggregation functions (SUM, COUNT, AVG) when needed
- If aggregation is used with dimensions, always add GROUP BY
- NEVER mix aggregated and non-aggregated columns without GROUP BY

[Grain Rules]
- Each table has a grain (level of detail)
- When joining tables with different grains:
  - Avoid duplication
  - Use aggregation if needed

[Column Rules]
- dimension columns are GROUP BY targets
- measure columns are aggregation targets

[Validation]
- Ensure no duplicated counting
- Ensure logical correctness
"""

    if previous_sql and error_msg:
        base_prompt += f"""
[Self-Correction Request]
Your previous SQL attempt failed with a MySQL error. 
Previous SQL:
{previous_sql}

Error Message:
{error_msg}

Please carefully analyze the error, review the schema and constraints, and provide a corrected SQL query.
"""

    base_prompt += "\nReturn ONLY SQL."
    return base_prompt
