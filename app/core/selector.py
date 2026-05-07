import logging
import re
import json
import os
from pathlib import Path
from typing import List, Dict
from app.core.schema_loader import load_schema
from app.utils.embeddings import get_embedding, cosine_similarity

logger = logging.getLogger(__name__)

class TableSelector:
    def __init__(self, schema_full_path: str, schema_index_path: str, embeddings_path: str = None):
        self.schema_full = load_schema(schema_full_path)
        self.schema_index = load_schema(schema_index_path)
        self.embeddings_path = embeddings_path
        
        self.table_map = {
            t["name"]: t for t in self.schema_full["tables"]
            if not t.get("hidden") and not t.get("ignore")
        }
        
        self.table_embeddings = {}
        if embeddings_path and Path(embeddings_path).exists():
            with open(embeddings_path, "r", encoding="utf-8") as f:
                self.table_embeddings = json.load(f)

        missing = [name for name in self.table_map if name not in self.schema_index]
        if missing:
            logger.warning("Tables in schema_full but missing from schema_index (will never be selected): %s", missing)

    def select(self, query: str, top_k: int = 5) -> List[Dict]:
        q = query.lower()
        scored = []

        if self.table_embeddings:
            try:
                query_vector = get_embedding(query)
                for table_name, table_vector in self.table_embeddings.items():
                    sim = cosine_similarity(query_vector, table_vector)
                    
                    if table_name.lower() in q:
                        sim += 0.2
                    for kw in self.schema_index.get(table_name, {}).get("keywords", []):
                        if kw.lower() in q:
                            sim += 0.1
                            
                    if sim > 0.3:
                        scored.append((sim, table_name))
            except Exception as e:
                logger.error(f"Embedding search failed: {e}. Falling back to keyword search.")
                scored = self._keyword_search(q)
        else:
            scored = self._keyword_search(q)

        scored.sort(reverse=True, key=lambda x: x[0])
        selected_names = [name for _, name in scored[:top_k]]

        selected_tables = [
            self.table_map[name] for name in selected_names
            if name in self.table_map
        ]

        return selected_tables

    def _keyword_search(self, q: str) -> List[tuple]:
        scored = []
        for table_name, meta in self.schema_index.items():
            score = 0
            if table_name.lower() in q:
                score += 5
            for kw in meta.get("keywords", []):
                if kw.lower() in q:
                    score += 3
            summary = meta.get("summary", "").lower()
            if any(word in q for word in re.findall(r'\w+', summary)):
                score += 1
            if score > 0:
                scored.append((score, table_name))
        return scored