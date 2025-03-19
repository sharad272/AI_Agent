from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from models.ollama_handler import OllamaHandler
import os
from datetime import datetime
import re
import logging
from utils.code_processor import CodeProcessor
import sys
import time

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
    chain_of_thought: str = None

class QueryService:
    def __init__(self, vector_db=None):
        self.ollama = OllamaHandler()
        self.vector_db = vector_db
        self._conversation_history = []
        self._max_history = 5
        self.code_processor = CodeProcessor()  # Initialize once
        self._quick_responses = {
            'hi': 'Hello! I\'m your AI code assistant. How can I help you?',
            'hello': 'Hi! Ready to assist with your code questions.',
            'hey': 'Hey there! What can I help you with?',
            'help': 'I can help you with:\n- Code analysis\n- Explaining code\n- Finding relevant files\n- Answering coding questions',
            'thanks': 'You\'re welcome!',
            'thank you': 'You\'re welcome!',
            'bye': 'Goodbye!',
            'exit': 'Closing the session.'
        }
        self._file_cache = {}
        self._code_keywords = {'code', 'file', 'function', 'class', 'explain'}
        self._file_related_keywords = {
            'file', 'code', 'function', 'class', 
            'tracking', 'folder', 'directory',
            'explain', 'show', 'find', 'search',
            'meaning', 'context', 'inside',
            'create', 'new', 'make', 'add'
        }
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

    def check_quick_response(self, query: str) -> str:
        """Check if query has a quick response"""
        query_lower = query.lower().strip()
        return self._quick_responses.get(query_lower)

    def process_query(self, query: str) -> str:
        try:
            # Quick response check first
            quick_response = self.check_quick_response(query)
            if quick_response:
                print("<think>Using quick response</think>")
                sys.stdout.flush()
                print(f"Answer: {quick_response}")
                sys.stdout.flush()
                return quick_response

            # Show thinking process
            print("<think>Processing query through LLM...</think>")
            sys.stdout.flush()

            # Get conversation history
            conversation_history = self._get_conversation_context()

            # Get context from vector DB if available (only search, no indexing)
            context = ""
            if self.vector_db:
                print("<think>Finding relevant code context...</think>")
                sys.stdout.flush()
                # Just search the already indexed files
                relevant_files = self.vector_db.search(query, k=5)
                for file_path, score in relevant_files:
                    if score > 0.4:
                        with open(file_path, 'r') as f:
                            file_content = f.read()
                            context += f"\nFile: {file_path}\n{file_content}\n"

            # Send to LLM
            print("Answer:", end='')
            sys.stdout.flush()
            response = self.ollama.get_response(
                query=query,
                context=context,
                conversation_history=conversation_history
            )

            return response

        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            logger.error(error_msg)
            print(f"<think>{error_msg}</think>")
            sys.stdout.flush()
            return error_msg