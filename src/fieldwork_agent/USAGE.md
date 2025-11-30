# Local Fieldwork Agent - 使用指南

## 🌟 架构原理 (How it works)

这个系统由三个部分组成，像一个餐厅一样运作：

1.  **Parallax 调度器 (前台/经理)**: 
    - **作用**: 负责接收你的请求（点单），并分配给节点处理。
    - **对应**: `start_qwen25.sh`
    - **地址**: `http://localhost:3001`

2.  **Parallax 节点 (厨房/厨师)**:
    - **作用**: 实际加载 AI 模型（Qwen2.5），进行计算（做菜）。
    - **对应**: `start_node.sh`

3.  **Streamlit App (顾客/菜单)**:
    - **作用**: 你看到的界面，负责上传文件和提问。它把问题发给调度器。
    - **对应**: `streamlit run ...`

---

## 🚀 启动步骤 (Startup)

你需要打开 **3 个终端窗口**，按顺序运行：

### 第一步：启动调度器 (Terminal 1)
这是大脑，必须最先启动。
```bash
./start_qwen25.sh
```
*等待直到看到类似 `Serving at localhost:3001` 的提示。*

### 第二步：启动节点 (Terminal 2)
这是肌肉，负责干活。
```bash
./start_node.sh
```
*等待直到看到 `Ready` 或连接成功的提示。*

### 第三步：启动应用 (Terminal 3)
这是界面，最后启动。
```bash
streamlit run src/fieldwork_agent/app.py
```
*浏览器会自动打开 `http://localhost:8501`。*

---

## 📝 使用说明

1.  **上传访谈稿**: 在左侧边栏上传 `.txt` 或 `.pdf` 文件。
2.  **建立索引**: 点击 "Index Document" 按钮。系统会把文本切块并存入本地向量数据库。
3.  **提问**: 在主界面的聊天框输入你的问题。
4.  **查看来源**: AI 回答后，展开 "View Source Context" 可以看到它是根据原文哪一段回答的。
