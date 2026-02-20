"""
工具系统 - 定义和管理Agent可用的工具
每个工具是一个可以被Agent调用的函数
"""
from typing import Callable, Dict, Any, List
import inspect
import json


class Tool:
    """工具类 - 封装可被Agent调用的函数"""

    def __init__(
        self,
        name: str,
        description: str,
        function: Callable,
        parameters: Dict[str, Any]
    ):
        """
        初始化工具

        Args:
            name: 工具名称
            description: 工具描述（给LLM看的）
            function: 实际执行的函数
            parameters: 参数schema（JSON Schema格式）
        """
        self.name = name
        self.description = description
        self.function = function
        self.parameters = parameters

    def to_openai_format(self) -> Dict[str, Any]:
        """转换为OpenAI Function Calling格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }

    def execute(self, **kwargs) -> str:
        """
        执行工具

        Args:
            **kwargs: 工具参数

        Returns:
            执行结果（字符串格式）
        """
        try:
            result = self.function(**kwargs)
            return str(result)
        except Exception as e:
            return f"错误: {str(e)}"


def tool(name: str, description: str, parameters: Dict[str, Any]):
    """
    装饰器：将函数转换为Tool对象

    Args:
        name: 工具名称
        description: 工具描述
        parameters: 参数schema

    Example:
        @tool(
            name="calculator",
            description="执行数学计算",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "要计算的数学表达式，如 '2 + 2'"
                    }
                },
                "required": ["expression"]
            }
        )
        def calculate(expression: str) -> float:
            return eval(expression)
    """
    def decorator(func: Callable) -> Tool:
        return Tool(name, description, func, parameters)
    return decorator


class ToolRegistry:
    """工具注册表 - 管理所有可用工具"""

    def __init__(self):
        self.tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        """注册工具"""
        self.tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        """获取工具"""
        if name not in self.tools:
            raise ValueError(f"工具 '{name}' 不存在")
        return self.tools[name]

    def list_tools(self) -> List[Tool]:
        """列出所有工具"""
        return list(self.tools.values())

    def to_openai_format(self) -> List[Dict[str, Any]]:
        """转换为OpenAI格式"""
        return [tool.to_openai_format() for tool in self.tools.values()]
