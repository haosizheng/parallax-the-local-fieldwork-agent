# Parallax Framework Setup Guide
# Parallax 框架设置指南

This guide explains how to set up the Parallax framework in a new project environment.
本指南说明如何在一个新的项目环境中设置 Parallax 框架。

---

## 1. Prerequisites / 先决条件

Before you begin, ensure you have the following:
开始之前，请确保您具备以下条件：

*   **OS**: macOS (Apple Silicon recommended) or Linux.
    *   **操作系统**: macOS（推荐 Apple Silicon）或 Linux。
*   **Python**: Version 3.10 or higher.
    *   **Python**: 3.10 或更高版本。
*   **Git**: For cloning the repository.
    *   **Git**: 用于克隆仓库。

---

## 2. Installation / 安装

### Step 1: Clone the Repository / 第一步：克隆仓库

If you haven't already, clone the Parallax repository or copy the source code to your project directory.
如果您还没有克隆 Parallax 仓库或将源代码复制到您的项目目录。

```bash
git clone https://github.com/gradient-ai/parallax.git
cd parallax
```

### Step 2: Create a Virtual Environment / 第二步：创建虚拟环境

It is highly recommended to use a virtual environment to manage dependencies.
强烈建议使用虚拟环境来管理依赖项。

```bash
# Create virtual environment / 创建虚拟环境
python3 -m venv venv

# Activate virtual environment / 激活虚拟环境
source venv/bin/activate
```

### Step 3: Install Dependencies / 第三步：安装依赖

Install the package in editable mode with necessary extras (e.g., `dev`, `mac` for macOS).
以可编辑模式安装包及其必要的扩展（例如 macOS 需要 `mac`，开发需要 `dev`）。

```bash
# Upgrade pip first / 首先升级 pip
pip install --upgrade pip

# Install Parallax with dependencies / 安装 Parallax 及其依赖
# For macOS / 适用于 macOS:
pip install -e ".[mac,dev]"

# For Linux / 适用于 Linux:
# pip install -e ".[dev]"
```

---

## 3. Network Configuration (For China Users) / 网络配置（适用于国内用户）

If you are in a region with restricted access to HuggingFace (like mainland China), configure a mirror.
如果您所在的地区访问 HuggingFace 受限（如中国大陆），请配置镜像源。

```bash
# Set HuggingFace Mirror / 设置 HuggingFace 镜像
export HF_ENDPOINT=https://hf-mirror.com

# Increase Timeout / 增加超时时间
export HF_HUB_DOWNLOAD_TIMEOUT=300
```

**Alternative: Use ModelScope / 替代方案：使用 ModelScope**
If HuggingFace is completely inaccessible, use ModelScope.
如果完全无法访问 HuggingFace，请使用 ModelScope。

```bash
pip install modelscope
```

---

## 4. Download a Model / 下载模型

You need a model to run Parallax. We recommend **Qwen2.5-0.5B-Instruct** for testing.
您需要一个模型来运行 Parallax。我们推荐使用 **Qwen2.5-0.5B-Instruct** 进行测试。

### Option A: Via HuggingFace (Recommended) / 选项 A：通过 HuggingFace（推荐）

```bash
# Ensure mirror is set if needed / 如果需要，确保已设置镜像
export HF_ENDPOINT=https://hf-mirror.com

huggingface-cli download mlx-community/Qwen2.5-0.5B-Instruct
```

### Option B: Via ModelScope (If HF fails) / 选项 B：通过 ModelScope（如果 HF 失败）

Create a python script `download_model.py`:
创建一个 python 脚本 `download_model.py`：

```python
from modelscope import snapshot_download
import shutil
from pathlib import Path

# Download / 下载
model_dir = snapshot_download("Qwen/Qwen2.5-0.5B-Instruct")

# Setup Symlink for Parallax / 为 Parallax 设置符号链接
hf_cache = Path.home() / ".cache" / "huggingface" / "hub" / "models--mlx-community--Qwen2.5-0.5B-Instruct"
hf_cache.mkdir(parents=True, exist_ok=True)
(hf_cache / "snapshots" / "main").symlink_to(model_dir)
print("Done!")
```

---

## 5. Running Parallax / 运行 Parallax

You need two terminal windows.
您需要两个终端窗口。

### Terminal 1: Start Scheduler / 终端 1：启动调度器

```bash
source venv/bin/activate
# Replace with your downloaded model name / 替换为您下载的模型名称
parallax run -m mlx-community/Qwen2.5-0.5B-Instruct -n 1
```

*   `-m`: Model name (must match the folder name in HF cache).
    *   `-m`: 模型名称（必须与 HF 缓存中的文件夹名称匹配）。
*   `-n`: Number of nodes (use 1 for local testing).
    *   `-n`: 节点数量（本地测试使用 1）。

### Terminal 2: Start Node / 终端 2：启动节点

```bash
source venv/bin/activate
parallax join
```

Wait until you see "Model loaded successfully".
等待直到看到 "Model loaded successfully"。

---

## 6. Usage / 使用

Once running, you can interact via HTTP API.
运行后，您可以通过 HTTP API 进行交互。

### Python Client Example / Python 客户端示例

```python
import requests

response = requests.post(
    "http://localhost:3001/v1/chat/completions",
    json={
        "model": "mlx-community/Qwen2.5-0.5B-Instruct",
        "messages": [{"role": "user", "content": "Hello!"}],
        "max_tokens": 100
    }
)
print(response.json())
```

### Web UI / 网页界面

Open your browser and visit:
打开浏览器并访问：
`http://localhost:3001`

---

## 7. Troubleshooting / 故障排除

*   **`No route to host (os error 65)`**: Common on macOS. It usually doesn't affect local single-node usage.
    *   **`No route to host (os error 65)`**: macOS 上常见。通常不影响本地单节点使用。
*   **Model output is empty or special tokens**: Ensure you are using a supported model like Qwen2.5 or Llama-3.2. Avoid Qwen3-0.6B due to known issues.
    *   **模型输出为空或特殊字符**: 确保使用支持的模型，如 Qwen2.5 或 Llama-3.2。避免使用 Qwen3-0.6B，因为它已知有问题。
