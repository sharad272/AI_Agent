import ollama
import logging
import re
import sys

logger = logging.getLogger(__name__)

class OllamaHandler:
    def __init__(self, model="deepseek-r1:1.5b"):
        self.model = model
        self.config = {
            "temperature": 0.7,
            "num_predict": 1000
        }

    def get_response(self, query: str, context: str = "") -> str:
        """Stream response and return final text"""
        try:
            system_prompt = """You are an AI assistant with access to conversation history and code context.
            Use the provided context to give more relevant and consistent responses.
            If referring to past conversations or code, be explicit about it."""
            
            full_prompt = f"""System: {system_prompt}

Context:
{context}

Current Query: {query}

Response:"""
            
            # Initialize response collection
            full_response = []
            
            # Stream the response
            for chunk in ollama.generate(
                model=self.model,
                prompt=full_prompt,
                options=self.config,
                stream=True
            ):
                if 'response' in chunk:
                    text = chunk['response']
                    sys.stdout.write(text)
                    sys.stdout.flush()
                    full_response.append(text)

            # Add final newline
            sys.stdout.write('\n')
            sys.stdout.flush()
            
            # Join all chunks and return
            final_response = ''.join(full_response)
            return final_response.strip()

        except Exception as e:
            logger.error(f"Error getting response: {e}")
            return f"Error: {str(e)}"