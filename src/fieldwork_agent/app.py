import streamlit as st
import os

from langchain_community.callbacks import StreamlitCallbackHandler

# Set HuggingFace mirror for China access (must be before other imports)
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
# Suppress tokenizers parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"
from rag_engine import process_file, get_vectorstore, get_qa_chain
from utils import save_uploaded_file, cleanup_temp_file

st.set_page_config(page_title="Local Fieldwork Agent", layout="wide")

st.title("Local Fieldwork Agent 🕵️‍♂️")
st.markdown("### Secure, Local RAG for Qualitative Research")

# Sidebar for File Upload
with st.sidebar:
    st.header("Data Input")
    
    # Indexing Settings
    with st.expander("⚙️ Indexing Settings", expanded=False):
        chunk_size = st.slider("Chunk Size", 100, 2000, 1000, 100, help="Size of text chunks in characters.")
        chunk_overlap = st.slider("Chunk Overlap", 0, 500, 200, 50, help="Overlap between chunks to maintain context.")

    # Generation Settings
    with st.expander("🤖 Generation Settings", expanded=False):
        temperature = st.slider("Temperature", 0.0, 1.0, 0.6, 0.1, help="Creativity of the model. Higher = more creative.")
        top_k = st.slider("Top-K Retrieval", 1, 30, 5, 1, help="Number of document chunks to retrieve.")

    uploaded_file = st.file_uploader("Upload Interview Transcript", type=["txt", "pdf"])
    
    if uploaded_file is not None:
        if st.button("Index Document"):
            with st.spinner("Processing and Indexing..."):
                # Save file temporarily
                file_path = save_uploaded_file(uploaded_file)
                
                if file_path:
                    try:
                        # Process and Chunk
                        chunks = process_file(file_path, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
                        st.info(f"Created {len(chunks)} chunks.")
                        
                        # Create/Update Vector Store
                        get_vectorstore(chunks, reset=True)
                        
                        st.session_state['is_indexed'] = True
                        st.success("Indexing Complete! You can now ask questions.")
                    except Exception as e:
                        st.error(f"An error occurred: {e}")
                    finally:
                        cleanup_temp_file(file_path)

    if st.session_state.get('is_indexed'):
        st.success("✅ Document Indexed and Ready")

# Main Chat Interface
st.header("Ask Questions")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message:
            with st.expander("View Source Context"):
                st.markdown(message["sources"])

# Accept user input
if prompt := st.chat_input("What would you like to know about the interview?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        # Use StreamlitCallbackHandler to show "Thinking" process
        st_callback = StreamlitCallbackHandler(st.container())
        try:
            # Load existing vectorstore
            vectorstore = get_vectorstore()
            qa_chain = get_qa_chain(vectorstore, temperature=temperature, k=top_k)
            
            if top_k > 10:
                st.warning("⚠️ High Top-K (10+) may cause memory issues or slow performance on local devices.")
            
            st.write("Debug: Starting retrieval and generation...")
            
            response = qa_chain.invoke(
                {"query": prompt},
                config={"callbacks": [st_callback]}
            )
            answer = response["result"]
            source_docs = response["source_documents"]
            
            # Note: StreamlitCallbackHandler might have already printed the answer.
            # We print it again cleanly to ensure it's in the history and formatted correctly.
            # If it looks duplicated, we can adjust later, but this ensures persistence.
            st.markdown(answer)
                
            # Format sources
            sources_text = ""
            for i, doc in enumerate(source_docs):
                sources_text += f"**Source {i+1}:**\n> {doc.page_content}\n\n---\n\n"
            
            # Display Sources
            with st.expander("View Source Context"):
                st.markdown(sources_text)
            
            # Add assistant response to chat history with sources
            st.session_state.messages.append({
                "role": "assistant", 
                "content": answer,
                "sources": sources_text
            })
                
        except Exception as e:
            st.error(f"Error generating response: {e}")
            st.info("Make sure you have indexed a document and Parallax is running.")
