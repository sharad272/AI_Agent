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
        self._file_related_keywords = {
            'file', 'code', 'function', 'class', 
            'tracking', 'folder', 'directory',
            'explain', 'show', 'find', 'search',
            'meaning', 'context', 'inside'
        }

    def _is_file_related_query(self, query: str) -> bool:
        """Check if query is related to files in tracking directory"""
        query_lower = query.lower()
        
        # Check for file-related keywords
        if any(kw in query_lower for kw in self._file_related_keywords):
            return True
            
        # Check if query contains any tracked file names
        tracked_files = os.listdir(self.tracking_dir)
        if any(file.lower() in query_lower for file in tracked_files):
            return True
            
        return False

    def process_query(self, query: str) -> QueryResponse:
        """Process query with context only when file-related"""
        try:
            query_lower = query.lower().strip()
            
            # Handle quick responses
            if query_lower in self._quick_responses:
                return QueryResponse(
                    answer=self._quick_responses[query_lower],
                    is_code_related=False
                )

            # Check if query is file-related
            is_file_related = self._is_file_related_query(query)
            
            if not is_file_related:
                # Direct LLM query without context for non-file queries
                answer = self.ollama.get_response(query, "")
                return QueryResponse(
                    answer=answer,
                    is_code_related=False
                )

            # For file-related queries, use vector DB and context
            if not self._file_cache and os.path.exists(self.tracking_dir):
                for file in os.listdir(self.tracking_dir):
                    if file.endswith('.py'):
                        try:
                            with open(os.path.join(self.tracking_dir, file), 'r') as f:
                                self._file_cache[file] = f.read()
                        except Exception as e:
                            logger.error(f"Error reading {file}: {e}")

            # Build context for file-related queries
            context = "\n".join(f"File: {f}\n{c}" for f, c in self._file_cache.items())
            answer = self.ollama.get_response(query, context)

            return QueryResponse(
                answer=answer,
                is_code_related=True,
                relevant_files=list(self._file_cache.keys())
            )
        except Exception as e:
            logger.error(f"Query processing error: {e}")
            return QueryResponse(f"Error processing query: {str(e)}")