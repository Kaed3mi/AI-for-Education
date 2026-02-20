"""
内置工具集 - Agent可以使用的基础工具
"""
from datetime import datetime
import random
from typing import Dict, Any


# 全局存储（简单示例用）
_notes: Dict[str, str] = {}


def get_current_time(format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """获取当前时间"""
    return datetime.now().strftime(format)


def calculate(expression: str) -> float:
    """
    安全地计算数学表达式

    Args:
        expression: 数学表达式，如 "2 + 2" 或 "10 * 5"

    Returns:
        计算结果
    """
    # 只允许安全的数学运算
    allowed_chars = set("0123456789+-*/().() ")
    if not all(c in allowed_chars for c in expression):
        raise ValueError("表达式包含不允许的字符")

    try:
        return eval(expression)
    except Exception as e:
        raise ValueError(f"计算失败: {str(e)}")


def get_weather(city: str) -> str:
    """
    获取天气信息（模拟数据）

    Args:
        city: 城市名称

    Returns:
        天气信息
    """
    # 模拟天气数据
    conditions = ["晴朗", "多云", "阴天", "小雨", "大雨"]
    temps = {
        "北京": (5, 15),
        "上海": (10, 20),
        "广州": (15, 25),
        "深圳": (18, 28),
    }

    temp_range = temps.get(city, (10, 20))
    temp = random.randint(*temp_range)
    condition = random.choice(conditions)

    return f"{city}今天{condition}，温度{temp}度"


def save_note(title: str, content: str) -> str:
    """
    保存笔记

    Args:
        title: 笔记标题
        content: 笔记内容

    Returns:
        保存结果
    """
    _notes[title] = content
    return f"已保存笔记: {title}"


def get_note(title: str) -> str:
    """
    获取笔记

    Args:
        title: 笔记标题

    Returns:
        笔记内容
    """
    if title not in _notes:
        return f"未找到笔记: {title}"
    return f"笔记内容: {_notes[title]}"


def list_notes() -> str:
    """列出所有笔记"""
    if not _notes:
        return "暂无笔记"
    return "笔记列表:\n" + "\n".join(f"- {title}" for title in _notes.keys())


# 工具定义（OpenAI Function Calling格式）
BUILTIN_TOOLS_SPECS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取当前日期和时间",
            "parameters": {
                "type": "object",
                "properties": {
                    "format": {
                        "type": "string",
                        "description": "时间格式，默认为 '%Y-%m-%d %H:%M:%S'",
                        "default": "%Y-%m-%d %H:%M:%S"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "执行数学计算，支持加减乘除",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "要计算的数学表达式，例如 '2+2' 或 '10*5'"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如 '北京'、'上海'"
                    }
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_note",
            "description": "保存一条笔记",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "笔记标题"
                    },
                    "content": {
                        "type": "string",
                        "description": "笔记内容"
                    }
                },
                "required": ["title", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_note",
            "description": "获取指定标题的笔记内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "笔记标题"
                    }
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_notes",
            "description": "列出所有已保存的笔记",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]

# 工具执行映射
TOOL_FUNCTIONS = {
    "get_current_time": get_current_time,
    "calculate": calculate,
    "get_weather": get_weather,
    "save_note": save_note,
    "get_note": get_note,
    "list_notes": list_notes,
}


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """
    执行工具

    Args:
        tool_name: 工具名称
        arguments: 工具参数

    Returns:
        执行结果
    """
    if tool_name not in TOOL_FUNCTIONS:
        return f"错误: 未找到工具 '{tool_name}'"

    try:
        result = TOOL_FUNCTIONS[tool_name](**arguments)
        return str(result)
    except Exception as e:
        return f"工具执行失败: {str(e)}"
