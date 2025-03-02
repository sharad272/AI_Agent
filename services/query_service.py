from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional, Set
from models.ollama_handler import OllamaHandler
from vectordb.faiss_db import FAISSManager
from utils.file_reader import FileReader
import logging
import os
import json
import re

logger = logging.getLogger(__name__)

@dataclass
class QueryResponse:
    answer: str
    is_code_related: bool
    relevant_files: List[str]
    context: str = ""  # Make this optional with default empty string

class QueryService:
    def __init__(self):
        self.ollama = OllamaHandler()
        self.base_dir = os.path.normpath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.file_reader = FileReader(self.base_dir)  # Initialize FileReader first
        self.faiss_manager = self.file_reader.vector_store  # Use the same vector store instance
        self.context = {}  # Initialize context dictionary
        self.code_keywords = self._load_keywords()
        self.code_actions = {
            'show': self._show_file_content,
            'display': self._show_file_content,
            'fix': self._fix_file_content,
        }
        
    def _load_keywords(self) -> set:
        """Load keywords from config file"""
        try:
            config_path = os.path.join(self.base_dir, 'config', 'keywords.json')
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Combine all keyword categories
            keywords = set()
            for category in config['code_keywords'].values():
                keywords.update(category)
            
            logger.info(f"Loaded {len(keywords)} keywords from config")
            return keywords
        except Exception as e:
            logger.error(f"Error loading keywords: {e}")
            # Return default set if config loading fails
            return {'code', 'file', 'function', 'class'}

    def add_keywords(self, new_keywords: list) -> None:
        """Add new keywords to the existing set"""
        self.code_keywords.update(new_keywords)
        logger.info(f"Added {len(new_keywords)} new keywords")

    def update_context(self, file_contents: dict):
        """Update context and vector store"""
        self.context = file_contents
        # Ensure vector store is updated
        for filepath, content in file_contents.items():
            self.faiss_manager.add_file(filepath, content)
        logger.info(f"Updated context and vector store with {len(file_contents)} files")

    def is_code_related_query(self, query: str) -> bool:
        """Determine if the query is related to code or files"""
        query_words = set(query.lower().split())
        return bool(query_words & self.code_keywords)

    def _get_file_path_from_query(self, query: str) -> str:
        """Extract file path from query, handling both full and relative paths"""
        # Check for common file path patterns
        patterns = [
            r'\b\w+_?\w+\.py\b',  # matches file.py, file_name.py
            r'[\w/\\-]+\.py\b',   # matches path/to/file.py
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, query.lower())
            if matches:
                # Check in different possible locations
                for match in matches:
                    # Try relative to vectordb directory
                    vectordb_path = os.path.join(self.base_dir, 'vectordb', match)
                    if os.path.exists(vectordb_path):
                        return os.path.relpath(vectordb_path, self.base_dir)
                    
                    # Try direct path
                    direct_path = os.path.join(self.base_dir, match)
                    if os.path.exists(direct_path):
                        return os.path.relpath(direct_path, self.base_dir)
                    
                    # Try searching in all indexed files
                    for path in self.context.keys():
                        if path.lower().endswith(match):
                            return path
        return None

    def _show_file_content(self, file_path: str) -> str:
        """Display file content with better path handling"""
        try:
            # First try the exact path
            full_path = os.path.join(self.base_dir, file_path)
            
            # If not found, try to find it in indexed files
            if not os.path.exists(full_path):
                for indexed_path in self.context.keys():
                    if indexed_path.lower().endswith(file_path.lower()):
                        full_path = os.path.join(self.base_dir, indexed_path)
                        file_path = indexed_path
                        break
            
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return f"Content of {file_path}:\n\n```python\n{content}\n```"
            return f"File not found: {file_path}"
        except Exception as e:
            logger.error(f"Error reading file: {str(e)}")
            return f"Error reading file: {str(e)}"

    def _fix_file_content(self, file_path: str, context: str = "") -> str:
        """Handle fix requests for files"""
        try:
            full_path = os.path.join(self.base_dir, file_path)
            if not os.path.exists(full_path):
                return f"File not found: {file_path}"

            with open(full_path, 'r') as f:
                current_content = f.read()

            # Prepare context with current file content
            context = f"Current file content:\n```python\n{current_content}\n```\n\nPlease analyze and suggest fixes."
            
            # Get suggestions from Ollama
            return self.ollama.get_response(f"Fix the code in {file_path}", context)
        except Exception as e:
            return f"Error fixing file: {str(e)}"

    def is_contextual_query(self, query: str) -> bool:
        """Determine if query needs code context"""
        # Check length and code keywords
        if len(query.split()) <= 3:  # Short queries
            non_contextual = {
                'hi', 'hello', 'hey', 
                'how are you', 
                'what is your name',
                'who are you',
                'help',
                'thanks',
                'thank you'
            }
            return not any(q in query.lower() for q in non_contextual)
        return True

    def process_query(self, query: str) -> QueryResponse:
        """Process query and return suggestions without file modifications"""
        try:
            # Special handling for non-contextual queries
            if not self.is_contextual_query(query):
                response = self.ollama.get_response(query, "")
                return QueryResponse(
                    answer=response,
                    is_code_related=False,
                    relevant_files=[],
                    context=""
                )

            # For code-related queries
            vector_results = self.faiss_manager.search(query, k=5)
            context = self._build_vector_context(vector_results)
            
            if "fix" in query.lower() or "error" in query.lower():
                context = self._enhance_context_with_contents(vector_results)
            
            response = self.ollama.get_response(query, context)
            
            return QueryResponse(
                answer=response,
                is_code_related=True,
                relevant_files=[f for f, _ in vector_results],
                context=context
            )

        except Exception as e:
            logger.error(f"Query error: {e}")
            return QueryResponse(
                answer=f"Error: {str(e)}",
                is_code_related=False,
                relevant_files=[],
                context=""
            )

    def _build_vector_context(self, vector_results: List[Tuple[str, float]]) -> str:
        """Build context with vector similarity information"""
        if not vector_results:
            return ""
        
        context_parts = ["=== Relevant Files (by similarity) ==="]
        for filepath, score in vector_results:
            context_parts.append(f"- {filepath} (similarity: {score:.3f})")
        return "\n".join(context_parts)

    def _enhance_context_with_contents(self, vector_results: List[Tuple[str, float]]) -> str:
        """Add file contents to vector context"""
        context_parts = [self._build_vector_context(vector_results)]
        
        for filepath, score in vector_results[:3]:  # Limit to top 3 most relevant files
            content = self.context.get(filepath)
            if content:
                context_parts.append(f"\n=== File: {filepath} ===\n```python\n{content}\n```")
        
        return "\n\n".join(context_parts)

    def _get_relevant_files(self, query: str) -> List[str]:
        """Get relevant files using vector similarity"""
        try:
            similar_files = self.faiss_manager.search(query, k=5)
            if not similar_files:  # Handle empty results
                return []
            return [filepath for filepath, _ in similar_files]
        except Exception as e:
            logger.error(f"Error getting relevant files: {e}")
            return []