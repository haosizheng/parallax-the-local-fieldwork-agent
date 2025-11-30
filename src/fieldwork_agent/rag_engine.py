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

def process_file(file_path: str) -> List[Document]:
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
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
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
    
    return vectorstore

def get_qa_chain(vectorstore: Chroma):
    """
    Create a RetrievalQA chain using Parallax as the LLM.
    """
    from langchain.prompts import PromptTemplate

    llm = ChatOpenAI(
        openai_api_base=PARALLAX_API_BASE,
        openai_api_key=PARALLAX_API_KEY,
        model_name=MODEL_NAME,
        temperature=0.6,  # Higher temperature to reduce loops
        # Pass repetition_penalty via extra_body (supported by ChatOpenAI as a root arg)
        extra_body={"repetition_penalty": 1.1}
    )
    
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5}) # Increase k to get more context
    
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
