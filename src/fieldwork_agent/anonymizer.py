import json
import re
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

# Constants (Reusing from rag_engine or defining new ones)
PARALLAX_API_BASE = "http://localhost:3001/v1"
PARALLAX_API_KEY = "EMPTY"
MODEL_NAME = "parallax"

DEFAULT_SYSTEM_PROMPT = """你是一位专注于社会学研究伦理的专业数据脱敏工程师。你的核心任务是审查访谈文本，识别并标记所有可能导致受访者身份暴露的敏感信息（PII）和高危信息组合。你的回复必须严格遵循提供的 JSON Schema，不得包含任何解释性文本或额外内容。"""

DEFAULT_USER_PROMPT_TEMPLATE = """【当前文本块】
{current_chunk_text}

【上文情境（如有）】
{context_prefix}

根据以上文本，请执行以下任务：

1. 识别并列出所有直接 PII（例如：真实姓名、精确地址、电话、身份证号、未泛化的日期）。
2. 识别并列出所有高危信息组合。高危组合是指两个或多个非直接 PII（如职业、地点、经历）结合后，能将受访者从群体中唯一识别出来的情况。
3. 高危组合的判断规则包括但不限于：
   - **[稀有职业/身份]** + **[具体地点/机构名称]**（如：XX县唯一文物修复师 + 城北郊区XX社区）。
   - **[独特/罕见事件或经历]** + **[精确日期]**（如：在2005年参加了某特定非公开事件）。
   - **[特定背景特征]** + **[地域/时间上的唯一性描述]**（如：某小区唯一的外国籍业主）。
4. **排除规则与优先级（重要）**：
   - **排除非事实性信息**：除非观点中包含直接 PII（如“我的地址在 XXX”），否则请忽略对国家、政治制度、教育系统、宗教或哲学的一般性观点、信仰、比较性陈述和抽象理论。
   - **【新增】排除情绪与主观感受**：禁止标记与情绪状态、主观感受、抽象比较、或未付诸行动的意图相关的文本（例如：“太无聊”、“有点害怕”、“比他们强”）。风险标记必须基于可核实或高暴露风险的传记事实。
   - **优先标记传记性事实**：必须优先标记传记性事实（例如：出生日期、详细行动、工作单位、居住地、健康状况），这些信息能够与外部数据库进行交叉比对以锁定个体。

请严格按照下方 JSON Schema 输出结果，并确保每一个标记都包含在原始文本中。如果未发现任何风险，请返回空的 JSON 数组：[]。

JSON Schema:
[
  {{
    "entity": "被标记的敏感实体或高危组合的原始文本片段",
    "type": "PII（直接身份信息） 或 HIGH_RISK_COMBO（高危组合）",
    "risk_level": "HIGH（高） 或 MEDIUM（中）",
    "reason": "简要说明风险原因。如果是 HIGH_RISK_COMBO，请说明是哪几个元素结合导致了风险。",
    "start_index": "实体在当前文本块中的起始字符位置（用于前端高亮）"
  }}
]"""

def analyze_text(text: str, system_prompt: str = DEFAULT_SYSTEM_PROMPT, user_prompt_template: str = DEFAULT_USER_PROMPT_TEMPLATE) -> List[Dict[str, Any]]:
    """
    Analyze text for PII and high-risk combinations using Qwen.
    Returns a list of detected entities.
    """
    llm = ChatOpenAI(
        openai_api_base=PARALLAX_API_BASE,
        openai_api_key=PARALLAX_API_KEY,
        model_name=MODEL_NAME,
        temperature=0.1,  # Low temperature for deterministic output
        extra_body={"repetition_penalty": 1.1}
    )

    # Construct the full prompt
    # We map the input 'text' to 'current_chunk_text'
    # For now, 'context_prefix' is empty as we process chunks independently
    formatted_user_prompt = user_prompt_template.format(
        current_chunk_text=text,
        context_prefix="无"
    )

    from langchain.schema import SystemMessage, HumanMessage
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=formatted_user_prompt)
    ]

    try:
        response = llm.invoke(messages)
        content = response.content.strip()
        
        # Attempt to clean markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        entities = json.loads(content)
        return entities
    except json.JSONDecodeError:
        print("Failed to parse JSON response.")
        return [{"error": "JSON Parsing Failed", "raw_content": content}]
    except Exception as e:
        print(f"Error during analysis: {e}")
        return [{"error": str(e)}]

def highlight_text(text: str, entities: List[Dict[str, Any]]) -> str:
    """
    Highlight entities in the text using HTML.
    """
    # Sort entities by length descending to avoid nested replacement issues (simple approach)
    # A more robust approach would be index-based, but for now string replacement is faster to prototype.
    # To prevent double replacement, we can use a placeholder strategy or careful ordering.
    
    # Filter out errors
    valid_entities = [e for e in entities if "entity" in e and e["entity"] in text]
    
    # Sort by length descending to replace longest matches first
    valid_entities.sort(key=lambda x: len(x["entity"]), reverse=True)
    
    highlighted_text = text
    
    # We use a temporary placeholder to avoid re-replacing inside HTML tags
    # But since we are just wrapping in span, we need to be careful.
    # Simple strategy: Replace with unique tokens, then replace tokens with HTML.
    
    replacements = {}
    
    for i, item in enumerate(valid_entities):
        entity = item["entity"]
        risk = item.get("risk_level", "Low").lower()
        
        # Colors for TEXT (Darker for readability on white background)
        if risk == "high":
            color = "#d32f2f" # Strong Red
        elif risk == "medium":
            color = "#f57c00" # Dark Orange
        elif risk == "low":
            color = "#827717" # Dark Yellow/Olive
        else:
            color = "#333333"
            
        token = f"__ENTITY_{i}__"
        # Create HTML span with text color and bold
        # Use 'reason' in title if available, otherwise fallback to type
        tooltip = item.get("reason", f"{item['type']} ({item.get('risk_level', 'Unknown')})")
        # Escape quotes in tooltip
        tooltip = tooltip.replace('"', '&quot;')
        
        html = f'<span style="color: {color}; font-weight: bold; text-decoration: underline;" title="{tooltip}">{entity}</span>'
        
        replacements[token] = html
        # Replace only the first occurrence or all? Usually all.
        highlighted_text = highlighted_text.replace(entity, token)
        
    # Swap tokens back to HTML
    for token, html in replacements.items():
        highlighted_text = highlighted_text.replace(token, html)
        
    # Convert newlines to <br> for HTML rendering
    highlighted_text = highlighted_text.replace("\n", "<br>")
    
    return highlighted_text

def extract_risky_sentences(text: str, entities: List[Dict[str, Any]]) -> List[str]:
    """
    Extract sentences that contain detected entities.
    """
    # Simple sentence splitting for Chinese/English
    # Split by common sentence terminators (。！？.!?\n)
    # We use a regex that keeps the delimiters
    parts = re.split(r'([。！？.!?\n]+)', text)
    
    sentences = []
    current_sent = ""
    
    # Reassemble parts into sentences
    for part in parts:
        current_sent += part
        # If part contains a delimiter, it ends the sentence
        if re.search(r'[。！？.!?\n]', part):
            if current_sent.strip():
                sentences.append(current_sent.strip())
            current_sent = ""
            
    if current_sent.strip():
        sentences.append(current_sent.strip())
        
    # Filter for sentences containing entities
    risky_sentences = []
    for sent in sentences:
        for item in entities:
            if item.get("entity") and item["entity"] in sent:
                # Highlight the entity in the sentence for better visibility in the list?
                # User just asked for the list. Let's keep it simple first.
                risky_sentences.append(sent)
                break # Avoid adding same sentence twice if it has multiple entities
                
    return risky_sentences
