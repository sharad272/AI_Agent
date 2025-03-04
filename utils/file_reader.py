import os
from pathlib import Path
import logging
from typing import Dict, Set, Optional
import fnmatch
from vectordb.faiss_db import FAISSManager
from utils.embeddings_manager import EmbeddingsManager

logger = logging.getLogger(__name__)

class FileReader:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.supported_extensions = {'.py', '.js', '.ts', '.json', '.md'}
        self.ignore_patterns = {
            '.*',
            '__pycache__',
            'node_modules',
            '.git',
            '.vectordb',
            '*.pyc'
        }
        self._file_cache: Dict[str, float] = {}  # filepath -> mtime
        self._content_cache: Dict[str, str] = {}  # filepath -> content
        self.vector_store = FAISSManager()  # Initialize vector store
        self.embeddings_manager = EmbeddingsManager(base_dir)

    def is_supported_file(self, filepath: str) -> bool:
        """Check if file should be processed"""
        path = Path(filepath)
        
        # Check if file matches ignore patterns
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(path.name, pattern):
                return False
        
        return path.suffix in self.supported_extensions

    def read_all_files(self) -> Dict[str, str]:
        """Read all files and update embeddings if changed"""
        result = {}
        current_files = set()

        try:
            for filepath in self.base_dir.rglob('*'):
                if not filepath.is_file():
                    continue
                
                rel_path = str(filepath.relative_to(self.base_dir))
                current_files.add(rel_path)
                
                if not self.is_supported_file(filepath):
                    continue

                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    result[rel_path] = content
                    
                    # Update embeddings if content changed
                    if self.embeddings_manager.file_changed(rel_path, content):
                        self.vector_store.add_file(rel_path, content)
                        logger.info(f"Updated embeddings for: {rel_path}")

            # Remove deleted files
            for filepath in set(self._file_cache.keys()) - current_files:
                self.embeddings_manager.remove_file(filepath)
                self.vector_store.remove_file(filepath)
                logger.info(f"Removed embeddings for deleted file: {filepath}")

            return result

        except Exception as e:
            logger.error(f"Error reading files: {e}")
            return {}

    def get_relative_path(self, full_path: str) -> str:
        """Convert full path to relative path from base directory"""
        return os.path.relpath(full_path, self.base_dir)

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
        """Get file content efficiently using cache"""
        try:
            full_path = self.base_dir / filepath
            if not full_path.exists() or not self.is_supported_file(str(full_path)):
                return None

            mtime = full_path.stat().st_mtime
            cached_mtime = self._file_cache.get(filepath)

            # Return cached content if file hasn't changed
            if cached_mtime is not None and mtime <= cached_mtime:
                return self._content_cache.get(filepath)

            # Read and cache if file is new or modified
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self._file_cache[filepath] = mtime
                self._content_cache[filepath] = content
                return content

        except Exception as e:
            logger.error(f"Error reading {filepath}: {e}")
            return None
