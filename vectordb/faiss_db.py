import logging
import faiss
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional
from sentence_transformers import SentenceTransformer
from datetime import datetime
import os
import pickle
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Document:
    path: str
    content: str
    embedding: List[float]
    timestamp: datetime = None
    doc_type: str = "code"  # code, conversation, or memory

class FAISSManager:
    def __init__(self, dimension=384, n_lists=1):
        try:
            logger.info("Initializing FAISS Manager...")
            self.dimension = dimension
            self.storage_path = os.path.join(os.getcwd(), "vectordb")
            self.index_path = os.path.join(self.storage_path, "faiss.index")
            self.metadata_path = os.path.join(self.storage_path, "metadata.pkl")
            
            # Initialize basic structures
            self.document_store = {}
            self.file_paths = []
            self.embeddings = {}
            self._embedding_buffer = []
            self.buffer_size = 50
            self._encoder = None  # Lazy load
            
            # Add missing attributes
            self.trained = False
            self.use_ivf = False
            
            # Create storage directory if needed
            if not os.path.exists(self.storage_path):
                os.makedirs(self.storage_path)
            
            # Create minimal FAISS index
            self.index = faiss.IndexFlatL2(dimension)
            
            # Load existing index if available
            if os.path.exists(self.index_path):
                self._load_from_disk()
            
            logger.info("Basic FAISS initialization complete")
            
        except Exception as e:
            logger.error(f"Error initializing FAISS Manager: {e}")
            raise

    @property
    def encoder(self):
        """Lazy load the encoder only when needed"""
        if self._encoder is None:
            logger.info("Loading sentence transformer model...")
            self._encoder = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
        return self._encoder

    def _load_from_disk(self) -> bool:
        """Load index and metadata from disk"""
        try:
            if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
                # Load index
                self.index = faiss.read_index(self.index_path)
                
                # Load metadata
                with open(self.metadata_path, 'rb') as f:
                    metadata = pickle.load(f)
                    self.document_store = metadata['document_store']
                    self.file_paths = metadata['file_paths']
                    self.embeddings = metadata['embeddings']
                    self.trained = metadata.get('trained', False)
                    self.use_ivf = metadata.get('use_ivf', False)
                
                # Remove direct encoder initialization - it will be lazy loaded when needed
                return True
        except Exception as e:
            logger.error(f"Error loading index from disk: {e}")
            return False
        return False

    def _save_to_disk(self):
        """Save index and metadata to disk"""
        try:
            # Save index
            faiss.write_index(self.index, self.index_path)
            
            # Save metadata
            metadata = {
                'document_store': self.document_store,
                'file_paths': self.file_paths,
                'embeddings': self.embeddings,
                'trained': self.trained,
                'use_ivf': self.use_ivf
            }
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(metadata, f)
                
            logger.info("Saved FAISS index and metadata to disk")
        except Exception as e:
            logger.error(f"Error saving index to disk: {e}")

    def _maybe_upgrade_index(self, num_vectors):
        """Upgrade to IVF index if we have enough vectors"""
        if num_vectors >= 40 and not self.use_ivf:  # Only upgrade for larger datasets
            try:
                # Create IVF index
                self.quantizer = faiss.IndexFlatL2(self.dimension)
                n_lists = min(4, num_vectors // 10)  # Adjust n_lists based on data size
                new_index = faiss.IndexIVFFlat(
                    self.quantizer,
                    self.dimension,
                    n_lists,
                    faiss.METRIC_L2
                )
                
                # Transfer existing vectors if any
                if len(self.embeddings) > 0:
                    vectors = np.array(list(self.embeddings.values())).astype('float32')
                    new_index.train(vectors)
                    new_index.add(vectors)
                
                self.index = new_index
                self.use_ivf = True
                self.trained = True
                logger.info(f"Upgraded to IVF index with {n_lists} lists")
                
            except Exception as e:
                logger.warning(f"Failed to upgrade index: {e}, continuing with flat index")

    def _train_index(self, vectors):
        """Train the index if not already trained"""
        if not self.trained and len(vectors) > 0:
            try:
                if len(vectors) < self.index.nlist:
                    # If we have fewer vectors than clusters, adjust nlist
                    self.index = faiss.IndexIVFFlat(
                        self.quantizer,
                        self.dimension,
                        max(1, len(vectors) // 2),
                        faiss.METRIC_L2
                    )
                
                self.index.train(vectors)
                self.trained = True
                self.index.nprobe = min(20, self.index.nlist)  # Optimize search parameters
            except Exception as e:
                logger.error(f"Error training index: {e}")

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
    
    def add_file(self, filepath: str, content: str, language: str = None):
        """Add file with optimized processing"""
        try:
            logger.debug(f"Adding file to vector DB: {filepath}")
            # Generate embedding using SentenceTransformer
            embedding = self.encoder.encode([content])[0]
            
            # Add to buffer for batch processing
            self._embedding_buffer.append(embedding)
            self.file_paths.append(filepath)
            self.embeddings[filepath] = embedding
            self.document_store[filepath] = {
                'language': language,
                'timestamp': datetime.now()
            }
            
            # Process buffer if full - this is where actual indexing happens
            if len(self._embedding_buffer) >= self.buffer_size:
                logger.debug("Processing embedding buffer...")
                self._process_buffer()  # This adds embeddings to FAISS index
                self._save_to_disk()    # This saves the index to disk
                
            logger.debug(f"Successfully added file: {filepath}")
            
        except Exception as e:
            logger.error(f"Error adding file to FAISS: {e}")

    def _process_buffer(self):
        """Process accumulated embeddings"""
        if not self._embedding_buffer:
            return
            
        vectors = np.array(self._embedding_buffer).astype('float32')
        
        # Check if we should upgrade the index
        total_vectors = len(self.embeddings) + len(self._embedding_buffer)
        self._maybe_upgrade_index(total_vectors)
        
        # Add vectors to index
        try:
            if self.use_ivf and not self.trained:
                self.index.train(vectors)
                self.trained = True
            self.index.add(vectors)
            self._embedding_buffer = []
        except Exception as e:
            logger.error(f"Error processing buffer: {e}")

    def add_dynamic_content(self, content: str, doc_type: str, metadata: dict = None):
        """Add dynamic content with automatic updating"""
        try:
            doc_id = f"{doc_type}_{datetime.now().timestamp()}"
            embedding = self.encoder.encode([content])[0]
            
            # Store document info
            self.document_store[doc_id] = {
                'content': content,
                'type': doc_type,
                'timestamp': datetime.now(),
                'metadata': metadata or {}
            }
            
            # Add to FAISS index
            self.index.add(np.array([embedding]).astype('float32'))
            self.file_paths.append(doc_id)
            self.embeddings[doc_id] = embedding
            
            self.last_update = datetime.now()
            return doc_id
            
        except Exception as e:
            logger.error(f"Error adding dynamic content: {e}")
            return None

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
    
    def search(self, query: str, k: int = 2) -> List[Tuple[str, float]]:
        """Optimized search in vector DB"""
        try:
            # Generate query embedding
            query_vector = self.encoder.encode([query])[0].reshape(1, -1)
            
            # Use approximate search for faster results
            distances, indices = self.index.search(query_vector, k)
            
            # Get results
            results = []
            for i, dist in zip(indices[0], distances[0]):
                if i != -1:  # Valid index
                    file_path = self.file_paths[i]
                    # Convert distance to similarity score
                    score = 1 / (1 + dist)
                    results.append((file_path, score))
            
            return results
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def search_by_type(self, query: str, doc_type: str = None, k: int = 3) -> List[Tuple[str, float, dict]]:
        """Search with optional type filtering"""
        results = self.search(query, k=k)
        if doc_type:
            return [(id, score, self.document_store[id]) 
                   for id, score in results 
                   if id in self.document_store 
                   and self.document_store[id]['type'] == doc_type]
        return [(id, score, self.document_store[id]) 
                for id, score in results 
                if id in self.document_store]

    def __del__(self):
        """Cleanup method"""
        try:
            # Process any remaining embeddings before destruction
            self._process_buffer()
            self._save_to_disk()
        except:
            pass

    def flush(self):
        """Force process any remaining embeddings in buffer"""
        if self._embedding_buffer:
            logger.info(f"Flushing {len(self._embedding_buffer)} remaining embeddings to index")
            self._process_buffer()
            self._save_to_disk()

    def add_to_index(self, filepath: str, embedding: np.ndarray, language: str = None):
        """Add pre-generated embedding to index - optimized version"""
        try:
            # Add directly to index if buffer is full
            if len(self._embedding_buffer) >= self.buffer_size:
                vectors = np.array(self._embedding_buffer + [embedding]).astype('float32')
                self.index.add(vectors)
                self._embedding_buffer = []
                self._save_to_disk()
            else:
                self._embedding_buffer.append(embedding)
            
            # Store metadata
            self.file_paths.append(filepath)
            self.embeddings[filepath] = embedding
            self.document_store[filepath] = {
                'language': language,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error adding embedding to index: {e}")

    def finalize_index(self):
        """Finalize the index after all embeddings are added"""
        try:
            # Process any remaining embeddings
            if self._embedding_buffer:
                self._process_buffer()
            
            # Save to disk
            self._save_to_disk()
            logger.info(f"Finalized index with {len(self.file_paths)} files")
            
        except Exception as e:
            logger.error(f"Error finalizing index: {e}")
