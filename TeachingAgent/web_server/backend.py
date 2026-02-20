"""
FastAPI 后端服务器 - 编程教学 Agent Web 界面
提供流式输出的聊天 API
"""
import os
import sys
import json
import uuid
from typing import Dict, Any, List, Optional
from pathlib import Path
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from dotenv import load_dotenv

# 获取目录路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# 加载 .env 文件 - 从项目根目录加载
env_path = os.path.join(parent_dir, '.env')
load_dotenv(env_path)

# 添加 src 目录到路径
src_dir = os.path.join(parent_dir, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# 添加 teaching_agents 到路径
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from llm_client import LLMClient
from teaching_agents.feynman_agent import FeynmanAgent
from teaching_agents.reverse_turing_agent import ReverseTuringAgent
from teaching_agents.socratic_agent import SocraticAgent
from teaching_agents.core_teaching_agent import CoreTeachingAgent
from teaching_agents.error_analysis_agent import ErrorAnalysisAgent

# 创建 FastAPI 应用
app = FastAPI(title="编程教学 Agent API", version="1.0.0")

# 挂载静态文件目录
static_dir = os.path.join(current_dir, "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局配置
API_BASE = os.getenv("API_BASE", "https://api.openai.com/v1")
API_KEY = os.getenv("API_KEY", "")
MODEL = os.getenv("MODEL", "gpt-3.5-turbo")


# 数据模型
class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    agent_type: str  # "feynman", "reverse_turing", "socratic"
    message: str
    session_id: Optional[str] = None
    history: List[ChatMessage] = []


class AgentResponse(BaseModel):
    response: str
    agent_type: str
    stage: Optional[str] = None
    progress: Optional[Dict[str, Any]] = None


# 会话管理
sessions: Dict[str, Dict[str, Any]] = {}


def get_or_create_session(session_id: Optional[str], agent_type: str) -> tuple[str, Dict[str, Any]]:
    """获取或创建会话"""
    if not session_id:
        session_id = str(uuid.uuid4())

    if session_id not in sessions:
        # 创建新的 Agent 实例
        llm_client = LLMClient(api_base=API_BASE, api_key=API_KEY, model=MODEL)

        if agent_type == "feynman":
            agent = FeynmanAgent(llm_client)
        elif agent_type == "reverse_turing":
            agent = ReverseTuringAgent(llm_client)
        elif agent_type == "socratic":
            agent = SocraticAgent(llm_client)
        elif agent_type == "core_teaching":
            agent = CoreTeachingAgent(llm_client)
        elif agent_type == "error_analysis":
            agent = ErrorAnalysisAgent(llm_client)
        else:
            raise HTTPException(status_code=400, detail=f"未知的 Agent 类型: {agent_type}")

        sessions[session_id] = {
            "agent": agent,
            "agent_type": agent_type,
            "created_at": datetime.now().isoformat(),
            "message_count": 0
        }

    return session_id, sessions[session_id]


def generate_response_stream(agent, user_input: str, session_id: str):
    """生成真正的流式响应"""
    try:
        # 首先发送 session_id
        yield f"data: {json.dumps({'session_id': session_id, 'done': False}, ensure_ascii=False)}\n\n"

        # 记录学生输入（模拟 Agent 的逻辑）
        if hasattr(agent, 'memory'):
            agent.memory.add_memory(
                f"学生: {user_input}",
                importance=0.6,
                tags=["student_input"],
                level="short"
            )

        # 构建消息列表（模拟 Agent 的逻辑）
        messages = []

        # 添加 system prompt
        if hasattr(agent, '_build_system_prompt'):
            messages.append({"role": "system", "content": agent._build_system_prompt()})

        if hasattr(agent, '_get_stage_prompt'):
            messages.append({"role": "system", "content": agent._get_stage_prompt()})

        # 添加对话历史
        if hasattr(agent, 'memory') and hasattr(agent.memory, 'short_term'):
            for memory in agent.memory.short_term.get_all():
                messages.append({
                    "role": "user",
                    "content": memory.content
                })

        # 使用真正的流式 API
        full_response = ""
        for chunk in agent.llm_client.chat_stream(messages=messages):
            if chunk:
                full_response += chunk
                yield f"data: {json.dumps({'content': chunk, 'done': False}, ensure_ascii=False)}\n\n"

        # 检查 [BUG_FOUND] 信号（针对 ErrorAnalysisAgent）
        if "[BUG_FOUND]" in full_response:
            if hasattr(agent, 'found_bugs_count') and hasattr(agent, 'total_bugs_count'):
                agent.found_bugs_count = min(agent.found_bugs_count + 1, agent.total_bugs_count)
            # 移除信号，不显示给用户
            full_response = full_response.replace("[BUG_FOUND]", "").strip()

        # 记录 Agent 回复并更新阶段（模拟 Agent 的逻辑）
        if hasattr(agent, 'memory'):
            agent.memory.add_memory(
                f"{agent.__class__.__name__}: {full_response}",
                importance=0.7,
                tags=["tutor_response"],
                level="short"
            )

        if hasattr(agent, '_update_stage'):
            # 尝试传递 full_response，如果参数不匹配则只传 user_input
            import inspect
            sig = inspect.signature(agent._update_stage)
            if len(sig.parameters) >= 2:
                agent._update_stage(user_input, full_response)
            else:
                agent._update_stage(user_input)

        # 获取更新后的进度信息
        progress = agent.get_progress() if hasattr(agent, 'get_progress') else None

        # 发送完成信号（包含进度信息）
        yield f"data: {json.dumps({'content': '', 'done': True, 'progress': progress}, ensure_ascii=False)}\n\n"

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        error_msg = f"Error: {str(e)}\n{error_detail}"
        yield f"data: {json.dumps({'content': error_msg, 'done': True, 'error': True}, ensure_ascii=False)}\n\n"


@app.get("/")
async def root():
    """返回首页"""
    html_file = os.path.join(current_dir, "static", "index.html")
    with open(html_file, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """普通聊天接口（非流式）"""
    session_id, session = get_or_create_session(request.session_id, request.agent_type)
    agent = session["agent"]

    try:
        response = agent.chat(request.message)

        # 更新消息计数
        session["message_count"] += 1

        # 获取 Agent 特定的信息
        result = {
            "response": response,
            "session_id": session_id,
            "agent_type": session["agent_type"]
        }

        # 添加 Agent 特定的进度信息
        if hasattr(agent, "current_stage"):
            result["stage"] = agent.current_stage.value
        if hasattr(agent, "get_progress"):
            result["progress"] = agent.get_progress()
        if hasattr(agent, "get_current_scores"):
            result["scores"] = agent.get_current_scores()

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """流式聊天接口"""
    session_id, session = get_or_create_session(request.session_id, request.agent_type)
    agent = session["agent"]

    session["message_count"] += 1

    return StreamingResponse(
        generate_response_stream(agent, request.message, session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.post("/api/session/{session_id}/reset")
async def reset_session(session_id: str, agent_type: str):
    """重置会话"""
    if session_id in sessions:
        agent = sessions[session_id]["agent"]
        if hasattr(agent, "reset"):
            agent.reset()
        del sessions[session_id]
        return {"message": "会话已重置"}

    # 创建新会话
    _, session = get_or_create_session(session_id, agent_type)
    return {"message": "新会话已创建", "session_id": session_id}


@app.get("/api/session/{session_id}/info")
async def get_session_info(session_id: str):
    """获取会话信息"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话不存在")

    session = sessions[session_id]
    agent = session["agent"]

    info = {
        "session_id": session_id,
        "agent_type": session["agent_type"],
        "created_at": session["created_at"],
        "message_count": session["message_count"]
    }

    # 添加 Agent 特定信息
    if hasattr(agent, "current_concept"):
        info["current_concept"] = agent.current_concept
    if hasattr(agent, "current_stage"):
        info["current_stage"] = agent.current_stage.value
    if hasattr(agent, "get_progress"):
        info["progress"] = agent.get_progress()
    if hasattr(agent, "get_learning_summary"):
        info["learning_summary"] = agent.get_learning_summary()
    # 优先使用综合评分（CoreTeachingAgent），否则使用完整评分
    if hasattr(agent, "get_comprehensive_scores"):
        info["scores"] = agent.get_comprehensive_scores()
    elif hasattr(agent, "get_current_scores"):
        info["scores"] = agent.get_current_scores()
    if hasattr(agent, "selected_topics"):
        info["selected_topics"] = agent.selected_topics
    if hasattr(agent, "current_code_snippet"):
        info["current_code_snippet"] = agent.current_code_snippet

    return info


@app.post("/api/session/{session_id}/next-topic")
async def next_topic(session_id: str):
    """切换到下一个题目/话题 (主要用于 Error Analysis Agent)"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="会话不存在")
        
    session = sessions[session_id]
    agent = session["agent"]
    
    if hasattr(agent, "next_question"):
        response = agent.next_question()
        return {"message": "已切换", "response": response}
    
    return {"message": "当前 Agent 不支持切换题目"}


class TopicSelectionRequest(BaseModel):
    topic_ids: List[str]
    agent_type: str = "core_teaching"  # 添加 agent_type 字段
    mode: str = "knowledge_learning"
    difficulty: str = "medium"


@app.get("/api/knowledge-points")
async def get_knowledge_points():
    """获取所有知识点"""
    # 临时创建一个 Agent 实例来获取知识点，或者硬编码
    # 为了简单，直接使用 CoreTeachingAgent 类的静态方法或属性
    # 由于我们需要 LLMClient 初始化 Agent，这里直接硬编码返回，或者实例化一个临时的
    # 更好的方式是把 KnowledgePoint 定义挪出来，但现在我们实例化一个 CoreTeachingAgent 是最快的
    
    # 优化：直接从 CoreTeachingAgent 类属性获取
    return [
        {"id": kp.id, "name": kp.name, "description": kp.description}
        for kp in CoreTeachingAgent.AVAILABLE_TOPICS
    ]


@app.post("/api/session/{session_id}/select-topics")
async def select_topics(session_id: str, request: TopicSelectionRequest):
    """提交选中的知识点"""
    # 如果会话不存在，先创建会话
    if session_id not in sessions:
        # 使用 request.agent_type 或者默认为 'core_teaching'
        agent_type = getattr(request, 'agent_type', 'core_teaching') or 'core_teaching'
        _, session = get_or_create_session(session_id, agent_type)
    else:
        session = sessions[session_id]

    agent = session["agent"]
    
    if not isinstance(agent, (CoreTeachingAgent, ErrorAnalysisAgent)):
        raise HTTPException(status_code=400, detail="当前 Agent 不支持知识点选择")
        
    # 设置模式和难度
    # agent.set_mode(request.mode) # Deprecated
    agent.set_difficulty(request.difficulty)
    
    initial_message = agent.set_selected_topics(request.topic_ids)
    
    return {"message": "知识点已选择", "initial_response": initial_message}


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    if session_id in sessions:
        del sessions[session_id]
        return {"message": "会话已删除"}
    return {"message": "会话不存在"}


if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("  编程教学 Agent Web 服务器")
    print("=" * 60)
    print(f"\n📡 服务器地址: http://localhost:8020")
    print(f"📊 API 文档: http://localhost:8020/docs")
    print(f"💡 模型配置: {MODEL}")
    print(f"🔑 API 地址: {API_BASE}")
    print("\n按 Ctrl+C 停止服务器\n")

    uvicorn.run(app, host="0.0.0.0", port=8020)
