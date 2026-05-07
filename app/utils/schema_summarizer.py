import json
import re
from pathlib import Path
import sys

# To import from llm package
sys.path.append(str(Path(__file__).parent.parent))

from llm import get_llm

def generate_summaries(schema_path: str, output_path: str):
    llm = get_llm()
    
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_full = json.load(f)
        
    schema_index = {}
    
    if Path(output_path).exists():
        with open(output_path, "r", encoding="utf-8") as f:
            try:
                schema_index = json.load(f)
            except:
                pass
                
    for table in schema_full.get("tables", []):
        if table.get("hidden") or table.get("ignore"):
            continue
            
        table_name = table["name"]
        
        # Skip if already generated
        if table_name in schema_index and schema_index[table_name].get("summary") and schema_index[table_name].get("summary") != "Error":
            continue
            
        columns = []
        for col in table.get("columns", []):
            if col.get("hidden") or col.get("ignore"):
                continue
            desc_text = f" - {col['desc']}" if "desc" in col else ""
            columns.append(f"{col['name']} ({col['type']}){desc_text}")
        
        prompt = f"""
Here is a database table named '{table_name}'.
Columns: {', '.join(columns)}

Additional Information:
- A user can have a maximum of 3 characters.
- user_idx represents the user's ID.
- char_idx represents the character's ID.

Describe the purpose of this table in 1-2 sentences in Korean.
Also, provide 3-5 Korean keywords related to this table.
Return ONLY valid JSON in this format:
{{
  "summary": "...",
  "keywords": ["...", "..."]
}}
"""
        try:
            print(f"Generating summary for {table_name}...")
            response = llm.generate(prompt)
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                response = match.group(0)
            
            data = json.loads(response)
            schema_index[table_name] = data
        except Exception as e:
            print(f"Failed for {table_name}: {e}")
            schema_index[table_name] = {"summary": "Error", "keywords": []}
            
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(schema_index, f, ensure_ascii=False, indent=2)
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    _DIR = Path(__file__).parent / "data"
    generate_summaries(str(_DIR / "schema_full.json"), str(_DIR / "schema_index.json"))
