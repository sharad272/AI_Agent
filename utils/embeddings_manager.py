import os
import json
import hashlib
from typing import Dict, Optional

class EmbeddingsManager:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.embeddings_dir = os.path.join(base_dir, '.embeddings')
        self.hash_file = os.path.join(self.embeddings_dir, 'file_hashes.json')
        self._file_hashes: Dict[str, str] = {}
        self._load_hashes()
        
    def _load_hashes(self):
        """Load saved file hashes"""
        if os.path.exists(self.hash_file):
            with open(self.hash_file, 'r') as f:
                self._file_hashes = json.load(f)
                
    def _save_hashes(self):
        """Save current file hashes"""
        os.makedirs(self.embeddings_dir, exist_ok=True)
        with open(self.hash_file, 'w') as f:
            json.dump(self._file_hashes, f)

    def file_changed(self, filepath: str, content: str) -> bool:
        """Check if file content has changed"""
        current_hash = hashlib.md5(content.encode()).hexdigest()
        stored_hash = self._file_hashes.get(filepath)
        
        if stored_hash != current_hash:
            self._file_hashes[filepath] = current_hash
            self._save_hashes()
            return True
        return False

    def remove_file(self, filepath: str):
        """Remove file hash when file is deleted"""
        if filepath in self._file_hashes:
            del self._file_hashes[filepath]
            self._save_hashes()
