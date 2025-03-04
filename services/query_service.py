from dataclasses import dataclass
from typing import List, Dict, Tuple
from models.ollama_handler import OllamaHandler
import os

@dataclass
class QueryResponse:
    answer: str
    is_code_related: bool = False
    relevant_files: List[str] = None

class QueryService:
    def __init__(self, tracking_dir: str):
        self.ollama = OllamaHandler()
        self.tracking_dir = tracking_dir
        self._file_cache = {}
        self._quick_responses = {
            'hi': 'Hello! How can I help you?',
            'hello': 'Hi! Ready to assist you.',
            'help': 'I can help you with code analysis and questions.'
        }
        self._code_keywords = {'code', 'file', 'function', 'class', 'explain'}

    def process_query(self, query: str) -> QueryResponse:
        """Process query with simple context building"""
        try:
            query_lower = query.lower().strip()
            
            # Handle quick responses
            if query_lower in self._quick_responses:
                return QueryResponse(
                    answer=self._quick_responses[query_lower],
                    is_code_related=False
                )

            # Load files if needed
            if not self._file_cache and os.path.exists(self.tracking_dir):
                for file in os.listdir(self.tracking_dir):
                    if file.endswith('.py'):
                        try:
                            with open(os.path.join(self.tracking_dir, file), 'r') as f:
                                self._file_cache[file] = f.read()
                        except Exception as e:
                            logger.error(f"Error reading {file}: {e}")

            # Get response with or without context
            is_code_query = any(kw in query_lower for kw in self._code_keywords)
            context = ""
            if is_code_query and self._file_cache:
                context = "\n".join(f"File: {f}\n{c}" for f, c in self._file_cache.items())

            answer = self.ollama.get_response(query, context)
            if not answer:
                answer = "I apologize, but I couldn't generate a response. Please try rephrasing your question."

            return QueryResponse(
                answer=answer,
                is_code_related=is_code_query,
                relevant_files=list(self._file_cache.keys()) if is_code_query else []
            )

        except Exception as e:
            logger.error(f"Query processing error: {e}")
            return QueryResponse(f"Error processing query: {str(e)}")