import json

def load_schema(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)