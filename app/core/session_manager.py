import time
from typing import List, Dict

class SessionManager:
    def __init__(self, max_history=5, expiry_seconds=3600):
        self.sessions = {}
        self.max_history = max_history
        self.expiry_seconds = expiry_seconds

    def get_context(self, session_id: str) -> dict:
        self._cleanup()
        if session_id not in self.sessions:
            return {"history": [], "last_tables": []}
        
        self.sessions[session_id]["last_accessed"] = time.time()
        return self.sessions[session_id]

    def update_context(self, session_id: str, user_query: str, sql: str, selected_tables: List[Dict]):
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "history": [],
                "last_tables": [],
                "last_accessed": time.time()
            }
        
        session = self.sessions[session_id]
        session["last_accessed"] = time.time()
        
        # Append history
        session["history"].append({
            "user": user_query,
            "sql": sql
        })
        
        # Keep only max_history
        if len(session["history"]) > self.max_history:
            session["history"] = session["history"][-self.max_history:]
            
        # Update last tables
        session["last_tables"] = selected_tables

    def _cleanup(self):
        now = time.time()
        expired = [sid for sid, data in self.sessions.items() 
                  if now - data["last_accessed"] > self.expiry_seconds]
        for sid in expired:
            del self.sessions[sid]

# Singleton instance
session_manager = SessionManager()
