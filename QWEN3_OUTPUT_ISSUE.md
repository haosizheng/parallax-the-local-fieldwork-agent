# Parallax Qwen3 输出问题说明

## 🐛 问题描述

你遇到的问题是：模型输出了特殊 token `<|im_start|>` 而不是正常的中文文本。

### 实际输出
```
<|im_start|><|im_start|><|im_start|><|im_start|>
```

### 期望输出
```
你好！我是一个AI助手...
```

---

## 🔍 问题原因

这是 **Qwen3 模型的已知问题**，原因是：

1. **Tokenizer 配置问题**：Qwen3 使用特殊的 chat template，包含 `<|im_start|>` 和 `<|im_end|>` 等特殊 token
2. **Token 过滤缺失**：Parallax 在解码时没有正确过滤这些特殊 token
3. **EOS Token 配置**：模型可能把 `<|im_start|>` 当作了输出 token

---

## ✅ 临时解决方案

### 方案 1: 使用更稳定的模型（推荐）

Qwen3-0.6B 是一个非常小的模型，可能不够稳定。建议尝试：

```bash
# 停止当前服务（Ctrl+C）

# 使用 Qwen2.5 (更稳定)
./start_scheduler.sh -m mlx-community/Qwen2.5-0.5B-Instruct -n 1
```

### 方案 2: 手动过滤特殊 Token

在客户端代码中过滤输出：

```python
import re

def clean_output(text):
    """移除 Qwen3 的特殊 token"""
    # 移除所有特殊 token
    text = re.sub(r'<\|im_start\|>', '', text)
    text = re.sub(r'<\|im_end\|>', '', text)
    text = re.sub(r'<\|endoftext\|>', '', text)
    return text.strip()

# 使用示例
response = api_call()
cleaned_text = clean_output(response['choices'][0]['message']['content'])
```

### 方案 3: 修改 Parallax 源码

这需要修改 Parallax 的 tokenizer 配置。

**文件**: `src/parallax/server/executor.py`

在 line 851 附近，修改 `apply_chat_template` 的调用：

```python
prompt = self.tokenizer.apply_chat_template(
    messages,
    raw_request.get("tools") or None,
    tokenize=True,
    add_generation_prompt=True,
    **chat_template_kwargs,
)
```

添加特殊 token 过滤：

```python
# 在解码时过滤特殊 token
self.tokenizer.decode(
    output_ids,
    skip_special_tokens=True,  # 添加这个参数
    clean_up_tokenization_spaces=True
)
```

---

## 🎯 推荐操作

### 立即可行的方案

1. **在 Web UI 中手动忽略这些 token**
   - 虽然输出有问题，但系统是正常运行的
   - 你可以继续测试其他功能

2. **尝试其他模型**
   
   下载并测试 Qwen2.5（更稳定）：
   
   ```bash
   # 下载模型
   export HF_ENDPOINT=https://hf-mirror.com
   huggingface-cli download mlx-community/Qwen2.5-0.5B-Instruct
   
   # 重启服务
   # 终端 1
   parallax run -m mlx-community/Qwen2.5-0.5B-Instruct -n 1
   
   # 终端 2
   parallax join
   ```

3. **使用 Llama 3.2（最稳定）**
   
   ```bash
   # 下载 Llama 3.2 1B
   export HF_ENDPOINT=https://hf-mirror.com
   huggingface-cli download mlx-community/Llama-3.2-1B-Instruct-bf16
   
   # 启动
   parallax run -m mlx-community/Llama-3.2-1B-Instruct-bf16 -n 1
   ```

---

## 📊 模型对比

| 模型 | 大小 | 稳定性 | 中文支持 | 推荐度 |
|------|------|--------|----------|--------|
| Qwen3-0.6B | 0.6B | ⚠️ 一般 | ✅ 优秀 | ⭐⭐ |
| Qwen2.5-0.5B | 0.5B | ✅ 良好 | ✅ 优秀 | ⭐⭐⭐⭐ |
| Llama-3.2-1B | 1B | ✅ 优秀 | ⚠️ 一般 | ⭐⭐⭐⭐⭐ |

---

## 🔧 深层原因（技术细节）

Qwen3 的 chat template 格式：

```
<|im_start|>system
You are a helpful assistant.<|im_end|>
<|im_start|>user
你好<|im_end|>
<|im_start|>assistant
```

模型应该在 `<|im_start|>assistant` 之后生成文本，但由于某种原因，它在重复输出 `<|im_start|>` token。

可能的原因：
1. MLX 版本的 Qwen3 转换有问题
2. Parallax 的 chat template 应用逻辑有 bug
3. 模型本身训练不足（0.6B 太小）

---

## 💡 建议

**对于学习和开发 Parallax**：
- 先用 **Llama-3.2-1B** 确保系统正常工作
- 然后再尝试其他模型

**对于生产使用**：
- 使用 **Qwen2.5-7B** 或更大的模型
- 确保有足够的内存（至少 16GB）

---

需要我帮你下载并测试其他模型吗？
