# Local Fieldwork Agent / 本地田野调查助手

**Local Fieldwork Agent** is a secure, local-first tool designed for qualitative researchers. It allows you to analyze sensitive interview transcripts and detect PII (Personally Identifiable Information) without uploading data to the cloud.

**Local Fieldwork Agent** 是专为定性研究人员设计的安全、本地优先的工具。它允许您分析敏感的访谈记录并检测 PII（个人身份信息），而无需将数据上传到云端。

---

## 🚀 Quick Start / 快速启动

To run the agent, you need to start the backend AI service (Parallax) and the frontend UI (Streamlit).
要运行此助手，您需要启动后端 AI 服务 (Parallax) 和前端 UI (Streamlit)。

### 1. Start Parallax Backend / 启动 Parallax 后端

Open two terminal windows to run the local LLM service.
打开两个终端窗口来运行本地 LLM 服务。

**Terminal 1 (Scheduler / 调度器):**
```bash
source venv/bin/activate
# Replace with your model name / 替换为您的模型名称
parallax run -m mlx-community/Qwen2.5-0.5B-Instruct -n 1
```

**Terminal 2 (Compute Node / 计算节点):**
```bash
source venv/bin/activate
parallax join
```
*Wait until you see "Model loaded successfully". / 等待直到看到 "Model loaded successfully"。*

### 2. Start Frontend UI / 启动前端 UI

**Terminal 3 (App / 应用):**
```bash
source venv/bin/activate
streamlit run src/fieldwork_agent/app.py
```

Visit `http://localhost:8501` in your browser.
在浏览器中访问 `http://localhost:8501`。

---

## 🛠️ Implementation Principles / 实现原理

### 1. RAG Chat (Retrieval-Augmented Generation) / RAG 对话（检索增强生成）

This feature allows you to "chat" with your interview transcripts.
此功能允许您与访谈记录进行“对话”。

*   **Ingestion / 数据摄入**:
    *   **Loader**: Supports `.txt` and `.pdf` files. / 支持 `.txt` 和 `.pdf` 文件。
    *   **Cleaning**: Custom regex logic cleans up formatting issues common in copy-pasted text (e.g., broken lines). / 自定义正则逻辑清理复制粘贴文本中常见的格式问题（如断行）。
    *   **Chunking**: Uses `RecursiveCharacterTextSplitter` to split text into manageable chunks (default 1000 chars) with overlap to preserve context. / 使用 `RecursiveCharacterTextSplitter` 将文本分割成可管理的块（默认 1000 字符），并保留重叠以保持上下文。
*   **Storage / 存储**:
    *   **Embeddings**: Uses `sentence-transformers/all-MiniLM-L6-v2` (running locally via HuggingFace) to convert text chunks into vector representations. / 使用 `sentence-transformers/all-MiniLM-L6-v2`（通过 HuggingFace 本地运行）将文本块转换为向量表示。
    *   **Vector DB**: Stores vectors in a local `Chroma` database (`./chroma_db`). / 将向量存储在本地 `Chroma` 数据库中 (`./chroma_db`)。
*   **Retrieval & Generation / 检索与生成**:
    *   **Query**: User questions are embedded and compared against the vector store to find the top-k most relevant chunks. / 用户问题被嵌入并与向量库进行比对，以找到前 k 个最相关的块。
    *   **Answer**: The relevant chunks are fed into the local LLM (via Parallax API) as context to generate an accurate answer based *only* on the provided text. / 相关块作为上下文输入到本地 LLM（通过 Parallax API），以仅基于提供的文本生成准确的答案。

### 2. Anonymization Checker / 匿名化检查器

This feature identifies sensitive information to ensure research ethics.
此功能用于识别敏感信息以确保研究伦理。

*   **Zero-Trust UI / 零信任界面**:
    *   Designed with a "Secure Workstation" aesthetic (Red/Yellow/Green zones) to emphasize the gravity of handling PII. / 采用“安全工作站”美学设计（红/黄/绿区域），强调处理 PII 的严肃性。
*   **Detection Logic / 检测逻辑**:
    *   **Mock Mode (Demo) / 模拟模式（演示）**: Currently uses a keyword-based simulation (detects names like "Alex", "Sarah" and "Location") to demonstrate the workflow without heavy compute. / 目前使用基于关键词的模拟（检测 "Alex", "Sarah" 和 "Location" 等名称）来演示工作流，无需大量计算。
    *   **AI Mode (Production Ready) / AI 模式（生产就绪）**: The codebase includes `analyze_text` which sends text chunks to the local LLM. It uses a specialized **System Prompt** acting as a "Sociological Ethics Expert" to identify: / 代码库包含 `analyze_text`，它将文本块发送到本地 LLM。它使用充当“社会学伦理专家”的专用 **System Prompt** 来识别：
        *   **Direct PII**: Names, IDs, Phones. / 直接 PII：姓名、ID、电话。
        *   **High-Risk Combinations**: Rare profession + Specific location (e.g., "The only doctor in Village X"). / 高危组合：稀有职业 + 具体地点（例如，“X 村唯一的医生”）。
    *   **Output**: Returns a structured JSON list of entities, which are then highlighted in the UI. / 返回结构化的实体 JSON 列表，然后在 UI 中高亮显示。
