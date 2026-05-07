import os
import json
import numpy as np
from pathlib import Path

def get_embedding(text: str) -> list[float]:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    a = np.array(v1)
    b = np.array(v2)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))

def build_embeddings_index(schema_index_path: str, output_path: str):
    with open(schema_index_path, "r", encoding="utf-8") as f:
        schema_index = json.load(f)
        
    embeddings_data = {}
    
    for table_name, data in schema_index.items():
        summary = data.get("summary", "")
        keywords = " ".join(data.get("keywords", []))
        text_to_embed = f"Table: {table_name}\nSummary: {summary}\nKeywords: {keywords}"
        
        print(f"Embedding {table_name}...")
        try:
            vector = get_embedding(text_to_embed)
            embeddings_data[table_name] = vector
        except Exception as e:
            print(f"Error embedding {table_name}: {e}")
            
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(embeddings_data, f, ensure_ascii=False)
    print(f"Embeddings saved to {output_path}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    _DIR = Path(__file__).parent / "data"
    build_embeddings_index(str(_DIR / "schema_index.json"), str(_DIR / "table_embeddings.json"))
