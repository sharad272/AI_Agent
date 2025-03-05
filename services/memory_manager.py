from typing import List, Dict
import json
import os
from datetime import datetime

class MemoryManager:
    def __init__(self, storage_path: str, max_memory: int = 10):
        self.storage_path = storage_path
        self.max_memory = max_memory
        self.memory_file = os.path.join(storage_path, "conversation_memory.json")
        self.short_term_memory: List[Dict] = []
        self.load_memory()

    def load_memory(self):
        """Load conversation history from disk"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    self.short_term_memory = json.load(f)[-self.max_memory:]
            except Exception as e:
                self.short_term_memory = []

    def save_memory(self):
        """Save conversation history to disk"""
        with open(self.memory_file, 'w') as f:
            json.dump(self.short_term_memory, f)

    def add_interaction(self, query: str, response: str):
        """Add new interaction to memory"""
        self.short_term_memory.append({
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'response': response
        })
        if len(self.short_term_memory) > self.max_memory:
            self.short_term_memory.pop(0)
        self.save_memory()

    def get_recent_context(self, limit: int = 5) -> str:
        """Get formatted recent conversations"""
        if not self.short_term_memory:
            return ""
        
        context = "Recent conversations:\n"
        for memory in self.short_term_memory[-limit:]:
            context += f"User: {memory['query']}\nAssistant: {memory['response']}\n\n"
        return context.strip()
