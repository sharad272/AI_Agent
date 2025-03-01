import logging
from models.ollama_handler import OllamaHandler
from utils.file_reader import FileReader
from services.query_service import QueryService
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, file_reader, query_service):
        self.file_reader = file_reader
        self.query_service = query_service

    def on_modified(self, event):
        if not event.is_directory and self.file_reader.is_supported_file(event.src_path):
            logger.info(f"File changed: {event.src_path}")
            self.update_context()

    def update_context(self):
        file_contents = self.file_reader.read_all_files()
        self.query_service.update_context(file_contents)
        logger.info(f"Updated context with {len(file_contents)} files")

def main():
    # Initialize components with correct path handling
    logger.info("Initializing with Ollama Deepseek model...")
    # Use the current working directory instead of script directory
    current_dir = os.getcwd()
    logger.info(f"Using base directory: {current_dir}")
    
    file_reader = FileReader(current_dir)
    query_service = QueryService()

    # Initial context loading
    logger.info("Loading initial file context...")
    event_handler = FileChangeHandler(file_reader, query_service)
    event_handler.update_context()

    # Set up file monitoring
    observer = Observer()
    observer.schedule(event_handler, path=file_reader.base_dir, recursive=True)
    observer.start()

    try:
        print("\nAI Code Assistant (using Ollama Deepseek)")
        print("----------------------------------------")
        while True:
            query = input("\nEnter your question (or 'quit' to exit): ")
            if query.lower() == 'quit':
                break

            response = query_service.process_query(query)
            print("\nAnswer:", response.answer)
            
            # Only show relevant files for code-related queries
            if response.is_code_related and response.relevant_files:
                print("\nRelevant files:", ", ".join(response.relevant_files))
            
            # Reload context if files were modified
            if any(keyword in response.answer for keyword in ['Created file:', 'Modified file:', 'Deleted file:']):
                event_handler.update_context()

    except KeyboardInterrupt:
        observer.stop()
    
    observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
