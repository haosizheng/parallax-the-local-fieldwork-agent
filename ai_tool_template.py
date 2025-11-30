"""
AI 工具开发模板 - 支持轻松切换模型

这个模板设计为模型无关，可以轻松切换不同的 LLM
"""

import requests
from typing import List, Dict, Optional
import os

class AIClient:
    """
    AI 客户端 - 封装 Parallax API
    
    优点：
    1. 模型无关 - 切换模型不需要改代码
    2. 易于测试 - 可以 mock
    3. 配置集中 - 所有参数在一个地方
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:3001",
        default_max_tokens: int = 200,
        default_temperature: float = 0.7
    ):
        self.base_url = base_url
        self.api_url = f"{base_url}/v1/chat/completions"
        self.default_max_tokens = default_max_tokens
        self.default_temperature = default_temperature
    
    def chat(
        self,
        message: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        发送聊天请求
        
        Args:
            message: 用户消息
            max_tokens: 最大 token 数（None 使用默认值）
            temperature: 温度参数（None 使用默认值）
            system_prompt: 系统提示词（可选）
        
        Returns:
            AI 的回复文本
        """
        messages = []
        
        # 添加系统提示词
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # 添加用户消息
        messages.append({"role": "user", "content": message})
        
        # 构建请求
        payload = {
            "messages": messages,
            "max_tokens": max_tokens or self.default_max_tokens,
            "temperature": temperature or self.default_temperature
        }
        
        # 发送请求
        response = requests.post(self.api_url, json=payload, timeout=30)
        response.raise_for_status()
        
        # 解析响应
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    def chat_stream(
        self,
        message: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ):
        """
        流式聊天（逐字返回）
        
        使用方法：
        for chunk in client.chat_stream("你好"):
            print(chunk, end="", flush=True)
        """
        payload = {
            "messages": [{"role": "user", "content": message}],
            "max_tokens": max_tokens or self.default_max_tokens,
            "temperature": temperature or self.default_temperature,
            "stream": True
        }
        
        response = requests.post(
            self.api_url,
            json=payload,
            stream=True,
            timeout=30
        )
        
        for line in response.iter_lines():
            if line:
                # 解析 SSE 格式
                if line.startswith(b"data: "):
                    data = line[6:]
                    if data != b"[DONE]":
                        import json
                        chunk = json.loads(data)
                        if "choices" in chunk:
                            delta = chunk["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]


# ============================================
# 使用示例
# ============================================

def example_basic_usage():
    """基础使用示例"""
    client = AIClient()
    
    # 简单对话
    response = client.chat("你好，请介绍一下你自己")
    print(f"AI: {response}")


def example_with_system_prompt():
    """使用系统提示词"""
    client = AIClient()
    
    # 设置角色
    response = client.chat(
        message="帮我写一首诗",
        system_prompt="你是一位专业的诗人，擅长写现代诗。"
    )
    print(f"AI: {response}")


def example_translation_tool():
    """翻译工具示例"""
    client = AIClient()
    
    def translate(text: str, target_lang: str = "英文") -> str:
        """翻译函数"""
        prompt = f"请将以下文本翻译成{target_lang}：\n\n{text}"
        return client.chat(
            prompt,
            system_prompt="你是一位专业的翻译，翻译准确、地道。"
        )
    
    # 使用
    result = translate("你好，世界！", "英文")
    print(f"翻译结果: {result}")


def example_code_generator():
    """代码生成工具示例"""
    client = AIClient()
    
    def generate_code(description: str, language: str = "Python") -> str:
        """生成代码"""
        prompt = f"请用 {language} 实现以下功能：\n\n{description}"
        return client.chat(
            prompt,
            max_tokens=500,  # 代码可能需要更多 token
            system_prompt="你是一位专业的程序员，代码简洁、高效。"
        )
    
    # 使用
    code = generate_code("计算斐波那契数列的第 n 项")
    print(f"生成的代码:\n{code}")


def example_batch_processing():
    """批量处理示例"""
    client = AIClient()
    
    questions = [
        "什么是机器学习？",
        "什么是深度学习？",
        "什么是神经网络？"
    ]
    
    for q in questions:
        answer = client.chat(q, max_tokens=100)
        print(f"Q: {q}")
        print(f"A: {answer}\n")


# ============================================
# 配置文件支持（可选）
# ============================================

class ConfigurableAIClient(AIClient):
    """
    支持配置文件的 AI 客户端
    
    可以通过环境变量或配置文件调整参数，
    切换模型时不需要改代码
    """
    
    def __init__(self):
        # 从环境变量读取配置
        base_url = os.getenv("AI_BASE_URL", "http://localhost:3001")
        max_tokens = int(os.getenv("AI_MAX_TOKENS", "200"))
        temperature = float(os.getenv("AI_TEMPERATURE", "0.7"))
        
        super().__init__(base_url, max_tokens, temperature)
        
        # 记录当前配置
        print(f"AI 客户端配置:")
        print(f"  - API: {base_url}")
        print(f"  - Max Tokens: {max_tokens}")
        print(f"  - Temperature: {temperature}")


# ============================================
# 主程序
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("AI 工具开发模板")
    print("=" * 60)
    
    # 选择一个示例运行
    print("\n1. 基础对话")
    example_basic_usage()
    
    print("\n" + "=" * 60)
    print("2. 翻译工具")
    example_translation_tool()
    
    print("\n" + "=" * 60)
    print("3. 代码生成")
    example_code_generator()
    
    print("\n" + "=" * 60)
    print("\n提示：切换模型时，只需重启 Parallax，代码完全不变！")
