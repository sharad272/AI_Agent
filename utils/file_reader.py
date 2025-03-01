import os
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class FileReader:
    def __init__(self, base_dir: str):
        self.base_dir = os.path.normpath(base_dir)
        self.supported_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.json', '.md', '.txt'}
        logger.info(f"Initialized FileReader with base directory: {self.base_dir}")

    def is_supported_file(self, file_path: str) -> bool:
        """Check if the file type is supported"""
        return os.path.splitext(file_path)[1].lower() in self.supported_extensions

    def get_relative_path(self, full_path: str) -> str:
        """Convert full path to relative path from base directory"""
        return os.path.relpath(full_path, self.base_dir)

    def read_all_files(self) -> Dict[str, str]:
        """Read all supported files in the directory tree"""
        file_contents = {}
        try:
            logger.info(f"Starting file indexing from: {self.base_dir}")
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
                            logger.info(f"Indexed file: {relative_path}")
                        except Exception as e:
                            logger.error(f"Error reading file {full_path}: {str(e)}")

            logger.info(f"Completed indexing. Found {len(file_contents)} files")
            # Log all indexed files for debugging
            logger.debug("Indexed files:")
            for path in file_contents.keys():
                logger.debug(f"  - {path}")
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
