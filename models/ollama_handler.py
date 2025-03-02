import ollama
import logging
import re

logger = logging.getLogger(__name__)

class OllamaHandler:
    def __init__(self, model="deepseek-r1:1.5b"):
        self.model = model
        self.error_fix_config = {
            "temperature": 0.5,
            "num_predict": -1,
            "stop": ["</SUGGESTION>"]
        }
        self.normal_config = {
            "temperature": 0.7,
            "num_predict": 1000,
        }
        self.explanation_config = {
            "temperature": 0.5,
            "num_predict": -1,  # No limit for explanations
            "stop": ["</EXPLANATION>"]
        }

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
        """Get response with suggestions only, no file operations"""
        try:
            if "explain" in query.lower() or "how" in query.lower():
                system_prompt = (
                    "You are a code explanation assistant. For each file:\n"
                    "1. Start with file path and its main purpose\n"
                    "2. Explain key components (classes, functions, methods)\n"
                    "3. Describe the flow and interactions\n"
                    "4. Note any important dependencies\n"
                    "5. Format each file explanation as:\n"
                    "=== FILE: <filepath> ===\n"
                    "[Your explanation here]\n"
                    "=== END FILE ===\n\n"
                    "If multiple files are involved, explain their relationships.\n"
                    "<EXPLANATION>\n"
                )
                config = self.explanation_config
            elif "error" in query.lower() or "fix" in query.lower():
                system_prompt = (
                    "You are a code assistant. For each error or issue:\n"
                    "1. First explain the error briefly\n"
                    "2. For each affected file, suggest the complete fixed code as:\n"
                    "SUGGESTION FOR <filepath>:\n"
                    "```python\n"
                    "[Complete suggested code]\n"
                    "```\n"
                    "3. Make sure to include complete code, no truncations\n"
                    "4. Provide suggestions for all affected files\n"
                    "</SUGGESTION>\n"
                )
                config = self.error_fix_config
            else:
                system_prompt = (
                    "You are a code assistant. "
                    "Provide direct answers without explaining your thought process."
                )
                config = self.normal_config

            full_prompt = (
                f"{system_prompt}\n\n"
                f"Context:\n{context}\n\n"
                f"Query: {query}\n\n"
                "Response:"
            )

            response = ollama.generate(
                model=self.model,
                prompt=full_prompt,
                options=config
            )

            return self._clean_response(response['response'])

        except Exception as e:
            logger.error(f"Error getting response: {e}")
            return f"Error: {str(e)}"
