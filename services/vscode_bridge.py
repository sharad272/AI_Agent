import sys
import json
import os
from services.query_service import QueryService
from models.ollama_handler import OllamaHandler
import logging
from vectordb import FAISSManager  # Fixed import path

logger = logging.getLogger(__name__)

class VSCodeBridge:
    def __init__(self):
        try:
            logger.info("Initializing VSCodeBridge components...")
            # Initialize vector DB first - but don't index yet
            self.vector_db = FAISSManager(dimension=384, n_lists=1)
            self.query_service = QueryService(vector_db=self.vector_db)
            self.conversation_history = []
            logger.info("VSCodeBridge initialization complete")
        except Exception as e:
            logger.error(f"Error initializing VSCodeBridge: {e}")
            raise

    def handle_input(self):
        """Handle input from VSCode extension"""
        while True:
            try:
                input_line = sys.stdin.readline()
                if not input_line:
                    break
                
                data = json.loads(input_line)
                command = data.get('command', '')
                
                logger.debug(f"Received command: {command}")
                
                if command == 'initialize':
                    files = data.get('files', [])
                    logger.info(f"Starting to process {len(files)} files...")
                    
                    # Process files in batches for better performance
                    batch_size = 10
                    for i in range(0, len(files), batch_size):
                        batch = files[i:i + batch_size]
                        embeddings_batch = []
                        
                        # Generate embeddings for batch
                        for file in batch:
                            embedding = self.vector_db.encoder.encode([file['content']])[0]
                            embeddings_batch.append({
                                'filepath': file['filePath'],
                                'embedding': embedding,
                                'language': file['language']
                            })
                        
                        # Index batch
                        for emb in embeddings_batch:
                            self.vector_db.add_to_index(**emb)
                        
                        logger.debug(f"Processed batch {i//batch_size + 1}/{(len(files)-1)//batch_size + 1}")
                    
                    # Finalize indexing
                    self.vector_db.finalize_index()
                    logger.info("Successfully indexed all files")
                    print("AI Assistant ready! Waiting for queries...")
                    sys.stdout.flush()
                    
                elif command == 'query':
                    query = data.get('text', '').strip()
                    logger.info(f"[VSCodeBridge] Received query command: {query}")
                    
                    try:
                        # Show processing status
                        sys.stdout.flush()
                        logger.debug("[VSCodeBridge] Sent thinking status")
                        
                        # Get response from query service
                        logger.debug("[VSCodeBridge] Calling query service...")
                        response = self.query_service.process_query(query)
                        logger.debug("[VSCodeBridge] Got response from query service")
                        
                        # Print the answer
                        if response:
                            logger.debug("[VSCodeBridge] Sending response to frontend")
                            print(f"Answer: {response}")
                        else:
                            logger.warning("[VSCodeBridge] No response generated")
                            print("Error: No response generated")
                        sys.stdout.flush()
                        logger.debug("[VSCodeBridge] Response flushed to frontend")
                        
                    except Exception as e:
                        error_msg = f"Error processing query: {str(e)}"
                        logger.error(f"[VSCodeBridge] {error_msg}", exc_info=True)
                        print(f"Error: {error_msg}")
                        sys.stdout.flush()
                
                sys.stdout.flush()
                
            except Exception as e:
                error_msg = f"Error in bridge: {str(e)}"
                logger.error(error_msg, exc_info=True)
                print(f"Error: {error_msg}")
                sys.stdout.flush()

if __name__ == '__main__':
    bridge = VSCodeBridge()
    bridge.handle_input() 