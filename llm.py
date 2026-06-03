"""
=============================================================================
 llm.py — LLM API 客户端
=============================================================================
 职责:
   封装与大语言模型 API 的 HTTP 通信，提供统一的 chat 接口。
   支持 OpenAI 兼容格式的聊天完成接口（/chat/completions）。

 当前限制:
   - 仅支持 OpenAI 兼容的 REST API（如 DeepSeek、OpenRouter）
   - 不支持 Anthropic / Google Gemini 等其他协议格式
   - 不支持流式响应（stream=True）
=============================================================================
"""

from dataclasses import dataclass    # 数据类装饰器
from typing import Optional          # 可选类型标注
import requests                      # HTTP 请求库
import json                          # JSON 处理


# ============================================================================
# LLM 配置数据类
# ============================================================================
@dataclass
class LLMConfig:
    """
    大语言模型的连接配置。

    属性:
      provider: 提供商名称（如 deepseek, openai, anthropic）
      name:     模型名称（如 deepseek-v4-flash, gpt-4o-mini）
      api_key:  API 认证密钥
      base_url: API 基础 URL（不含 /chat/completions 路径）
    """
    provider: str    # 模型提供商
    name: str        # 模型名称
    api_key: str     # API 密钥
    base_url: str    # API 基础地址


# ============================================================================
# LLM 客户端类
# ============================================================================
class LLMClient:
    """
    大语言模型 API 的 HTTP 客户端。

    使用 requests.Session 复用 TCP 连接，自动管理连接池，
    比每次请求新建连接效率更高。

    属性:
      config:  LLMConfig 配置对象
      session: requests.Session 会话（管理连接池和请求头）
    """

    def __init__(self, config: LLMConfig):
        """
        初始化 LLM 客户端。

        设置 HTTP 会话和认证头（Bearer Token）。

        参数:
          config: LLMConfig 配置对象（含 provider, name, api_key, base_url）
        """
        self.config = config

        # 创建可复用的 HTTP 会话
        self.session = requests.Session()

        # 设置全局请求头
        # Authorization: Bearer <api_key> — 标准的 API 认证方式
        # Content-Type: application/json — 请求体为 JSON 格式
        self.session.headers.update({
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        })


    def chat(
        self,
        messages: list,
        tools: Optional[list] = None,
        temperature: float = 0.3,
    ) -> dict:
        """
        向 LLM API 发送聊天请求并获取响应。

        参数:
          messages:    消息列表（OpenAI 格式，含 role 和 content）
          tools:       工具定义列表（可选，有则启用 function calling）
          temperature: 生成温度（0.0-1.0），控制输出的随机性

        返回:
          dict — API 响应的 message 对象（含 content 和/或 tool_calls）

        处理流程:
          1. 构建请求 payload（model, messages, temperature）
          2. 如有工具定义，添加到 payload 并设置 tool_choice="auto"
          3. 发送 POST 请求到 {base_url}/chat/completions
          4. 检查 HTTP 状态码
          5. 提取并返回 choices[0].message

        API 响应格式:
          {
            "choices": [{
              "message": {
                "role": "assistant",
                "content": "最终文本回复",        // 直接回复时非空
                "tool_calls": [...]              // 调用工具时非空
              }
            }]
          }
        """
        # ---- 步骤 1: 构建请求体 ----
        payload = {
            "model": self.config.name,    # 模型名称
            "messages": messages,          # 对话历史
            "temperature": temperature,    # 生成温度
        }

        # ---- 步骤 2: 如果启用工具调用 ----
        if tools:
            payload["tools"] = tools           # 注入工具定义
            payload["tool_choice"] = "auto"     # 让 LLM 自主决定是否调用

        # ---- 步骤 3: 发送 HTTP 请求 ----
        resp = self.session.post(
            f"{self.config.base_url}/chat/completions",
            json=payload,        # 自动序列化并设置 Content-Type
            timeout=120,         # 120 秒超时（复杂任务可能需要较长时间）
        )

        # ---- 步骤 4: 解析响应 ----
        # 如果状态码非 2xx，抛出 HTTPError
        resp.raise_for_status()

        # 提取 AI 助手的消息内容
        # resp.json()  → 完整的 API 响应
        # ["choices"]  → 候选回复列表
        # [0]          → 取第一个（通常也是唯一一个）
        # ["message"]  → { role, content, tool_calls }
        return resp.json()["choices"][0]["message"]
