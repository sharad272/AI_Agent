from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from models.ollama_handler import OllamaHandler
import os
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)

@dataclass
class CodeEdit:
    file_path: str
    content: str
    language: str = "python"

@dataclass
class QueryResponse:
    answer: str
    is_code_related: bool = False
    relevant_files: List[str] = None
    conversation_id: str = None
    code_edits: List[CodeEdit] = None

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
            'meaning', 'context', 'inside',
            'create', 'new', 'make', 'add'
        }
        self._conversation_history = []
        self._max_history = 5
        self._user_info = {}  # Add this to store user details
        self._code_block_pattern = r"```(\w+):?(.*?)\n(.*?)```"

    def _add_to_history(self, query: str, response: str):
        """Add conversation to history"""
        self._conversation_history.append({
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'response': response
        })
        # Keep only recent history
        if len(self._conversation_history) > self._max_history:
            self._conversation_history.pop(0)

    def _get_conversation_context(self) -> str:
        """Get formatted conversation history"""
        if not self._conversation_history:
            return ""
        
        context = "Previous conversations:\n"
        for conv in self._conversation_history:
            context += f"User: {conv['query']}\n"
            context += f"Assistant: {conv['response']}\n"
        return context

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

    def _extract_names(self, query: str) -> List[str]:
        """Extract potential names from the query"""
        # Simple name extraction - you might want to use NLP for better accuracy
        words = query.split()
        # Look for capitalized words that might be names
        potential_names = [word for word in words if word[0].isupper()]
        return potential_names

    def _update_user_info(self, query: str):
        """Update user info based on query content"""
        # Look for name introductions
        name_patterns = [
            r"(?i)my name is (\w+)",
            r"(?i)i am (\w+)",
            r"(?i)this is (\w+)",
            r"(?i)i'm (\w+)"
        ]
        
        for pattern in name_patterns:
            matches = re.findall(pattern, query)
            if matches:
                self._user_info['user_name'] = matches[0]
                break

        # Look for friend/other person mentions
        friend_patterns = [
            r"(?i)my friend (\w+)",
            r"(?i)friend named (\w+)",
            r"(?i)friend is (\w+)"
        ]
        
        for pattern in friend_patterns:
            matches = re.findall(pattern, query)
            if matches:
                if 'mentioned_people' not in self._user_info:
                    self._user_info['mentioned_people'] = set()
                self._user_info['mentioned_people'].add(matches[0])

    def _extract_code_edits(self, response: str) -> List[CodeEdit]:
        """Extract code blocks and their target files from the response"""
        code_edits = []
        matches = re.finditer(self._code_block_pattern, response, re.DOTALL)
        
        for match in matches:
            language = match.group(1)
            file_path = match.group(2).strip()
            content = match.group(3).strip()
            
            if file_path:  # Only process blocks with file paths
                code_edits.append(CodeEdit(
                    file_path=file_path,
                    content=content,
                    language=language
                ))
        
        return code_edits

    def apply_code_edits(self, code_edits: List[CodeEdit]) -> Dict[str, str]:
        """Apply code edits to files and return results"""
        results = {}
        
        for edit in code_edits:
            try:
                file_path = os.path.join(self.tracking_dir, edit.file_path)
                
                # Ensure the file exists or is being created
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                # If content contains "... existing code ..." markers, do partial update
                if "... existing code ..." in edit.content:
                    if os.path.exists(file_path):
                        with open(file_path, 'r') as f:
                            current_content = f.read()
                        # TODO: Implement smart merging of changes
                        final_content = current_content + "\n" + edit.content
                    else:
                        final_content = edit.content
                else:
                    # If no markers, replace entire file content
                    final_content = edit.content
                
                # Write the changes
                with open(file_path, 'w') as f:
                    f.write(final_content)
                
                results[edit.file_path] = "Success"
                
            except Exception as e:
                results[edit.file_path] = f"Error: {str(e)}"
        
        return results

    def create_new_file(self, file_path: str, content: str) -> bool:
        """Create a new file with the given content"""
        try:
            full_path = os.path.join(self.tracking_dir, file_path)
            
            # Check if file already exists
            if os.path.exists(full_path):
                logger.warning(f"File {file_path} already exists")
                return False
                
            # Create directories if they don't exist
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Write the file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            # Add to file cache
            self._file_cache[file_path] = content
            
            logger.info(f"Successfully created file: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating file {file_path}: {e}")
            return False

    def process_query(self, query: str) -> QueryResponse:
        """Process query with enhanced context awareness"""
        try:
            # Update user info based on query
            self._update_user_info(query)
            
            query_lower = query.lower().strip()
            
            # Handle quick responses
            if query_lower in self._quick_responses:
                response = self._quick_responses[query_lower]
                self._add_to_history(query, response)
                return QueryResponse(
                    answer=response,
                    is_code_related=False
                )

            # Get conversation context with user info
            conversation_context = self._get_conversation_context()
            
            if not self._is_file_related_query(query):
                answer = self.ollama.get_response(
                    query, 
                    conversation_context,
                    self._user_info  # Pass user info to Ollama
                )
                self._add_to_history(query, answer)
                return QueryResponse(
                    answer=answer,
                    is_code_related=False
                )

            # For file-related queries, use vector DB and context
            if not self._file_cache and os.path.exists(self.tracking_dir):
                for file in os.listdir(self.tracking_dir):
                    if file.endswith('.py'):
                        try:
                            with open(os.path.join(self.tracking_dir, file), 'r', encoding='utf-8', errors='ignore') as f:
                                self._file_cache[file] = f.read()
                        except Exception as e:
                            logger.error(f"Error reading {file}: {e}")

            # Build context combining file content and conversation history
            file_context = "\n".join(f"File: {f}\n{c}" for f, c in self._file_cache.items())
            conversation_context = self._get_conversation_context()
            combined_context = f"{conversation_context}\n\nCode Context:\n{file_context}"
            
            # Check for file creation request
            if any(kw in query_lower for kw in ['create file', 'new file', 'make file']):
                # Let the LLM handle the file creation response
                answer = self.ollama.get_response(
                    query + "\nPlease provide the code in a markdown code block with the file path like: ```python:path/to/file```", 
                    conversation_context
                )
                self._add_to_history(query, answer)
                
                # Extract code edits (which include new files)
                code_edits = self._extract_code_edits(answer)
                
                # Create new files from the code edits
                created_files = []
                for edit in code_edits:
                    if self.create_new_file(edit.file_path, edit.content):
                        created_files.append(edit.file_path)
                
                return QueryResponse(
                    answer=answer,
                    is_code_related=True,
                    relevant_files=created_files,
                    code_edits=code_edits
                )

            answer = self.ollama.get_response(query, combined_context)
            self._add_to_history(query, answer)
            
            # Extract code edits from the response
            code_edits = self._extract_code_edits(answer)
            
            return QueryResponse(
                answer=answer,
                is_code_related=True,
                relevant_files=list(self._file_cache.keys()),
                code_edits=code_edits
            )
        except Exception as e:
            logger.error(f"Query processing error: {e}")
            return QueryResponse(f"Error processing query: {str(e)}")