import logging
import faiss
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

@dataclass
class Document:
    path: str
    content: str
    embedding: List[float]

class FAISSManager:
    def __init__(self, dimension=384):
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.file_paths: List[str] = []
        self.embeddings: dict = {}
        self._is_initialized = False
    
    def create_index(self, documents: list[Document]):
        """Create FAISS index from documents with embeddings"""
        if not documents:
            logger.warning("No documents provided")
            return
            
        embeddings = [doc.embedding for doc in documents]
        self.documents = documents
        
        embeddings_array = np.array(embeddings).astype('float32')
        dimension = len(embeddings[0])
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings_array)
        logger.info(f"Created FAISS index with {len(embeddings)} documents")
    
    def add_file(self, filepath: str, content: str):
        """Add file to the FAISS index"""
        try:
            # Generate embedding for the content
            embedding = self.encoder.encode([content])[0]
            
            # Add to FAISS index
            self.index.add(np.array([embedding]).astype('float32'))
            
            # Store filepath and embedding
            self.file_paths.append(filepath)
            self.embeddings[filepath] = embedding
            self._is_initialized = True
            
            logger.info(f"Added embedding for {filepath}")
        except Exception as e:
            logger.error(f"Error adding file to FAISS: {e}")

    def refresh(self):
        """Clear and rebuild the index"""
        try:
            self.index = faiss.IndexFlatL2(self.dimension)
            if self.embeddings:
                embeddings = np.array(list(self.embeddings.values())).astype('float32')
                self.index.add(embeddings)
                self._is_initialized = True
                logger.info(f"Rebuilt index with {len(self.embeddings)} files")
            else:
                self._is_initialized = False
                self._is_initialized = False
                logger.warning("No embeddings available to rebuild index")
        except Exception as e:
            logger.error(f"Error refreshing index: {e}")
            self._is_initialized = False
    
    def search(self, query: str, k: int = 3) -> List[Tuple[str, float]]:
        """Search for similar files with better error handling"""
        try:
            if not self._is_initialized or len(self.file_paths) == 0:
                logger.warning("FAISS index is empty or not initialized")
                return []

            # Generate query embedding
            query_vector = self.encoder.encode([query])[0]
            
            # Limit k to available files
            k = min(k, len(self.file_paths))
            if k == 0:
                return []
                
            distances, indices = self.index.search(
                np.array([query_vector]).astype('float32'), 
                k
            )
            
            results = []
            for idx, dist in zip(indices[0], distances[0]):
                if idx >= 0 and idx < len(self.file_paths):
                    similarity = 1 / (1 + dist)
                    results.append((self.file_paths[idx], similarity))
            
            return results

        except Exception as e:
            logger.error(f"Error searching FAISS: {e}")
            return []
