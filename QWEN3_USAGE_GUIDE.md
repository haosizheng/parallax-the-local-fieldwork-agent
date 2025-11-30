# 如何正常使用 Qwen3 模型

## ✅ 解决方案：使用客户端过滤

虽然 Qwen3-0.6B 会输出特殊 token，但我们可以在客户端自动过滤掉它们！

---

## 🚀 快速开始

### 1. 启动 Parallax 服务

**终端 1 - 启动调度器：**
```bash
cd /Users/shibi/Documents/cursor-test/gradient/parallax
./start_scheduler.sh
```

**终端 2 - 启动节点：**
```bash
cd /Users/shibi/Documents/cursor-test/gradient/parallax
./start_node.sh
```

### 2. 使用过滤客户端

**终端 3 - 启动聊天客户端：**
```bash
cd /Users/shibi/Documents/cursor-test/gradient/parallax
python3 qwen3_client.py
```

---

## 💬 使用方式

### 方式 1: 交互式聊天（推荐）

```bash
python3 qwen3_client.py
```

然后你可以像这样聊天：

```
你: 你好
AI: 你好！很高兴见到你。

你: 1+1等于几？
AI: 1+1等于2。

你: quit  # 退出
```

### 方式 2: 单次查询

```bash
python3 qwen3_client.py "你好，请介绍一下你自己"
```

### 方式 3: 在 Python 代码中使用

```python
from qwen3_client import ParallaxClient

client = ParallaxClient()

# 发送消息
result = client.chat("你好")

if result["success"]:
    print(result["content"])  # 已过滤的干净输出
else:
    print(f"错误: {result['error']}")
```

---

## 🔍 工作原理

客户端会自动：

1. ✅ 发送请求到 Parallax API
2. ✅ 接收模型的原始输出（包含特殊 token）
3. ✅ 过滤掉所有 Qwen 特殊 token
4. ✅ 返回干净的文本

---

## 📊 功能特性

- ✅ 自动过滤特殊 token
- ✅ 显示 token 使用统计
- ✅ 支持交互式聊天
- ✅ 支持单次查询
- ✅ 可作为 Python 库使用
- ✅ 显示警告（当检测到特殊 token 时）

---

## 🎯 现在就试试！

1. 确保 Parallax 服务正在运行（两个终端）
2. 运行客户端：
   ```bash
   python3 qwen3_client.py
   ```
3. 开始聊天！

---

## 💡 提示

- 如果模型回复很短或只有特殊 token，增加 `max_tokens` 参数
- 如果想要更有创意的回复，增加 `temperature` 参数（0.7-1.0）
- 如果想要更确定的回复，降低 `temperature` 参数（0.1-0.5）

---

现在你可以正常使用 Qwen3 了！🎉
