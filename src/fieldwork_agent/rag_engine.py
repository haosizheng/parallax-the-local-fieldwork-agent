import os
import shutil
from typing import List, Optional

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain_core.documents import Document

# Constants
CHROMA_PATH = "chroma_db"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
PARALLAX_API_BASE = "http://localhost:3001/v1"
PARALLAX_API_KEY = "EMPTY"  # Parallax/vLLM usually doesn't require a real key for local
MODEL_NAME = "parallax" # Or whatever model name the server expects, often ignored or "default"

import re

def clean_text(text: str) -> str:
    """
    Clean text by merging broken lines while preserving paragraph breaks.
    """
    # 1. Replace multiple newlines (paragraph breaks) with a placeholder
    text = re.sub(r'\n\s*\n', '__PARAGRAPH__', text)
    
    # 2. Merge single newlines
    # For Chinese: Remove newline between Chinese characters
    # Regex: Lookbehind for Chinese, match newline, Lookahead for Chinese
    text = re.sub(r'(?<=[\u4e00-\u9fa5])\n(?=[\u4e00-\u9fa5])', '', text)
    
    # For others (English/Mixed): Replace newline with space
    text = text.replace('\n', ' ')
    
    # 3. Restore paragraph breaks
    text = text.replace('__PARAGRAPH__', '\n\n')
    
    # 4. Collapse multiple spaces (but keep newlines)
    text = re.sub(r'[ \t]+', ' ', text)
    
    return text.strip()

def process_file(file_path: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[Document]:
    """
    Load and chunk a file (PDF or TXT).
    """
    if file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith(".txt"):
        loader = TextLoader(file_path)
    else:
        raise ValueError("Unsupported file type")

    documents = loader.load()
    
    # Clean content of each document
    for doc in documents:
        doc.page_content = clean_text(doc.page_content)
        
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.split_documents(documents)
    return chunks

def get_vectorstore(chunks: Optional[List[Document]] = None, reset: bool = False) -> Chroma:
    """
    Get or create a Chroma vector store.
    If chunks are provided, they are added to the store.
    If reset is True, the existing database is cleared.
    """
    if reset and os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    
    try:
        if chunks:
            vectorstore = Chroma.from_documents(
                documents=chunks,
                embedding=embeddings,
                persist_directory=CHROMA_PATH
            )
        else:
            vectorstore = Chroma(
                persist_directory=CHROMA_PATH,
                embedding_function=embeddings
            )
    except Exception as e:
        # Auto-recovery for corrupted DB
        if "Could not connect to tenant" in str(e) or "sqlite3.OperationalError" in str(e):
            print(f"Detected corrupted database: {e}. Resetting...")
            if os.path.exists(CHROMA_PATH):
                shutil.rmtree(CHROMA_PATH)
            # Retry creation (will be empty if no chunks provided, but prevents crash)
            vectorstore = Chroma(
                persist_directory=CHROMA_PATH,
                embedding_function=embeddings
            )
        else:
            raise e
    
    return vectorstore

def get_qa_chain(vectorstore: Chroma, temperature: float = 0.6, k: int = 5):
    """
    Create a RetrievalQA chain using Parallax as the LLM.
    """
    from langchain.prompts import PromptTemplate

    llm = ChatOpenAI(
        openai_api_base=PARALLAX_API_BASE,
        openai_api_key=PARALLAX_API_KEY,
        model_name=MODEL_NAME,
        temperature=temperature,  # Dynamic temperature
        # Pass repetition_penalty via extra_body (supported by ChatOpenAI as a root arg)
        extra_body={"repetition_penalty": 1.1},
        streaming=True,
    )
    
    retriever = vectorstore.as_retriever(search_kwargs={"k": k}) # Dynamic k
    
    # Custom Prompt Template
    template = """Use the following pieces of context to answer the question at the end. 
    If you don't know the answer, just say that you don't know, don't try to make up an answer. 
    Keep the answer concise.
    
    Context:
    {context}
    
    Question: {question}
    
    Answer:"""
    
    QA_CHAIN_PROMPT = PromptTemplate.from_template(template)

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": QA_CHAIN_PROMPT}
    )
    
    return qa_chain
