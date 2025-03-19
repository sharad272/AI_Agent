import ollama
import logging
import re
import sys
import json
import time
import io

logger = logging.getLogger(__name__)

class OllamaHandler:
    def __init__(self):
        self.model = "deepseek-r1:1.5b"
        self.config = {
            "temperature": 0.7,
            "num_predict": 1000,
            "stream": True
        }
        
        # Ensure stdout uses UTF-8 encoding
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        else:
            # For older Python versions
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    def get_response(self, query: str, context: str = "", conversation_history: str = "") -> str:
        """Stream response from LLM with context and memory"""
        try:
            logger.debug(f"[OllamaHandler] Starting response for query: {query[:100]}...")
            response_text = ""

            # Format prompt
            full_prompt = f"""Context:
{context}

Query: {query}"""

            logger.debug("[OllamaHandler] Sending request to Ollama")
            try:
                # Stream response with timeout
                for chunk in ollama.chat(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an AI code assistant. Provide clear and concise responses."
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
                        response_text += text
                        
                        # Ensure proper UTF-8 encoding when writing to stdout
                        try:
                            sys.stdout.write(text)
                            sys.stdout.flush()
                        except UnicodeEncodeError as e:
                            # Handle encoding errors by replacing problematic characters
                            safe_text = text.encode('utf-8', errors='replace').decode('utf-8')
                            sys.stdout.write(safe_text)
                            sys.stdout.flush()
                            logger.warning(f"[OllamaHandler] Replaced problematic characters in output")
                            
                        logger.debug("[OllamaHandler] Received chunk")

            except Exception as e:
                logger.error(f"[OllamaHandler] Error during streaming: {str(e)}")
                raise

            sys.stdout.write('\n')
            sys.stdout.flush()
            
            logger.debug("[OllamaHandler] Response completed")
            return response_text

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            logger.error(f"[OllamaHandler] {error_msg}")
            
            # Ensure error message is properly encoded
            try:
                print(error_msg)
            except UnicodeEncodeError:
                print("Error: Encoding issue with response")
                
            sys.stdout.flush()
            return error_msg

def process_streaming_data(data):
    try:
        # Ensure the data is decoded using UTF-8
        text = data.decode('utf-8')
        # Process the text as needed
        # ...
    except UnicodeEncodeError as e:
        log(f"[OllamaHandler] Error during streaming: {str(e)}", 'error')
        # Handle the error appropriately
        # ...