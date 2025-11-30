import streamlit as st
import os

from langchain_community.callbacks import StreamlitCallbackHandler

# Set HuggingFace mirror for China access (must be before other imports)
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
# Suppress tokenizers parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"
from rag_engine import process_file, get_vectorstore, get_qa_chain
from anonymizer import analyze_text, highlight_text, extract_risky_sentences, DEFAULT_SYSTEM_PROMPT, DEFAULT_USER_PROMPT_TEMPLATE
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
elif mode == "🛡️ Anonymization Checker":
    st.header("🛡️ Anonymization Checker")
    st.markdown("Identify PII (names, dates, locations) and high-risk combinations in your text.")
    
    # Sidebar for Anonymizer
    with st.sidebar:
        st.header("Anonymizer Settings")
        
        # Chunking Settings for Anonymizer
        with st.expander("⚙️ Chunking Settings", expanded=False):
            anon_chunk_size = st.slider("Chunk Size", 500, 5000, 3000, 100, help="Size of text chunks for analysis.")
            anon_chunk_overlap = st.slider("Chunk Overlap", 0, 1000, 500, 50, help="Overlap between chunks.")
        
        # Prompt Settings
        with st.expander("📝 Prompt Configuration", expanded=False):
            system_prompt = st.text_area("System Prompt", value=DEFAULT_SYSTEM_PROMPT, height=150)
            user_prompt_template = st.text_area("User Prompt Template", value=DEFAULT_USER_PROMPT_TEMPLATE, height=300)

        anon_file = st.file_uploader("Upload File for Analysis", type=["txt", "pdf"], key="anon_upload")

    # Main Area
    if anon_file:
        if st.button("Analyze File Risks"):
            with st.spinner("Processing file and analyzing risks..."):
                # Save file temporarily
                file_path = save_uploaded_file(anon_file)
                
                if file_path:
                    try:
                        # Process and Chunk using rag_engine's utility
                        chunks = process_file(file_path, chunk_size=anon_chunk_size, chunk_overlap=anon_chunk_overlap)
                        st.info(f"File split into {len(chunks)} chunks for analysis.")
                        
                        # Analyze each chunk
                        for i, chunk in enumerate(chunks):
                            with st.expander(f"Chunk {i+1} Analysis", expanded=True):
                                st.text(f"Content Preview: {chunk.page_content[:100]}...")
                                
                                results = analyze_text(chunk.page_content, system_prompt=system_prompt, user_prompt_template=user_prompt_template)
                                
                                # Check for errors
                                if results and "error" in results[0]:
                                    st.error("Analysis Failed or returned non-JSON format.")
                                    st.warning("Raw Output from AI:")
                                    st.code(results[0].get("raw_content", results[0]["error"]))
                                else:
                                    # 1. Sensitive Info Table
                                    st.markdown("#### 1. 敏感信息表格")
                                    if results:
                                        st.table(results)
                                    else:
                                        st.success("No PII detected in this chunk.")

                                    # 2. Risky Sentences List
                                    st.markdown("#### 2. 涉及敏感信息的句子")
                                    risky_sents = extract_risky_sentences(chunk.page_content, results)
                                    if risky_sents:
                                        for idx, sent in enumerate(risky_sents, 1):
                                            st.markdown(f"**{idx}.** {sent}")
                                    else:
                                        st.info("No specific risky sentences found.")

                                    # 3. Original Text (Collapsed)
                                    with st.expander("3. 原文查看 (点击展开)", expanded=False):
                                        highlighted_html = highlight_text(chunk.page_content, results)
                                        st.markdown(highlighted_html, unsafe_allow_html=True)
                                        
                                        # Legend
                                        st.markdown("""
                                        **Legend:**
                                        <span style="color: #d32f2f; font-weight: bold;">High Risk</span>
                                        <span style="color: #f57c00; font-weight: bold;">Medium Risk</span>
                                        <span style="color: #827717; font-weight: bold;">Low Risk</span>
                                        """, unsafe_allow_html=True)
                                        
                    except Exception as e:
                        st.error(f"An error occurred: {e}")
                    finally:
                        cleanup_temp_file(file_path)
    else:
        # Fallback to text area if no file uploaded
        anonymize_input = st.text_area("Or Paste Text Here:", height=200)
        if st.button("Analyze Pasted Text"):
             if anonymize_input:
                with st.spinner("Analyzing text..."):
                    results = analyze_text(anonymize_input, system_prompt=system_prompt, user_prompt_template=user_prompt_template)
                    if results and "error" in results[0]:
                        st.error("Analysis Failed.")
                        st.code(results[0].get("raw_content", results[0]["error"]))
                    else:
                        # 1. Table
                        st.markdown("#### 1. 敏感信息表格")
                        st.table(results)
                        
                        # 2. Sentences
                        st.markdown("#### 2. 涉及敏感信息的句子")
                        risky_sents = extract_risky_sentences(anonymize_input, results)
                        if risky_sents:
                            for idx, sent in enumerate(risky_sents, 1):
                                st.markdown(f"**{idx}.** {sent}")
                        
                        # 3. Original Text
                        with st.expander("3. 原文查看 (点击展开)", expanded=False):
                            highlighted_html = highlight_text(anonymize_input, results)
                            st.markdown(highlighted_html, unsafe_allow_html=True)
                            
                            st.markdown("""
                            **Legend:**
                            <span style="color: #d32f2f; font-weight: bold;">High Risk</span>
                            <span style="color: #f57c00; font-weight: bold;">Medium Risk</span>
                            <span style="color: #827717; font-weight: bold;">Low Risk</span>
                            """, unsafe_allow_html=True)
             else:
                 st.warning("Please upload a file or paste text.")
