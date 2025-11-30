#!/usr/bin/env python3
"""
Parallax Qwen3 客户端 - 带特殊 Token 过滤

这个脚本可以正常使用 Qwen3 模型，自动过滤掉特殊 token
"""

import requests
import json
import re
import sys

class ParallaxClient:
    def __init__(self, base_url="http://localhost:3001"):
        self.base_url = base_url
        self.api_url = f"{base_url}/v1/chat/completions"
    
    def clean_response(self, text):
        """移除 Qwen3 的特殊 token"""
        if not text:
            return ""
        
        # 移除所有 Qwen 特殊 token
        text = re.sub(r'<\|im_start\|>', '', text)
        text = re.sub(r'<\|im_end\|>', '', text)
        text = re.sub(r'<\|endoftext\|>', '', text)
        text = re.sub(r'<\|object_ref_start\|>', '', text)
        text = re.sub(r'<\|object_ref_end\|>', '', text)
        text = re.sub(r'<\|box_start\|>', '', text)
        text = re.sub(r'<\|box_end\|>', '', text)
        text = re.sub(r'<\|quad_start\|>', '', text)
        text = re.sub(r'<\|quad_end\|>', '', text)
        text = re.sub(r'<\|vision_start\|>', '', text)
        text = re.sub(r'<\|vision_end\|>', '', text)
        text = re.sub(r'<\|vision_pad\|>', '', text)
        text = re.sub(r'<\|image_pad\|>', '', text)
        text = re.sub(r'<\|video_pad\|>', '', text)
        
        return text.strip()
    
    def chat(self, message, max_tokens=200, temperature=0.7, stream=False):
        """发送聊天请求"""
        payload = {
            "model": "mlx-community/Qwen3-0.6B-bf16",
            "messages": [
                {
                    "role": "user",
                    "content": message
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream
        }
        
        try:
            response = requests.post(self.api_url, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                # 注意：Parallax 返回的格式可能是 "messages" 而不是 "message"
                choice = result["choices"][0]
                if "messages" in choice:
                    raw_content = choice["messages"]["content"]
                elif "message" in choice:
                    raw_content = choice["message"]["content"]
                else:
                    raw_content = str(choice)
                
                # 清理特殊 token
                clean_content = self.clean_response(raw_content)
                
                return {
                    "success": True,
                    "content": clean_content,
                    "raw_content": raw_content,
                    "usage": result.get("usage", {}),
                    "has_special_tokens": raw_content != clean_content
                }
            else:
                return {
                    "success": False,
                    "error": "No choices in response",
                    "raw_response": result
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Request failed: {e}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {e}"
            }

def main():
    """交互式聊天"""
    client = ParallaxClient()
    
    print("=" * 60)
    print("Parallax Qwen3 聊天客户端")
    print("=" * 60)
    print("提示: 输入 'quit' 或 'exit' 退出")
    print("提示: 输入 'clear' 清屏")
    print("-" * 60)
    
    while True:
        try:
            # 获取用户输入
            user_input = input("\n你: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n再见！👋")
                break
            
            if user_input.lower() == 'clear':
                print("\033[2J\033[H")  # 清屏
                continue
            
            # 发送请求
            print("\nAI: ", end="", flush=True)
            result = client.chat(user_input)
            
            if result["success"]:
                print(result["content"])
                
                # 如果检测到特殊 token，显示警告
                if result["has_special_tokens"]:
                    print(f"\n⚠️  [已过滤特殊 token，原始输出: {result['raw_content'][:50]}...]")
                
                # 显示使用统计
                usage = result.get("usage", {})
                if usage:
                    print(f"\n📊 Tokens: {usage.get('prompt_tokens', 0)} 输入 + "
                          f"{usage.get('completion_tokens', 0)} 输出 = "
                          f"{usage.get('total_tokens', 0)} 总计")
            else:
                print(f"❌ 错误: {result['error']}")
                
        except KeyboardInterrupt:
            print("\n\n再见！👋")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")

if __name__ == "__main__":
    # 检查是否有命令行参数
    if len(sys.argv) > 1:
        # 单次查询模式
        client = ParallaxClient()
        query = " ".join(sys.argv[1:])
        print(f"查询: {query}\n")
        result = client.chat(query)
        if result["success"]:
            print(f"回复: {result['content']}")
        else:
            print(f"错误: {result['error']}")
    else:
        # 交互模式
        main()
