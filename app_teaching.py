import os
import sys
import json
import uuid
import re
from difflib import SequenceMatcher
from flask import Blueprint, request, jsonify, Response, stream_with_context, session as flask_session
from typing import Dict, Any, List, Optional

# Add TeachingAgent paths
current_dir = os.path.dirname(os.path.abspath(__file__))
teaching_agent_dir = os.path.join(current_dir, 'TeachingAgent')

if teaching_agent_dir not in sys.path:
    sys.path.insert(0, teaching_agent_dir)
src_path = os.path.join(teaching_agent_dir, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import agents and client
try:
    from teaching_agents.core_teaching_agent import CoreTeachingAgent
    from teaching_agents.error_analysis_agent import ErrorAnalysisAgent
    from llm_client import LLMClient
except ImportError as e:
    import traceback
    traceback.print_exc()
    print(f"Error importing TeachingAgent modules: {e}")
    # Define dummy classes to avoid crash during import, but routes will fail
    class CoreTeachingAgent: pass
    class ErrorAnalysisAgent: pass
    class LLMClient: pass

# Create Blueprint
teaching_bp = Blueprint('teaching', __name__, url_prefix='/api/teaching')

def semantic_similarity(str1: str, str2: str) -> float:
    """
    计算两个字符串的语义相似度
    使用 SequenceMatcher 进行字符串相似度匹配
    """
    if not str1 or not str2:
        return 0.0

    # 标准化字符串（转小写，去除多余空格）
    str1_normalized = ' '.join(str1.lower().split())
    str2_normalized = ' '.join(str2.lower().split())

    # 使用 SequenceMatcher 计算相似度
    return SequenceMatcher(None, str1_normalized, str2_normalized).ratio()

def keyword_match(user_input: str, bug_description: str) -> bool:
    """
    检查用户输入是否包含 bug 描述中的关键词
    """
    # 提取 bug 描述中的关键词（名词、动词等）
    keywords = re.findall(r'[\u4e00-\u9fa5a-zA-Z]{2,}', bug_description)

    # 检查用户输入是否包含这些关键词
    user_input_lower = user_input.lower()
    for keyword in keywords:
        if keyword.lower() in user_input_lower:
            return True

    return False

def smart_bug_match(user_input: str, bug_list: List[str]) -> bool:
    """
    智能匹配：判断用户输入是否匹配任何一个 bug

    参数:
        user_input: 学生的回答
        bug_list: bug 描述列表

    返回:
        bool: 是否找到匹配的 bug
    """
    user_input_lower = user_input.lower()

    for bug in bug_list:
        bug_lower = bug.lower()

        # 1. 精确匹配（子串）
        if bug_lower in user_input_lower or user_input_lower in bug_lower:
            return True

        # 2. 关键词匹配
        if keyword_match(user_input, bug):
            return True

        # 3. 语义相似度匹配（阈值 0.4）
        similarity = semantic_similarity(user_input, bug)
        if similarity >= 0.4:
            return True

    return False

# Global session store for agents (in-memory)
# Note: In a production multi-worker environment, this should be Redis.
# For this environment, we use a global dict.
TEACHING_SESSIONS: Dict[str, Dict[str, Any]] = {}

def get_llm_client():
    """Create LLM Client using environment variables"""
    # Prefer values from TeachingAgent/.env if loaded, or system env
    # The app.py loads .env, so os.environ should have them.
    # We can also fallback to hardcoded defaults or raise error.
    api_key = os.getenv("SIFLOW_API_KEY") or os.getenv("API_KEY")
    # Use Siflow URL if available, otherwise default
    api_base = "https://console.siflow.cn/siflow/longmen/skyinfer/fjing/qwen-lcb/v1/8020/v1" 
    # Check if app.py defined MODEL_ENDPOINTS, maybe we can reuse?
    # For now, let's use what LLMClient expects or defaults.
    
    # Actually, let's check what app.py uses.
    # app.py uses "https://console.siflow.cn/..."
    
    # We will try to instantiate LLMClient with env vars.
    return LLMClient(api_key=api_key)

def get_or_create_agent_session(session_id: str, agent_type: str):
    """Get or create an agent session"""
    if not session_id:
        session_id = str(uuid.uuid4())

    if session_id not in TEACHING_SESSIONS:
        try:
            llm_client = get_llm_client()
            
            if agent_type == 'core_teaching':
                agent = CoreTeachingAgent(llm_client)
            elif agent_type == 'error_analysis':
                agent = ErrorAnalysisAgent(llm_client)
            else:
                # Default to core teaching
                agent = CoreTeachingAgent(llm_client)
                
            TEACHING_SESSIONS[session_id] = {
                "agent": agent,
                "agent_type": agent_type,
                "created_at": str(uuid.uuid4()) # dummy timestamp
            }
        except Exception as e:
            print(f"Failed to create agent: {e}")
            raise e
            
    return session_id, TEACHING_SESSIONS[session_id]

@teaching_bp.route('/select-topics', methods=['POST'])
def select_topics():
    data = request.json
    session_id = data.get('session_id')
    agent_type = data.get('agent_type', 'core_teaching')
    topic_ids = data.get('topic_ids', [])
    difficulty = data.get('difficulty', 'medium')

    try:
        session_id, session_data = get_or_create_agent_session(session_id, agent_type)
        agent = session_data['agent']
        
        # Ensure agent matches type (if session existed)
        if session_data['agent_type'] != agent_type:
            # Re-create if type mismatch
            del TEACHING_SESSIONS[session_id]
            session_id, session_data = get_or_create_agent_session(session_id, agent_type)
            agent = session_data['agent']

        if hasattr(agent, 'set_difficulty'):
            agent.set_difficulty(difficulty)
            
        initial_response = agent.set_selected_topics(topic_ids)
        
        return jsonify({
            "message": "Topics selected",
            "initial_response": initial_response,
            "session_id": session_id
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@teaching_bp.route('/chat', methods=['POST'])
def chat():
    # Check if it's a JSON request or standard form
    data = request.json or {}
    message = data.get('message', '')
    session_id = data.get('session_id')
    agent_type = data.get('agent_type', 'core_teaching')

    if not session_id or session_id not in TEACHING_SESSIONS:
        return jsonify({"error": "Session not found"}), 404

    session_data = TEACHING_SESSIONS[session_id]
    agent = session_data['agent']

    def generate():
        try:
            # Use agent's logic to generate response
            # Since LLMClient.chat_stream is available, we should use it if the agent exposes it.
            # But CoreTeachingAgent.chat() is synchronous and returns full string.
            # However, backend.py implemented `generate_response_stream` which replicates agent logic.
            # We should try to use that if possible, or just wrap the sync chat in a stream (pseudo-stream).
            
            # Let's see backend.py's generate_response_stream again.
            # It accesses agent.llm_client.chat_stream directly and manages memory manually!
            # This is BAD design in backend.py (logic leak), but we must copy it to support streaming.
            
            # Replicating backend.py logic:
            
            # 1. Send session_id
            # yield f"data: {json.dumps({'session_id': session_id, 'done': False})}\n\n"
            
            # 2. Add user memory
            if hasattr(agent, 'memory'):
                agent.memory.add_memory(
                    f"学生: {message}",
                    importance=0.6,
                    tags=["student_input"],
                    level="short"
                )

            # 3. Build messages
            messages = []
            if hasattr(agent, '_build_system_prompt'):
                messages.append({"role": "system", "content": agent._build_system_prompt()})
            if hasattr(agent, '_get_stage_prompt'):
                stage_prompt = agent._get_stage_prompt()
                if stage_prompt:
                    messages.append({"role": "system", "content": stage_prompt})
            
            # Add history
            if hasattr(agent, 'memory') and hasattr(agent.memory, 'short_term'):
                for mem in agent.memory.short_term.get_all():
                    messages.append({"role": "user", "content": mem.content})

            # 4. Stream from LLM
            full_response = ""
            # We need to use agent.llm_client.chat_stream
            # But wait, does LLMClient have chat_stream? Yes, I saw it.
            
            for chunk in agent.llm_client.chat_stream(messages=messages):
                if chunk:
                    full_response += chunk
                    # Send chunk to frontend
                    # Frontend expects lines like: data: {"content": "...", "done": false}
                    yield f"data: {json.dumps({'content': chunk, 'done': False}, ensure_ascii=False)}\n\n"
            
            # 5. Post-processing (BUG_FOUND, memory update)
            bug_found = False

            # 方法1：检查 LLM 是否输出了 [BUG_FOUND] 标记
            if "[BUG_FOUND]" in full_response:
                bug_found = True
                full_response = full_response.replace("[BUG_FOUND]", "").strip()
            # 方法2：智能匹配备用判断（针对错误分析 Agent）
            elif hasattr(agent, 'current_bugs_list') and hasattr(agent, 'found_bugs_count') and hasattr(agent, 'total_bugs_count'):
                # 获取当前会话中"尚未被确认发现"的 bug 列表
                # 由于我们不知道哪些 bug 已经被发现，这里简单处理：
                # 如果智能匹配认为学生回答匹配某个 bug，且 found_bugs_count < total_bugs_count，则增加计数
                if agent.found_bugs_count < agent.total_bugs_count:
                    # 尝试智能匹配
                    if smart_bug_match(message, agent.current_bugs_list):
                        bug_found = True

            # 更新 bug 计数
            if bug_found:
                if hasattr(agent, 'found_bugs_count') and hasattr(agent, 'total_bugs_count'):
                    agent.found_bugs_count = min(agent.found_bugs_count + 1, agent.total_bugs_count)
            
            if hasattr(agent, 'memory'):
                agent.memory.add_memory(
                    f"{agent.__class__.__name__}: {full_response}",
                    importance=0.7,
                    tags=["tutor_response"],
                    level="short"
                )

            # 5.5 备用评分机制 - 确保能力分数动态更新
            # 如果是 core_teaching agent，且 LLM 没有输出 [SCORE:xxx] 标记
            # 我们需要给一个默认评分，确保学生的能力分数能随参与而提升
            if hasattr(agent, 'scores') and message and len(message.strip()) > 3:
                # 检查是否包含 [SCORE:xxx] 标记
                if "[SCORE:" not in full_response:
                    # LLM 没有输出评分，给一个默认的参与分
                    # 关键修复：[STEP:xxx] 标记表示"即将切换到 xxx"，不是当前回复的阶段
                    # 例如：[STEP:example] 表示这是 concept 阶段的总结回复，应该给 concept 加分
                    llm_stage = None
                    step_match = re.search(r'\[STEP:(\w+)\]', full_response)

                    if step_match:
                        next_stage = step_match.group(1)
                        # 阶段顺序：concept -> example -> practice -> summary
                        # [STEP:xxx] 表示即将切换到 xxx，所以当前回复是对 xxx 的"前一个"阶段的评价
                        stage_order = ["concept", "example", "practice", "summary"]
                        if next_stage in stage_order:
                            next_index = stage_order.index(next_stage)
                            if next_index > 0:
                                # 当前回复是对上一个阶段的评价
                                llm_stage = stage_order[next_index - 1]
                            else:
                                # 边界情况：[STEP:concept] 不应该出现，但降级处理
                                llm_stage = "concept"

                    # 如果 LLM 回复中没有 [STEP:xxx] 标记，则从 topic_status 获取当前阶段
                    if not llm_stage and hasattr(agent, 'selected_topics') and hasattr(agent, 'current_topic_index'):
                        if agent.selected_topics and agent.current_topic_index < len(agent.selected_topics):
                            current_topic_id = agent.selected_topics[agent.current_topic_index]
                            if hasattr(agent, 'topic_status') and current_topic_id in agent.topic_status:
                                llm_stage = agent.topic_status[current_topic_id].get("stage", "concept")

                    # 调试日志：记录评分决策
                    current_topic_id = agent.selected_topics[agent.current_topic_index] if hasattr(agent, 'selected_topics') and agent.current_topic_index < len(agent.selected_topics) else "unknown"
                    print(f"[评分调试] LLM回复对应的阶段: {llm_stage}, topic_id: {current_topic_id}, 用户消息: {message[:50]}...")

                    # 根据阶段确定维度
                    # 注意：这里使用 try-except 避免导入失败
                    try:
                        from teaching_agents.core_teaching_agent import TeachingDimension
                        target_dim = None
                        if llm_stage == "concept":
                            target_dim = TeachingDimension.CONCEPT_UNDERSTANDING.value
                        elif llm_stage == "example" or llm_stage == "code":
                            target_dim = TeachingDimension.CODE_APPLICATION.value
                        elif llm_stage == "practice":
                            target_dim = TeachingDimension.LOGICAL_THINKING.value
                        elif llm_stage == "summary":
                            # CRITICAL_THINKING dimension removed from app_teaching.py
                            pass  # summary阶段不需要评分

                        # 给默认参与分：65分（表示学生参与了）
                        if target_dim and target_dim in agent.scores:
                            old_score = agent.scores[target_dim]
                            # 缓慢提升：0.92 * old_score + 0.08 * 0.65
                            agent.scores[target_dim] = old_score * 0.92 + 0.65 * 0.08
                            print(f"[评分调试] 给维度 {target_dim} 加分: {old_score:.3f} -> {agent.scores[target_dim]:.3f}")
                    except ImportError:
                        pass  # 如果导入失败，跳过备用评分

            if hasattr(agent, '_update_stage'):
                # Handle signature difference
                import inspect
                sig = inspect.signature(agent._update_stage)
                if len(sig.parameters) >= 2:
                    agent._update_stage(message, full_response)
                else:
                    agent._update_stage(message)
            
            # 6. Send done signal with progress
            progress = agent.get_progress() if hasattr(agent, 'get_progress') else None
            yield f"data: {json.dumps({'content': '', 'done': True, 'progress': progress}, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'content': f'Error: {str(e)}', 'done': True, 'error': True}, ensure_ascii=False)}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@teaching_bp.route('/info', methods=['GET'])
def get_info():
    session_id = request.args.get('session_id')
    agent_type = request.args.get('agent_type', 'core_teaching')
    
    if not session_id or session_id not in TEACHING_SESSIONS:
        return jsonify({"error": "Session not found"}), 404
        
    session_data = TEACHING_SESSIONS[session_id]
    agent = session_data['agent']
    
    info = {
        "session_id": session_id,
        "agent_type": session_data['agent_type'],
    }
    
    if hasattr(agent, "get_progress"):
        progress = agent.get_progress()
        info["progress"] = progress
        
    if hasattr(agent, "get_comprehensive_scores"):
        info["scores"] = agent.get_comprehensive_scores()
    elif hasattr(agent, "get_current_scores"):
        info["scores"] = agent.get_current_scores()
        
    return jsonify(info)

@teaching_bp.route('/next-question', methods=['POST'])
def next_question():
    data = request.json or {}
    session_id = data.get('session_id')
    agent_type = data.get('agent_type')  # 获取agent类型

    if not session_id or session_id not in TEACHING_SESSIONS:
        return jsonify({"error": "Session not found"}), 404

    session_data = TEACHING_SESSIONS[session_id]
    agent = session_data['agent']

    # 验证agent类型是否匹配
    if agent_type and session_data['agent_type'] != agent_type:
        return jsonify({"error": "Agent type mismatch"}), 400

    if hasattr(agent, "next_question"):
        response = agent.next_question()
        return jsonify({"message": "Switched to next question", "response": response})

    return jsonify({"message": "Current agent does not support next_question"})
