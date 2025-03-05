import os
import hashlib
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class FileChangeDetector:
    def __init__(self, directory: str):
        self.directory = directory
        self.file_hashes: Dict[str, str] = {}
        self._initialize_hashes()

    def _initialize_hashes(self):
        """Initialize file hashes"""
        for file in os.listdir(self.directory):
            if file.endswith('.py'):
                path = os.path.join(self.directory, file)
                self.file_hashes[file] = self._get_file_hash(path)

    def _get_file_hash(self, filepath: str) -> str:
        """Get MD5 hash of file content"""
        try:
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.error(f"Error hashing file {filepath}: {e}")
            return ""

    def get_changed_files(self) -> Dict[str, str]:
        """Return dictionary of changed files and their content"""
        changed_files = {}
        for file in os.listdir(self.directory):
            if file.endswith('.py'):
                path = os.path.join(self.directory, file)
                current_hash = self._get_file_hash(path)
                
                if file not in self.file_hashes or self.file_hashes[file] != current_hash:
                    try:
                        with open(path, 'r') as f:
                            changed_files[file] = f.read()
                        self.file_hashes[file] = current_hash
                    except Exception as e:
                        logger.error(f"Error reading changed file {file}: {e}")
                        
        return changed_files
