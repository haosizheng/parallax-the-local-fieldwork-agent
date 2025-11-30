import streamlit as st
import os
from rag_engine import process_file, get_vectorstore, get_qa_chain
from utils import save_uploaded_file, cleanup_temp_file

st.set_page_config(page_title="Local Fieldwork Agent", layout="wide")

st.title("Local Fieldwork Agent 🕵️‍♂️")
st.markdown("### Secure, Local RAG for Qualitative Research")

# Sidebar for File Upload
with st.sidebar:
    st.header("Data Input")
    uploaded_file = st.file_uploader("Upload Interview Transcript", type=["txt", "pdf"])
    
    if uploaded_file is not None:
        if st.button("Index Document"):
            with st.spinner("Processing and Indexing..."):
                # Save file temporarily
                file_path = save_uploaded_file(uploaded_file)
                
                if file_path:
                    try:
                        # Process and Chunk
                        chunks = process_file(file_path)
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

# Accept user input
if prompt := st.chat_input("What would you like to know about the interview?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Load existing vectorstore
                vectorstore = get_vectorstore()
                qa_chain = get_qa_chain(vectorstore)
                
                response = qa_chain.invoke({"query": prompt})
                answer = response["result"]
                source_docs = response["source_documents"]
                
                st.markdown(answer)
                
                # Display Sources
                with st.expander("View Source Context"):
                    for i, doc in enumerate(source_docs):
                        st.markdown(f"**Source {i+1}:**")
                        st.markdown(f"> {doc.page_content}")
                        st.markdown("---")
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
            except Exception as e:
                st.error(f"Error generating response: {e}")
                st.info("Make sure you have indexed a document and Parallax is running.")
