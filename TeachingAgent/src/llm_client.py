"""
LLM客户端 - 封装OpenAI API调用
支持OpenAI或兼容OpenAI格式的API
"""
import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量 - 尝试从多个可能的位置加载 .env 文件
env_loaded = load_dotenv()  # 当前目录
if not env_loaded:
    # 尝试从父目录加载（用于 teaching_agents 子项目）
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    env_path = os.path.join(parent_dir, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)


class LLMClient:
    """大语言模型客户端"""

    def __init__(
        self,
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ):
        """
        初始化LLM客户端

        Args:
            api_base: API地址，默认从环境变量API_BASE读取
            api_key: API密钥，默认从环境变量API_KEY读取
            model: 模型名称，默认从环境变量MODEL读取
            temperature: 温度参数（0-1，越高越随机）
            max_tokens: 最大生成token数
        """
        self.api_base = api_base or os.getenv("API_BASE", "https://api.openai.com/v1")
        self.api_key = api_key or os.getenv("API_KEY", "")
        self.model = model or os.getenv("MODEL", "gpt-3.5-turbo")
        self.temperature = temperature
        self.max_tokens = max_tokens

        if not self.api_key:
            raise ValueError("API_KEY未设置，请在.env文件中配置或通过参数传入")

        # 创建OpenAI客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_base
        )

    def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        发送聊天请求

        Args:
            messages: 消息历史列表
            tools: 可用工具列表（用于Function Calling）
            **kwargs: 其他请求参数

        Returns:
            响应结果，包含消息和可能的工具调用
        """
        request_params = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
        }

        # 如果提供了工具，添加到请求中
        if tools:
            request_params["tools"] = tools
            request_params["tool_choice"] = "auto"

        try:
            response = self.client.chat.completions.create(**request_params)
            return self._parse_response(response)
        except Exception as e:
            raise RuntimeError(f"LLM请求失败: {str(e)}")

    def _parse_response(self, response) -> Dict[str, Any]:
        """解析OpenAI响应"""
        message = response.choices[0].message

        result = {
            "content": message.content,
            "tool_calls": []
        }

        # 解析工具调用（保持完整的OpenAI格式）
        if message.tool_calls:
            for tool_call in message.tool_calls:
                result["tool_calls"].append({
                    "id": tool_call.id,
                    "type": tool_call.type,
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                })

        return result

    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ):
        """
        发送流式聊天请求

        Args:
            messages: 消息历史列表
            tools: 可用工具列表（用于Function Calling）
            **kwargs: 其他请求参数

        Yields:
            流式响应的内容片段
        """
        request_params = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "stream": True,
        }

        # 如果提供了工具，添加到请求中
        if tools:
            request_params["tools"] = tools
            request_params["tool_choice"] = "auto"

        try:
            stream = self.client.chat.completions.create(**request_params)

            for chunk in stream:
                delta = chunk.choices[0].delta

                # 获取内容
                if hasattr(delta, 'content') and delta.content:
                    yield delta.content

                # 检查是否完成
                elif chunk.choices[0].finish_reason is not None:
                    break

        except Exception as e:
            raise RuntimeError(f"LLM流式请求失败: {str(e)}")

    def __repr__(self):
        return f"LLMClient(model={self.model}, api_base={self.api_base})"
