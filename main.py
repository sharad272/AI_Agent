import os
import logging
import json
import shutil

# Configure logging with more details
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    print("\n=== AI Code Assistant (VSCode) ===")
    
    try:
        print("Initializing (this might take a moment)...")
        from services.query_service import QueryService

        # Create a temporary tracking directory for embeddings
        temp_tracking_dir = os.path.join(os.getcwd(), "temp-tracking")
        if not os.path.exists(temp_tracking_dir):
            os.makedirs(temp_tracking_dir)
            print(f"Created temp directory at: {temp_tracking_dir}")
        
        # Get open files from environment
        open_files_json = os.getenv('OPEN_FILES', '[]')
        try:
            open_files = json.loads(open_files_json)
            print(f"Received {len(open_files)} files from editor")
            
            # Write files to temp directory for indexing
            for file in open_files:
                file_path = os.path.join(temp_tracking_dir, os.path.basename(file['filePath']))
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(file['content'])
                print(f"Indexed file: {os.path.basename(file['filePath'])}")
                
        except json.JSONDecodeError:
            print("No open files received")
            open_files = []
            
        # Initialize QueryService with temp directory
        print("Initializing QueryService...")
        query_service = QueryService(temp_tracking_dir)
        print(f"Vector DB initialized with {len(open_files)} files")
        print("Ready! Waiting for queries...")
        
        while True:
            try:
                query = input("\n> ").strip()
                print(f"\nReceived query: {query}")
                
                if query.lower() == 'quit':
                    break

                # Process the query using existing backend functionality
                print("Processing query...")
                response = query_service.process_query(query)
                print("Query processed, formatting response...")
                
                # Format the response
                if hasattr(response, 'answer'):
                    print(f"\nAnswer: {response.answer}")
                    
                    # Handle code edits if present
                    if response.code_edits:
                        print("\nProposed code changes:")
                        for edit in response.code_edits:
                            print(f"\nFile: {edit.file_path}")
                            print("Content:")
                            print(edit.content)
                else:
                    print(f"\nAnswer: {response}")

            except Exception as e:
                print(f"\nError processing query: {str(e)}")
                logger.error(f"Query processing error: {str(e)}", exc_info=True)

    except Exception as e:
        print(f"\nError: {str(e)}")
        logger.error(f"Initialization error: {str(e)}", exc_info=True)
    finally:
        # Cleanup temp directory
        if os.path.exists(temp_tracking_dir):
            try:
                shutil.rmtree(temp_tracking_dir)
                print(f"Cleaned up temp directory: {temp_tracking_dir}")
            except Exception as e:
                print(f"Error cleaning up temp directory: {str(e)}")

if __name__ == "__main__":
    main()