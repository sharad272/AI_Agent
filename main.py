import logging
from models.ollama_handler import OllamaHandler
from utils.file_reader import FileReader
from services.query_service import QueryService
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, file_reader, query_service):
        self.file_reader = file_reader
        self.query_service = query_service
        self.last_update = 0
        self.update_cooldown = 2.0
        self.pending_changes: Set[str] = set()
        self.base_dir = Path(query_service.base_dir)  # Add base_dir as Path

    def _schedule_update(self):
        """Schedule context update with debouncing"""
        current_time = time.time()
        if current_time - self.last_update >= self.update_cooldown and self.pending_changes:
            self._do_update()
            self.last_update = current_time

    def _do_update(self):
        """Process pending file changes"""
        try:
            # Only update changed files
            file_contents = {}
            for filepath in self.pending_changes:
                with open(os.path.join(self.base_dir, filepath), 'r', encoding='utf-8') as f:
                    content = f.read()
                    file_contents[filepath] = content
            
            if file_contents:
                self.query_service.update_context(file_contents)
                logger.info(f"Updated context with {len(file_contents)} changed files")
            
            self.pending_changes.clear()

        except Exception as e:
            logger.error(f"Error updating files: {e}")

    def on_modified(self, event):
        """Handle file modification events with proper path handling"""
        try:
            if not event.is_directory:
                file_path = Path(event.src_path)
                if self.file_reader.is_supported_file(str(file_path)):
                    rel_path = str(file_path.relative_to(self.base_dir))
                    self.pending_changes.add(rel_path)
                    self._schedule_update()
        except Exception as e:
            logger.error(f"Error in file change handler: {e}")

    def update_context(self):
        file_contents = self.file_reader.read_all_files()
        self.query_service.update_context(file_contents)
        logger.info(f"Updated context with {len(file_contents)} files")

def main():
    print("="*50)
    print("DEBUG: Starting main function")
    print("DEBUG: Current working directory:", os.getcwd())
    print("="*50)
    
    # Initialize components with tracking-folder path
    logger.info("Initializing with Ollama Deepseek model...")
    # Use the tracking-folder directory
    tracking_dir = os.path.join(os.getcwd(), "tracking-folder")
    print("DEBUG: Tracking directory path:", tracking_dir)
    print("DEBUG: Tracking directory exists:", os.path.exists(tracking_dir))
    print("="*50)
    
    file_reader = FileReader(tracking_dir)
    query_service = QueryService()

    # Initial context loading
    logger.info("Loading initial file context...")
    event_handler = FileChangeHandler(file_reader, query_service)
    event_handler.update_context()

    # Set up file monitoring for tracking-folder
    observer = Observer()
    observer.schedule(event_handler, path=tracking_dir, recursive=True)
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
    print("Hello World!")
    main()
