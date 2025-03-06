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
            "num_predict": 1000,
            "stream": True
        }

    def get_response(self, query: str, context: str = "", user_info: dict = None) -> str:
        """Stream response and return final text"""
        try:
            system_prompt = """You are an AI assistant with access to conversation history and code context.
            Pay attention to names and personal details mentioned in conversations.
            Remember and refer to people by their names when mentioned.
            Maintain a natural conversational flow while being consistent with previously shared information.
            If someone was mentioned before, acknowledge that you remember them."""
            
            # Format context to highlight user information
            user_context = ""
            if user_info:
                user_context = "User Information:\n"
                for key, value in user_info.items():
                    user_context += f"- {key}: {value}\n"

            full_prompt = f"""System: {system_prompt}

{user_context}
Conversation History:
{context}

Current Query: {query}

Response:"""
            
            # Initialize response collection
            full_response = []
            
            # Stream the response using chat API
            for chunk in ollama.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ],
                stream=True
            ):
                if 'message' in chunk:
                    text = chunk['message']['content']
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