# Local Fieldwork Agent (基于 Parallax & Qwen2.5)

**Local Fieldwork Agent** 是一个专为社会学田野调查和定性研究设计的本地化 AI 助手。它结合了 **RAG (检索增强生成)** 和 **隐私匿名化检查** 功能，帮助研究者在确保数据绝对安全（完全本地运行）的前提下，高效地分析访谈资料。

## ✨ 核心功能 (Features)

### 1. 💬 RAG Chat (访谈对话助手)
- **基于资料回答**: 上传访谈稿（PDF/TXT），AI 会严格基于文档内容回答你的问题。
- **来源溯源**: 每一个回答都会附带原文出处（Source Context），方便核对。
- **参数可调**: 支持动态调整 Chunk Size（切分大小）、Temperature（创造力）和 Top-K（检索数量）。

### 2. 🛡️ Anonymization Checker (匿名化检查器)
- **隐私风险识别**: 自动识别文本中的 **PII (个人身份信息)**（如姓名、日期、地点）。
- **高危组合预警**: 识别可能导致身份暴露的**高危信息组合**（如“稀有职业 + 唯一地点”）。
- **智能高亮**: 使用红/橙/黄三色高亮显示不同等级的风险，并提供风险原因说明。
- **自定义规则**: 内置社会学伦理专家 Prompt，并支持用户自定义 System Prompt 和排除规则。
- **PDF 智能清洗**: 自动修复 PDF 复制时的断行问题。

### 3. 🔒 完全本地化 (Local & Secure)
- **数据不出域**: 所有文件处理、向量存储（ChromaDB）和模型推理（Qwen2.5-7B）均在本地 Mac 上完成。
- **无需联网**: 模型下载完成后，运行时无需互联网连接。

---

## 🛠️ 系统架构 (Architecture)

本系统基于 **Parallax** 分布式推理框架运行，包含三个组件：

1.  **Scheduler (调度器)**: 负责接收请求并分发任务。
2.  **Node (计算节点)**: 加载 Qwen2.5-7B-Instruct (4bit) 模型进行推理。
3.  **Streamlit App (用户界面)**: 提供交互式 Web 界面。

---

## 🚀 快速开始 (Quick Start)

### 1. 环境准备
- **硬件**: Mac M1/M2/M3 Pro/Max (推荐 32GB+ 内存)。
- **Python**: 3.10+

### 2. 启动步骤
你需要打开 **3 个终端窗口**，按顺序运行以下命令：

#### Terminal 1: 启动调度器
```bash
./start_qwen25_7b.sh
```
*等待直到看到 `Serving at localhost:3001`。*

#### Terminal 2: 启动计算节点
```bash
./start_node.sh
```
*等待直到看到 `Ready` 或连接成功日志。*

#### Terminal 3: 启动用户界面
```bash
streamlit run src/fieldwork_agent/app.py
```
*浏览器会自动打开 `http://localhost:8501`。*

---

## 📖 使用指南

### 切换模式
在左侧边栏的 **Navigation** 中切换功能：

#### 💬 RAG Chat 模式
1.  **上传**: 在左侧上传访谈稿。
2.  **索引**: 点击 "Index Document"。
3.  **提问**: 在主界面输入问题。
4.  **调整**: 随时在左侧调整 Temperature 或 Top-K 来优化回答。

#### 🛡️ Anonymization Checker 模式
1.  **输入**: 上传文件或直接粘贴文本。
2.  **配置**: 在左侧 "Prompt Configuration" 中可以查看或修改检查规则。
3.  **分析**: 点击 "Analyze Risks"。
4.  **查看**: 
    -   **表格**: 查看结构化的风险列表。
    -   **句子**: 快速浏览包含风险的句子。
    -   **原文**: 展开查看带有高亮标记的全文（悬停可看原因）。

---

## ⚠️ 常见问题
- **内存不足 (OOM)**: 如果遇到 `Insufficient Memory` 错误，请尝试减小 **Top-K Retrieval** 的值（建议 5-10）。
- **数据库错误**: 如果遇到 `Could not connect to tenant`，系统会自动重置数据库，你只需重新 Index 文档即可。
