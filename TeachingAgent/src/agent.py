"""
Agent核心类 - 实现ReAct（推理-行动）模式的智能体
"""
import json
from typing import List, Dict, Any, Optional
from llm_client import LLMClient
from tools.builtin_tools import BUILTIN_TOOLS_SPECS, execute_tool


class Agent:
    """
    智能Agent - 使用ReAct模式完成复杂任务

    ReAct = Reasoning（推理） + Acting（行动）
    - 推理: 分析问题，决定下一步做什么
    - 行动: 执行工具或直接回答
    """

    def __init__(
        self,
        llm_client: LLMClient,
        name: str = "个人助手",
        description: str = "我是一个智能助手，可以使用各种工具帮助你完成任务",
        max_iterations: int = 5
    ):
        """
        初始化Agent

        Args:
            llm_client: LLM客户端
            name: Agent名称
            description: Agent描述
            max_iterations: 最大推理-行动循环次数
        """
        self.llm_client = llm_client
        self.name = name
        self.description = description
        self.max_iterations = max_iterations

        # 可用工具
        self.tools = BUILTIN_TOOLS_SPECS

        # 对话历史
        self.messages: List[Dict[str, str]] = []

        # 系统提示词
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        tools_desc = "\n".join([
            f"- {tool['function']['name']}: {tool['function']['description']}"
            for tool in self.tools
        ])

        return f"""你是{self.name}，{self.description}。

你可以使用以下工具来帮助用户：

{tools_desc}

工作流程：
1. 理解用户的请求
2. 分析需要使用哪些工具
3. 调用工具获取结果
4. 基于工具结果给出最终答案

重要提示：
- 如果问题可以直接回答，直接回答即可
- 如果需要使用工具，选择最合适的工具
- 如果需要多次工具调用，按顺序执行
- 始终基于工具的实际结果回答，不要编造信息
- 用友好、专业的语气与用户交流
"""

    def reset(self):
        """重置对话历史"""
        self.messages = []
        self.messages.append({
            "role": "system",
            "content": self.system_prompt
        })

    def run(self, user_input: str) -> str:
        """
        运行Agent处理用户输入

        Args:
            user_input: 用户输入

        Returns:
            Agent的回复
        """
        # 如果是第一次运行，初始化对话
        if not self.messages:
            self.reset()

        # 添加用户消息
        self.messages.append({
            "role": "user",
            "content": user_input
        })

        # 执行推理-行动循环
        for iteration in range(self.max_iterations):
            # 调用LLM
            response = self.llm_client.chat(
                messages=self.messages,
                tools=self.tools
            )

            # 构建assistant消息
            assistant_message = {
                "role": "assistant"
            }

            # 只有当content不为None时才添加（工具调用时content可能为None）
            if response["content"] is not None:
                assistant_message["content"] = response["content"]

            # 如果有工具调用
            if response["tool_calls"]:
                assistant_message["tool_calls"] = response["tool_calls"]
                self.messages.append(assistant_message)

                # 执行所有工具调用
                for tool_call in response["tool_calls"]:
                    # 从完整结构中提取工具名称和参数
                    tool_name = tool_call["function"]["name"]
                    try:
                        arguments = json.loads(tool_call["function"]["arguments"])
                    except (json.JSONDecodeError, TypeError):
                        arguments = {}

                    # 执行工具
                    result = execute_tool(tool_name, arguments)

                    # 添加工具结果到对话
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": tool_name,
                        "content": result
                    })

                # 继续循环，让LLM基于工具结果生成最终答案
                continue
            else:
                # 没有工具调用，说明是最终答案
                self.messages.append(assistant_message)
                return response["content"] or "抱歉，我没有生成回复。"

        # 达到最大迭代次数
        return "抱歉，处理该请求时遇到了问题，请重试或简化问题。"

    def chat(self, user_input: str) -> str:
        """
        对话接口（保持会话状态）

        Args:
            user_input: 用户输入

        Returns:
            Agent回复
        """
        return self.run(user_input)

    def get_history(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        return self.messages.copy()

    def __repr__(self):
        return f"Agent(name='{self.name}', tools={len(self.tools)})"
