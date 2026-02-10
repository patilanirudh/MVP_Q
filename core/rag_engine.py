import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
import logging
from typing import List, Dict
from .config import Config

logging.basicConfig(
    filename=Config.LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class RAGEngine:
    def __init__(self):
        self.client = chromadb.Client()
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=Config.EMBEDDING_MODEL
        )
        self.collection = None
        
    def load_sop(self, filepath: str):
        """Load SOP document into vector database"""
        try:
            logging.info(f"Loading SOP from {filepath}")
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            chunks = self._chunk_document(content)
            
            self.collection = self.client.get_or_create_collection(
                name=Config.CHROMA_COLLECTION,
                embedding_function=self.embedding_function
            )
            
            self.collection.add(
                documents=chunks,
                ids=[f"chunk_{i}" for i in range(len(chunks))],
                metadatas=[{"source": "sop_expenses", "chunk_index": i} for i in range(len(chunks))]
            )
            
            logging.info(f"Loaded {len(chunks)} chunks into vector database")
            return len(chunks)
            
        except Exception as e:
            logging.error(f"Error loading SOP: {str(e)}")
            raise
    
    def _chunk_document(self, content: str, chunk_size: int = 500) -> List[str]:
        """Split document into chunks by sections"""
        sections = content.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for section in sections:
            if len(current_chunk) + len(section) < chunk_size:
                current_chunk += section + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = section + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def query(self, query_text: str, n_results: int = 3) -> List[str]:
        """Query vector database for relevant SOP chunks"""
        try:
            if not self.collection:
                self.collection = self.client.get_collection(
                    name=Config.CHROMA_COLLECTION,
                    embedding_function=self.embedding_function
                )
            
            logging.info(f"Querying RAG for: {query_text}")
            
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            
            documents = results['documents'][0] if results['documents'] else []
            logging.info(f"Found {len(documents)} relevant chunks")
            
            return documents
            
        except Exception as e:
            logging.error(f"Error querying RAG: {str(e)}")
            return []