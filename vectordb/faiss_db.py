import logging
import faiss
import numpy as np
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Document:
    path: str
    content: str
    embedding: list[float]

class FAISSManager:
    def __init__(self, dimension=384):
        self.index = None
        self.documents: list[Document] = []
    
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
    
    def search(self, query_embedding: list[float], k=3):
        """Search for similar documents"""
        if not self.index or not self.documents:
            return [], []
            
        query_array = np.array([query_embedding]).astype('float32')
        D, I = self.index.search(query_array, k)
        results = [(self.documents[i].path, self.documents[i].content) for i in I[0] if i < len(self.documents)]
        return results, D[0]
