from dataclasses import dataclass
from models.ollama_handler import OllamaHandler
from vectordb.faiss_db import FAISSManager
import logging
import os
import json
import re

logger = logging.getLogger(__name__)

@dataclass
class QueryResponse:
    answer: str
    relevant_files: list
    context: str
    is_code_related: bool  # New field to track if query is code-related

class QueryService:
    def __init__(self):
        self.ollama = OllamaHandler()
        self.faiss_manager = FAISSManager()
        self.base_dir = os.path.normpath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
        """Update the context with new file contents"""
        self.context = file_contents
        logger.info(f"Updated context with {len(file_contents)} files")

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

    def process_query(self, query: str) -> QueryResponse:
        """Process a query using vector similarity search and LLM"""
        try:
            logger.info(f"Processing query: {query}")
            
            # Check for file operations first
            file_path = self._get_file_path_from_query(query)
            if file_path:
                for action, handler in self.code_actions.items():
                    if action in query.lower():
                        answer = handler(file_path)
                        return QueryResponse(
                            answer=answer,
                            context="",
                            relevant_files=[file_path],
                            is_code_related=True
                        )

            is_code_related = self.is_code_related_query(query)
            context_str = ""
            relevant_files = []

            # Only perform vector search for code-related queries
            if is_code_related:
                # First, try to find relevant documents using FAISS
                relevant_docs, scores = self.faiss_manager.search(query, k=3)
                
                # Prepare context from both FAISS results and current context
                faiss_context = []
                if relevant_docs:
                    faiss_context = [f"File: {path}\n{content}" for path, content in relevant_docs]
                    # Set initial relevant files from FAISS results
                    relevant_files = [path for path, _ in relevant_docs]
                
                # Add any additional current context
                current_context = [f"File: {path}\n{content}" 
                                for path, content in self.context.items()
                                if path not in [doc[0] for doc in relevant_docs]]
                
                # Combine contexts, prioritizing FAISS results
                context_str = "\n\n".join(faiss_context + current_context[:2])

            # Get response from Ollama
            answer = self.ollama.get_response(query, context_str if is_code_related else "")
            
            # Update relevant files based on the answer if needed
            if is_code_related:
                # Add any additional files mentioned in the answer
                relevant_files.extend([
                    path for path in self.context.keys() 
                    if path.lower() in answer.lower() and path not in relevant_files
                ])
            
            # Handle file operations if needed
            if any(keyword in query.lower() for keyword in ['create file', 'new file', 'edit file', 'delete file']):
                answer = self._handle_file_operations(query, answer)

            return QueryResponse(
                answer=answer,
                context=context_str,
                relevant_files=relevant_files,
                is_code_related=is_code_related
            )
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return QueryResponse(
                answer=f"Error: {str(e)}",
                context="Error occurred",
                relevant_files=[],
                is_code_related=False
            )

    def _handle_file_operations(self, query: str, llm_response: str) -> str:
        """Handle file creation, modification, and deletion based on LLM response"""
        try:
            if 'CREATE_FILE:' in llm_response:
                lines = llm_response.split('\n')
                for i, line in enumerate(lines):
                    if line.startswith('CREATE_FILE:'):
                        filepath = os.path.join(self.base_dir, line.split(':', 1)[1].strip())
                        content = '\n'.join(lines[i+1:])
                        os.makedirs(os.path.dirname(filepath), exist_ok=True)
                        with open(filepath, 'w') as f:
                            f.write(content)
                        return f"Created file: {filepath}"

            elif 'EDIT_FILE:' in llm_response:
                lines = llm_response.split('\n')
                for i, line in enumerate(lines):
                    if line.startswith('EDIT_FILE:'):
                        filepath = os.path.join(self.base_dir, line.split(':', 1)[1].strip())
                        content = '\n'.join(lines[i+1:])
                        with open(filepath, 'w') as f:
                            f.write(content)
                        return f"Modified file: {filepath}"

            elif 'DELETE_FILE:' in llm_response:
                filepath = os.path.join(self.base_dir, llm_response.split(':', 1)[1].strip())
                if os.path.exists(filepath):
                    os.remove(filepath)
                    return f"Deleted file: {filepath}"
                return f"File not found: {filepath}"

            return llm_response

        except Exception as e:
            logger.error(f"Error in file operation: {str(e)}")
            return f"Error performing file operation: {str(e)}"