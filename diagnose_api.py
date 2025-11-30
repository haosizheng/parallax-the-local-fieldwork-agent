#!/usr/bin/env python3
"""
测试 Parallax API 并诊断输出问题
"""

import json
import requests

def test_chat_api():
    url = "http://localhost:3001/v1/chat/completions"
    
    # 测试 1: 简单问候
    print("🧪 测试 1: 简单问候")
    print("-" * 50)
    
    payload = {
        "model": "mlx-community/Qwen3-0.6B-bf16",
        "messages": [
            {
                "role": "user",
                "content": "你好"
            }
        ],
        "max_tokens": 50,
        "stream": False,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        print(f"状态码: {response.status_code}")
        print(f"\n完整响应:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            print(f"\n✅ 模型回复: {content}")
            print(f"回复长度: {len(content)} 字符")
            
            # 检查是否包含特殊 token
            if "<|im_start|>" in content or "<|im_end|>" in content:
                print("\n⚠️  警告: 输出包含未处理的特殊 token!")
                print("这表明 chat template 或 tokenizer 配置有问题")
        else:
            print("\n❌ 错误: 响应中没有 choices")
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ 请求失败: {e}")
    except json.JSONDecodeError as e:
        print(f"\n❌ JSON 解析失败: {e}")
        print(f"原始响应: {response.text[:500]}")
    
    print("\n" + "=" * 50)
    
    # 测试 2: 数学问题
    print("\n🧪 测试 2: 数学问题")
    print("-" * 50)
    
    payload2 = {
        "model": "mlx-community/Qwen3-0.6B-bf16",
        "messages": [
            {
                "role": "user",
                "content": "1+1等于几？"
            }
        ],
        "max_tokens": 20,
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload2, timeout=30)
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        print(f"✅ 模型回复: {content}")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("Parallax API 诊断工具")
    print("=" * 50)
    test_chat_api()
