import os
import logging
from pathlib import Path
from typing import Dict, Optional
from vectordb.faiss_db import FAISSManager

logger = logging.getLogger(__name__)

class FileReader:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)  # Convert to Path object
        self.supported_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.json', '.md', '.txt'}
        self._file_contents: Dict[str, str] = {}
        self.vector_store = FAISSManager()  # Initialize vector store

    def is_supported_file(self, file_path: str) -> bool:
        """Check if file type is supported with better path handling"""
        try:
            if isinstance(file_path, str):
                path = Path(file_path)
            else:
                path = file_path
            return path.suffix.lower() in self.supported_extensions
        except Exception as e:
            logger.error(f"Error checking file type for {file_path}: {e}")
            return False

    def get_relative_path(self, full_path: str) -> str:
        """Convert full path to relative path from base directory"""
        return os.path.relpath(full_path, self.base_dir)

    def read_all_files(self) -> Dict[str, str]:
        """Read and index all files"""
        file_contents = {}
        try:
            logger.info(f"Starting file indexing from: {self.base_dir}")
            
            # First collect all files
            for root, dirs, files in os.walk(self.base_dir):
                # Skip hidden directories and common exclude paths
                dirs[:] = [d for d in dirs if not d.startswith('.') and 
                          d not in {'__pycache__', 'node_modules', 'venv', '.git'}]
                
                for file in files:
                    full_path = os.path.join(root, file)
                    if self.is_supported_file(full_path):
                        try:
                            with open(full_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            relative_path = self.get_relative_path(full_path)
                            file_contents[relative_path] = content
                            # Index the file in vector store
                            self.vector_store.add_file(relative_path, content)
                            logger.info(f"Indexed file: {relative_path}")
                        except Exception as e:
                            logger.error(f"Error reading file {full_path}: {str(e)}")

            # Log indexing results
            logger.info(f"Completed indexing {len(file_contents)} files")
            return file_contents

        except Exception as e:
            logger.error(f"Error reading directory tree: {str(e)}")
            return {}

    def read_file(self, file_path: str) -> str:
        """Read content of a specific file"""
        full_path = os.path.join(self.base_dir, file_path)
        try:
            if os.path.exists(full_path) and self.is_supported_file(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
        return ""

    def get_file_content(self, filepath: str) -> Optional[str]:
        """Get file content either from cache or disk"""
        try:
            # Try cache first
            if filepath in self._file_contents:
                return self._file_contents[filepath]

            # Read from disk if needed
            full_path = self.base_dir / filepath
            if full_path.exists() and self.is_supported_file(str(full_path)):
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self._file_contents[filepath] = content
                return content
        except Exception as e:
            logger.error(f"Error reading {filepath}: {e}")
        return None
