import os
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import pypdf

class RAGManager:
    def __init__(self, storage_path="rag_storage"):
        self.storage_path = storage_path
        
        # Initialize ChromaDB
        # Using persistent storage so data survives restarts
        self.client = chromadb.PersistentClient(path=storage_path)
        
        # Initialize Embedding Model
        # all-MiniLM-L6-v2 is fast and effective for this scale
        print("DEBUG: Loading Embedding Model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("DEBUG: Embedding Model Loaded.")

    def _extract_text(self, file_content: bytes, filename: str) -> str:
        """Extracts text from PDF or TXT bytes."""
        try:
            if filename.lower().endswith('.pdf'):
                import io
                pdf_file = io.BytesIO(file_content)
                reader = pypdf.PdfReader(pdf_file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
            else:
                # Assume text file
                return file_content.decode('utf-8', errors='ignore')
        except Exception as e:
            print(f"Error extracting text: {e}")
            return ""

    def _chunk_text(self, text: str, chunk_size=500, overlap=50) -> List[str]:
        """Splits text into overlapping chunks."""
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += chunk_size - overlap
        return chunks

    def process_document(self, file_content: bytes, filename: str, judge_id: str) -> str:
        """
        Processes a document and stores it in a dedicated collection for the judge.
        Returns the collection name.
        """
        collection_name = f"judge_{judge_id}"
        
        # Delete existing collection if it exists (overwrite knowledge)
        try:
            self.client.delete_collection(collection_name)
        except:
            pass
            
        collection = self.client.create_collection(name=collection_name)
        
        # 1. Extract
        text = self._extract_text(file_content, filename)
        if not text:
            raise ValueError("Could not extract text from file.")
            
        # 2. Chunk
        chunks = self._chunk_text(text)
        print(f"DEBUG: Generated {len(chunks)} chunks for {judge_id}")
        
        # 3. Embed & Store
        # We generate IDs for each chunk
        ids = [f"chunk_{i}" for i in range(len(chunks))]
        
        # ChromaDB can compute embeddings automatically if we don't provide them,
        # but we'll do it explicitly to control the model.
        embeddings = self.embedding_model.encode(chunks).tolist()
        
        collection.add(
            documents=chunks,
            embeddings=embeddings,
            ids=ids,
            metadatas=[{"source": filename} for _ in chunks]
        )
        
        return collection_name

    def query_knowledge(self, judge_id: str, query: str, top_k=3) -> List[str]:
        """Retrieves the most relevant text chunks for a query."""
        collection_name = f"judge_{judge_id}"
        try:
            collection = self.client.get_collection(collection_name)
        except:
            print(f"DEBUG: No knowledge base found for {judge_id}")
            return []
            
        query_embedding = self.embedding_model.encode([query]).tolist()
        
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=top_k
        )
        
        # results['documents'] is a list of lists
        if results['documents']:
            return results['documents'][0]
        return []

    def delete_knowledge(self, judge_id: str):
        """Cleans up the collection when a judge is deleted."""
        collection_name = f"judge_{judge_id}"
        try:
            self.client.delete_collection(collection_name)
        except:
            pass

# Singleton instance
rag_manager = RAGManager()
