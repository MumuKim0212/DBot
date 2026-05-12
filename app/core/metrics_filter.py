import json
import re
from pathlib import Path
from typing import List, Dict, Any


def filter_relevant_metrics(query: str, metrics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """키워드 매칭으로 질문과 관련된 지표만 반환한다."""
    query_lower = query.lower()
    matched = []
    for metric in metrics:
        keywords = metric.get("keywords", []) + [metric.get("name", "")]
        if any(kw.lower() in query_lower for kw in keywords if kw):
            matched.append(metric)
    return matched


def load_metrics(metrics_path: Path) -> List[Dict[str, Any]]:
    if not metrics_path.exists():
        return []
    try:
        data = json.loads(metrics_path.read_text(encoding="utf-8"))
        return data.get("metrics", [])
    except Exception:
        return []
