import sys
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")

try:
    import langchain
    print(f"langchain version: {langchain.__version__}")
    print(f"langchain file: {langchain.__file__}")
except ImportError as e:
    print(f"Error importing langchain: {e}")

try:
    from langchain.chains import RetrievalQA
    print("Successfully imported RetrievalQA from langchain.chains")
except ImportError as e:
    print(f"Error importing RetrievalQA from langchain.chains: {e}")

try:
    import langchain.chains
    print(f"langchain.chains file: {langchain.chains.__file__}")
except ImportError as e:
    print(f"Error importing langchain.chains: {e}")
