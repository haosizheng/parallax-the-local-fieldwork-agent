#!/usr/bin/env python3
"""诊断 Qwen3 输出问题"""

import requests
import json

url = "http://localhost:3001/v1/chat/completions"

payload = {
    "model": "mlx-community/Qwen3-0.6B-bf16",
    "messages": [{"role": "user", "content": "你好"}],
    "max_tokens": 100,
    "temperature": 0.7,
    "stream": False
}

print("测试 Qwen3 原始输出...")
response = requests.post(url, json=payload, timeout=30)
result = response.json()

print("\n完整响应:")
print(json.dumps(result, indent=2, ensure_ascii=False))

if "choices" in result:
    choice = result["choices"][0]
    content = choice.get("messages", {}).get("content", "") or choice.get("message", {}).get("content", "")
    
    print(f"\n原始内容: {repr(content)}")
    print(f"长度: {len(content)}")
    print(f"包含特殊token: {'<|im_start|>' in content}")
