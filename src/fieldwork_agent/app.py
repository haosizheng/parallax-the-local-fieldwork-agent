import streamlit as st
import os

from langchain_community.callbacks import StreamlitCallbackHandler

# Set HuggingFace mirror for China access (must be before other imports)
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
# Suppress tokenizers parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"
from rag_engine import process_file, get_vectorstore, get_qa_chain
from anonymizer import analyze_text, highlight_text, extract_risky_sentences, DEFAULT_SYSTEM_PROMPT, DEFAULT_USER_PROMPT_TEMPLATE, mock_anonymize
from utils import save_uploaded_file, cleanup_temp_file

st.set_page_config(page_title="Local Fieldwork Agent", layout="wide")

st.title("Local Fieldwork Agent 🕵️‍♂️")
st.markdown("### Secure, Local RAG for Qualitative Research")

# Sidebar Navigation
mode = st.sidebar.radio("Navigation", ["💬 RAG Chat", "🛡️ Anonymization Checker"])

# --- MODE 1: RAG Chat ---
if mode == "💬 RAG Chat":
    # Sidebar for File Upload (Only relevant for RAG)
    with st.sidebar:
        st.header("RAG Data Input")
        
        # Indexing Settings
        with st.expander("⚙️ Indexing Settings", expanded=False):
            chunk_size = st.slider("Chunk Size", 100, 2000, 1000, 100, help="Size of text chunks in characters.")
            chunk_overlap = st.slider("Chunk Overlap", 0, 500, 200, 50, help="Overlap between chunks to maintain context.")

        # Generation Settings
        with st.expander("🤖 Generation Settings", expanded=False):
            temperature = st.slider("Temperature", 0.0, 1.0, 0.6, 0.1, help="Creativity of the model. Higher = more creative.")
            top_k = st.slider("Top-K Retrieval", 1, 30, 5, 1, help="Number of document chunks to retrieve.")

        uploaded_file = st.file_uploader("Upload Interview Transcript", type=["txt", "pdf"], key="rag_upload")
        
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
                # Note: temperature and top_k are defined in the sidebar block above for this mode
                # We need to ensure they are accessible here. Python scoping in 'if' blocks allows this.
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

# --- MODE 2: Anonymization Checker ---
# --- MODE 2: Anonymization Checker ---
elif mode == "🛡️ Anonymization Checker":
    # --- ZERO-TRUST CSS STYLING ---
    st.markdown("""
    <style>
        /* Monospace font for the entire section */
        .stTextArea textarea, .stCode, .stMarkdown {
            font-family: 'Courier New', Courier, monospace !important;
        }
        
        /* Pane Titles */
        .pane-title-red {
            color: #ff4b4b;
            border-bottom: 2px solid #ff4b4b;
            padding-bottom: 5px;
            font-weight: bold;
            font-size: 1.2em;
            margin-bottom: 10px;
        }
        .pane-title-yellow {
            color: #ffa726;
            border-bottom: 2px solid #ffa726;
            padding-bottom: 5px;
            font-weight: bold;
            font-size: 1.2em;
            margin-bottom: 10px;
        }
        .pane-title-green {
            color: #00c853;
            border-bottom: 2px solid #00c853;
            padding-bottom: 5px;
            font-weight: bold;
            font-size: 1.2em;
            margin-bottom: 10px;
        }
    </style>
    """, unsafe_allow_html=True)

    st.title("PII REDACTION PROTOCOL: ZERO-TRUST WORKSTATION")
    st.markdown("### 🔒 SECURE ENVIRONMENT ACTIVE | NETWORK ISOLATED")
    
    # Sidebar for File Upload (to populate session state)
    with st.sidebar:
        st.header("Data Ingestion")
        anon_file = st.file_uploader("Upload Raw Transcript", type=["txt", "pdf"], key="anon_upload")
        
        if anon_file:
            # Load file content into session state
            file_path = save_uploaded_file(anon_file)
            if file_path:
                try:
                    # Simple read for txt, for pdf we might need more logic but let's assume txt for this demo or use existing loader
                    # Re-using process_file to get text is safest but returns chunks. 
                    # For this specific UI, let's just read the full text if possible or join chunks.
                    chunks = process_file(file_path, chunk_size=10000, chunk_overlap=0)
                    full_text = "\n".join([c.page_content for c in chunks])
                    st.session_state.raw_transcript = full_text
                except Exception as e:
                    st.error(f"Error reading file: {e}")
                finally:
                    cleanup_temp_file(file_path)
    
    # Main 3-Pane Layout
    col1, col2, col3 = st.columns(3)
    
    # --- PANE 1: INPUT ---
    with col1:
        st.markdown('<div class="pane-title-red">INPUT: RAW SENSITIVE DATA (WARNING)</div>', unsafe_allow_html=True)
        
        # Check if data exists
        if "raw_transcript" not in st.session_state:
            st.session_state.raw_transcript = ""
            
        # Text Area for Input
        raw_input = st.text_area("Raw Data Stream", value=st.session_state.raw_transcript, height=400, key="raw_input_area")
        
        # Update session state if user types directly
        if raw_input != st.session_state.raw_transcript:
            st.session_state.raw_transcript = raw_input

    # --- PANE 2: STATUS ---
    with col2:
        st.markdown('<div class="pane-title-yellow">PII ENTITY STATUS</div>', unsafe_allow_html=True)
        
        # Initialize state for results
        if "redaction_results" not in st.session_state:
            st.session_state.redaction_results = None
            
        # Button
        if st.button("INITIATE REDACTION", type="primary", use_container_width=True):
            if st.session_state.raw_transcript:
                with st.spinner("SCANNING FOR PII..."):
                    redacted, count, log = mock_anonymize(st.session_state.raw_transcript)
                    st.session_state.redaction_results = {
                        "redacted": redacted,
                        "count": count,
                        "log": log
                    }
            else:
                st.warning("NO DATA DETECTED")

        # Display Results if available
        if st.session_state.redaction_results:
            count = st.session_state.redaction_results["count"]
            log = st.session_state.redaction_results["log"]
            
            st.metric("Total PII Entities Detected", count)
            
            st.markdown("**Detection Log:**")
            st.code(log, language="text")
            
            if count > 0:
                st.success("THREATS NEUTRALIZED")
            else:
                st.info("NO THREATS FOUND")

    # --- PANE 3: OUTPUT ---
    with col3:
        st.markdown('<div class="pane-title-green">OUTPUT: CLEANED DATA (SECURE)</div>', unsafe_allow_html=True)
        
        output_text = ""
        if st.session_state.redaction_results:
            output_text = st.session_state.redaction_results["redacted"]
            
        st.text_area("Secure Data Stream", value=output_text, height=400, key="secure_output_area", disabled=True)
