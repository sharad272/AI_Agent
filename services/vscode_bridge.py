import sys
import json
from services.query_service import QueryService
import logging

logger = logging.getLogger(__name__)

class VSCodeBridge:
    def __init__(self):
        self.query_service = QueryService(None)
    
    def process_files(self, files_data):
        """Process files from VSCode and update vector DB"""
        try:
            for file in files_data:
                print(f"Processing file: {file['filePath']}")
                # Convert file data to format expected by QueryService
                file_info = {
                    'content': file['content'],
                    'language': file['language'],
                    'file_path': file['filePath']
                }
                # Update vector DB with file content
                self.query_service.update_file(file_info)
                print(f"Generated embeddings for: {file['filePath']}")
        except Exception as e:
            print(f"Error processing files: {str(e)}")
            raise e

    def handle_input(self):
        """Handle input from VSCode extension"""
        while True:
            try:
                input_line = sys.stdin.readline()
                if not input_line:
                    break
                
                data = json.loads(input_line)
                
                if data.get('command') == 'initialize':
                    self.process_files(data.get('files', []))
                    print("Files processed and embeddings updated")
                elif data.get('command') == 'query':
                    query = data.get('text')
                    result = self.query_service.process_query(query)
                    print(f"\nAnswer: {result}")
                
                sys.stdout.flush()
                
            except Exception as e:
                print(f"Error in bridge: {str(e)}")
                sys.stdout.flush()

if __name__ == '__main__':
    bridge = VSCodeBridge()
    bridge.handle_input() 