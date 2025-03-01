import ollama
import logging
import re

logger = logging.getLogger(__name__)

class OllamaHandler:
    def __init__(self, model="deepseek-r1:1.5b"):
        self.model = model

    def _clean_response(self, response: str) -> str:
        """Clean the response by removing chain-of-thoughts content"""
        # Remove content between <think> tags
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        
        # Remove any "Let me think..." or similar phrases
        thought_patterns = [
            r'Let me think.*?\n',
            r'Let\'s approach this.*?\n',
            r'I will.*?\n',
            r'First, I\'ll.*?\n',
            r'Here\'s my thought process.*?\n',
            r'Let me break this down.*?\n'
        ]
        
        for pattern in thought_patterns:
            response = re.sub(pattern, '', response, flags=re.IGNORECASE)
        
        # Clean up extra newlines and spaces
        response = re.sub(r'\n\s*\n', '\n\n', response)
        return response.strip()

    def get_response(self, query: str, context: str = "") -> str:
        """Get a response from Ollama using the provided context"""
        system_prompt = ("You are a code assistant that helps with file operations and code questions. "
                        "Provide direct answers without explaining your thought process. "
                        "When creating or modifying files, use these prefixes:\n"
                        "CREATE_FILE:<filepath>\n"
                        "EDIT_FILE:<filepath>\n"
                        "DELETE_FILE:<filepath>")
        
        # Format the prompt
        full_prompt = f"{system_prompt}\n\nContext:\n{context}\n\nQuestion: {query}\n\nAnswer:"
        
        try:
            response = ollama.generate(
                model=self.model,
                prompt=full_prompt,
                options={
                    "temperature": 0.7,
                    "num_predict": 1000,
                }
            )
            
            # Clean and return the response
            return self._clean_response(response['response'])

        except Exception as e:
            error_msg = f"Error getting response from Ollama: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
