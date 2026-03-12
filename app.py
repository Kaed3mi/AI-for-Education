import json
from flask import Flask, request, jsonify, Response, stream_with_context, session
from flask_cors import CORS
from config import OllamaLLM, XiaohangLLM, get_system_prompts, get_system_base_prompt, question_generation_prompts, exam_generation_prompt
from config_programming_assistant import get_programming_assistant_base_prompt, get_programming_assistant_prompts
from flask_session import Session
from models import db, Student, AnswerRecord, KnowledgeMastery, get_or_create_student
import jwt as pyjwt
import redis
import time
import logging
import uuid
import requests
import os
from dotenv import load_dotenv
import sys

# 添加项目根目录到 sys.path（确保可导入 generator_kit 等同级目录）
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 添加 xiaohang_integration 到 sys.path（指向当前项目内的目录）
xiaohang_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xiaohang_integration")
if xiaohang_path not in sys.path:
    sys.path.append(xiaohang_path)

try:
    from generator_kit import generate_cases
except ImportError as e:
    print(f"Warning: generator_kit not found. Error: {e}")
    def generate_cases(*args, **kwargs):
        raise ImportError(f"generator_kit module not found. Original error: {e}")

try:
    from generator_service import generate_problem, Difficulty, ProblemType
except ImportError as e:
    print(f"Warning: xiaohang_integration not found. Error: {e}")


# 加载环境变量
load_dotenv()

app = Flask(__name__)
# 启用跨域请求并允许携带凭证（用于会话 Cookie）
CORS(app, supports_credentials=True)

# Redis 配置 - 使用环境变量
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = int(os.getenv('REDIS_PORT', 6379))
redis_db = int(os.getenv('REDIS_DB', 0))

app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.Redis(host=redis_host, port=redis_port, db=redis_db)
# 移除会话时间过期设置，改为页面刷新重置
# app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 会话有效期30分钟
app.secret_key = 'your_secret_key'  # 设置密钥

# 初始化 Session
Session(app)

# MySQL 配置 (保留 20260212 配置)
mysql_host = os.getenv('MYSQL_HOST', 'localhost')
mysql_port = os.getenv('MYSQL_PORT', '3307')
mysql_user = os.getenv('MYSQL_USER', 'root')
mysql_password = os.getenv('MYSQL_PASSWORD', os.getenv('MYSQL_ROOT_PASSWORD', 'hangfudao123'))
mysql_database = os.getenv('MYSQL_DATABASE', 'hangfudao')
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f'mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}'
    '?charset=utf8mb4'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 3600,
    'pool_pre_ping': True,
}

# 初始化 SQLAlchemy
db.init_app(app)
with app.app_context():
    db.create_all()

# ---------------------- 引入小航辅导模块（增强版） ----------------------
from app_xiaohang_enhanced import xiaohang_enhanced_bp
app.register_blueprint(xiaohang_enhanced_bp)

# ---------------------- 引入 Teaching Agent 模块 ----------------------
try:
    from app_teaching import teaching_bp
    app.register_blueprint(teaching_bp)
except ImportError as e:
    import traceback
    traceback.print_exc()
    print(f"Warning: Failed to import teaching_bp: {e}")

# ---------------------- 辅助函数 ----------------------
def extract_current_topic_from_messages(messages):
    """从历史消息中提取最近一次被提及的主题关键词。
    messages: 已解析的历史消息列表（按时间从旧到新）。
    返回中文主题字符串或空字符串。
    """
    topic_keywords = [
        '栈', '队列', '数组', '链表', '哈希表', '散列表', '堆', '优先队列',
        '树', '二叉树', '二叉搜索树', 'AVL', '红黑树', 'B树', '字典树', 'Trie',
        '图', 'DFS', 'BFS', '最短路', '最小生成树', '拓扑排序',
        '排序', '查找', '动态规划', '贪心', '回溯', '递归'
    ]
    # 从最新消息向前搜索
    for msg in reversed(messages):
        content = str(msg.get('content', ''))
        for kw in topic_keywords:
            if kw in content:
                return kw
    return ''

# ---------------------- 模型映射与流式调用 ----------------------
MODEL_ENDPOINTS = {
    "thinking": {
        "name": "模型一（Thinking模型）",
        "url": "https://console.siflow.cn/siflow/longmen/skyinfer/fjing/qwen-lcb/v1/8020/v1/chat/completions",
        "model": "model-lcb",
    },
    "coder32b": {
        "name": "模型二（指令 32B）",
        "url": "https://console.siflow.cn/siflow/auriga/skyinfer/wzhang/qwen25-coder-ins/0/30000/v1/chat/completions",
        "model": "Qwen2.5-Coder-Instruct-32B-Arena",
    },
    "coder480b": {
        "name": "模型三（480B MoE 指令）",
        "url": "https://siflow-auriga.siflow.cn/siflow/auriga/skyinfer/lzchai/iquest-no-loop/v1/8000/v1/chat/completions",
        "model": "IQuest-Coder-V1-40B-Instruct",
    },
    "coder1t": {
        "name": "模型四（1T）",
        "url": "https://console.siflow.cn/siflow/longmen/skyinfer/wzhang/litellm-dpsk/v1/4000/v1/chat/completions",
        "model": "bh-code",
    },
    "loopcoder": {
        "name": "模型五",
        "url": "https://siflow-auriga.siflow.cn/siflow/auriga/skyinfer/lzchai/iquest-loop/v1/8000/v1/chat/completions",
        "model": "IQuest-Coder-V1-40B-Loop-Instruct",
    },
}

# from call_models import stream_chat_completion
def stream_chat_completion(url, model, messages, api_key=None, timeout=0):
    api_key = api_key if api_key is not None else os.getenv("SIFLOW_API_KEY", "EMPTY")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
    }
    req_timeout = None if timeout == 0 else timeout

    with requests.post(url, headers=headers, data=json.dumps(payload), stream=True, timeout=req_timeout) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines(decode_unicode=True):
            if not line:
                continue
            data_str = line[len("data: "):] if line.startswith("data: ") else line
            if data_str.strip() == "[DONE]":
                break
            try:
                data_json = json.loads(data_str)
            except json.JSONDecodeError:
                yield data_str
                continue

            choices = data_json.get("choices") or []
            if not choices:
                continue
            delta = choices[0].get("delta") or {}
            piece = delta.get("content")
            if piece is None:
                piece = choices[0].get("text") or ""
            if piece:
                yield piece

# @app.route('/')
# def index():
#     return app.send_static_file('index.html')

# @app.route('/xiaohang.html')
# def xiaohang():
#     return app.send_static_file('xiaohang_v2.html')

# @app.route('/xiaohang_v3.html')
# @app.route('/static/xiaohang_v3.html')
# def xiaohang_v3():
#     return app.send_static_file('xiaohang_v3.html')

# ---------------------- JWT 鉴权（希冀平台 cgtoken） ----------------------

def decode_cgtoken(token):
    """解析希冀平台的 cgtoken（无密钥，仅解码 payload）"""
    try:
        payload = pyjwt.decode(token, options={"verify_signature": False}, algorithms=["HS256"])
        student_id = payload.get('userid', '')
        return payload, student_id
    except Exception:
        return None, None


@app.route('/api/auth/verify_token', methods=['POST'])
def verify_cgtoken():
    """验证希冀平台传来的 cgtoken，解析学号并自动注册学生"""
    token = request.json.get('cgtoken')
    if not token:
        return jsonify({"error": "缺少 cgtoken"}), 400

    payload, student_id = decode_cgtoken(token)
    if not student_id:
        return jsonify({"error": "token 无效或已过期"}), 401

    # 自动注册/获取学生
    student = get_or_create_student(
        student_id=student_id,
        name=payload.get('name', ''),
        class_name=payload.get('class_name', '')
    )

    # 存入 session
    session['student_id_number'] = student_id
    session['user_id'] = student_id

    return jsonify({
        "student_id": student.student_id,
        "name": student.name,
        "role": payload.get('role', ''),
        "courseid": payload.get('courseid', ''),
        "message": "认证成功"
    })


@app.route('/api/auth/student_info', methods=['GET'])
def get_current_student_info():
    """获取当前登录学生的使用信息"""
    student_id = session.get('student_id_number')
    if not student_id:
        return jsonify({"error": "未登录"}), 401

    student = Student.query.filter_by(student_id=student_id).first()
    if not student:
        return jsonify({"error": "学生不存在"}), 404

    total_answers = AnswerRecord.query.filter_by(student_db_id=student.id).count()
    correct_answers = AnswerRecord.query.filter_by(student_db_id=student.id, is_correct=True).count()
    mastery_list = KnowledgeMastery.query.filter_by(student_db_id=student.id).all()

    return jsonify({
        "student": student.to_dict(),
        "total_answers": total_answers,
        "correct_answers": correct_answers,
        "accuracy": round(correct_answers / total_answers * 100, 1) if total_answers > 0 else 0,
        "mastery": [m.to_dict() for m in mastery_list]
    })


@app.route('/')
# @app.route('/static/hangfudao.html')
def hangfudao():
    return app.send_static_file('hangfudao.html')

@app.route('/api/ask', methods=['POST'])
def ask():
    question = request.json.get('question')
    stage = request.json.get('stage', '聊天')
    language = request.json.get('language', 'C')  # 获取语言参数，默认为C语言
    user_id = session.get('user_id', 'default_user')
    history = request.json.get('history', [])  # 获取前端传来的历史记录
    selected_model = request.json.get('model', 'xiaohang')
    
    # 获取参考答案数据
    reference_answer = request.json.get('reference_answer', '')
    data = {'reference_answer': reference_answer}
    
    # 只在session中没有session_id时才创建新的
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    session_id = session['session_id']
    
    chat_history_key = f"chat_history:{user_id}:{session_id}"
    
    # 检查是否是新的session（前端刷新页面时会生成新的session_id）
    frontend_session_id = request.json.get('session_id')
    if frontend_session_id and frontend_session_id != session.get('frontend_session_id'):
        # 前端session_id发生变化，清理旧的Redis缓存
        old_key = f"chat_history:{user_id}:{session.get('frontend_session_id', '')}"
        if app.config['SESSION_REDIS'].exists(old_key):
            app.config['SESSION_REDIS'].delete(old_key)
            print(f"清理旧的Redis缓存: {old_key}")
        
        # 更新session中的frontend_session_id
        session['frontend_session_id'] = frontend_session_id
        chat_history_key = f"chat_history:{user_id}:{frontend_session_id}"
    
    # 存储当前用户消息到Redis
    message = {
        "role": "user",
        "content": question,
        "stage": stage,
        "timestamp": time.time()
    }
    app.config['SESSION_REDIS'].rpush(chat_history_key, json.dumps(message))
    
    def generate_response():
        try:
            # 获取Redis中的历史记录
            redis_history = app.config['SESSION_REDIS'].lrange(chat_history_key, -10, -1)
            redis_history = [json.loads(h.decode('utf-8')) if isinstance(h, bytes) else json.loads(h) for h in redis_history]
            
            # 合并前端历史记录和Redis历史记录
            all_history = history + redis_history
            
            # 构建历史对话文本
            history_text = ""
            if all_history:
                history_text = "\n".join([
                    f"{'用户' if h.get('role') == 'user' else 'AI'}({h.get('stage', '聊天')}): {h.get('content', '')}" 
                    for h in all_history[-10:]  # 只取最近10条
                ])
            
            # 根据语言获取对应的提示词
            system_base_prompt = get_programming_assistant_base_prompt(language)
            system_prompts = get_programming_assistant_prompts(language)
            
            # 构建提示词
            if stage == "深入追问":
                # 聊天模式使用基础提示词，并加入历史记录
                prompt = system_base_prompt
                if history_text:
                    prompt += f"\n\n历史对话：\n{history_text}"
                
                # 检测是否是直接粘贴的题目（通常包含"输入"、"输出"、"样例"等关键词）
                problem_keywords = ["输入格式", "输出格式", "样例输入", "样例输出", "数据范围", "题目描述", "算法题", "编程题"]
                is_problem_statement = any(keyword in question for keyword in problem_keywords)
                
                if is_problem_statement:
                    prompt += f"\n\n【特别提醒】：学生提交了一个编程题目，请不要直接给出代码解答。而是要：\n"
                    prompt += f"1. 先询问学生对这个问题的理解和初步想法\n"
                    prompt += f"2. 引导学生分析问题的核心要求\n"
                    prompt += f"3. 帮助学生思考可能用到的数据结构和算法\n"
                    prompt += f"4. 通过提问的方式引导学生建立解题思路\n\n"
                
                prompt += f"\n\n当前问题：{question}"
            else:
                # 其他阶段的处理
                if  stage == "核心代码生成":
                    prompt = system_prompts.get("核心代码生成") if stage == "核心代码生成" else system_prompts["核心语句"]
                    # prompt += f"\n\n参考答案代码：\n{data.get('reference_answer')}"
                elif stage == "框架":
                    prompt = system_prompts["框架"]
                elif stage == "伪代码生成":
                    prompt = system_prompts.get("伪代码生成") if stage == "伪代码生成" else system_prompts["伪代码"]
                elif stage == "错误诊断":
                    prompt = system_prompts.get("错误诊断") if stage == "错误诊断" else system_prompts["错误代码分析"]
                else:
                    prompt = system_prompts["思路"]
                
                # 为非聊天阶段也添加历史记录上下文
                if history_text:
                    prompt += f"\n\n历史对话：\n{history_text}"
                prompt += f"\n\n问题：{question}"
            
            # 供外部模型 system 消息使用
            system_content = prompt  # 简化处理，直接用 prompt
            if stage != "深入追问":
                system_content = system_prompts.get(stage, system_base_prompt)

            ai_response = ""
            
            if selected_model == "xiaohang":
                # 创建 XiaohangLLM 实例并直接使用
                llm = XiaohangLLM()
                for content_piece in llm._call(prompt):
                    ai_response += content_piece  # 只用于存储到Redis
                    yield content_piece  # 流式输出给前端
            else:
                # 外部模型分发（SIFLOW 兼容 OpenAI Chat Completions）
                endpoint = MODEL_ENDPOINTS.get(selected_model)
                if not endpoint:
                    yield f"错误: 未知模型 '{selected_model}'"
                else:
                    messages = [
                        {"role": "system", "content": "你是C语言数据结构与算法的专家。"}, # 简单 system prompt
                        {"role": "user", "content": prompt},
                    ]
                    api_key = os.getenv("SIFLOW_API_KEY", "EMPTY")
                    for piece in stream_chat_completion(
                        url=endpoint["url"],
                        model=endpoint["model"],
                        messages=messages,
                        api_key=api_key,
                        timeout=0
                    ):
                        ai_response += piece
                        yield piece
            
            # 存储AI回复到Redis
            ai_message = {
                "role": "assistant",
                "content": ai_response,
                "stage": stage,
                "timestamp": time.time()
            }
            app.config['SESSION_REDIS'].rpush(chat_history_key, json.dumps(ai_message))
            
            # 保持Redis历史记录在合理范围内（最多50条）
            current_length = app.config['SESSION_REDIS'].llen(chat_history_key)
            if current_length > 50:
                app.config['SESSION_REDIS'].ltrim(chat_history_key, -50, -1)
            
        except Exception as e:
            yield f"错误: {str(e)}"
    
    return Response(stream_with_context(generate_response()), mimetype='text/event-stream')

@app.route('/api/generate_questions', methods=['POST'])
def generate_questions():
    data = request.json
    question_type = data.get('type', 'choice')
    difficulty = data.get('difficulty', 'medium')
    count = data.get('count', 3)
    topics = data.get('topics', [])
    selected_model = data.get('model', 'coder32b')
    
    # 构建提示词
    prompt = question_generation_prompts.get(question_type, question_generation_prompts['choice'])
    prompt += f"\n\n难度等级：{difficulty}\n题目数量：{count}\n知识点：{', '.join(topics)}"
    
    def generate_response():
        try:
            ai_response = ""
            if selected_model in MODEL_ENDPOINTS and selected_model != "xiaohang":
                endpoint = MODEL_ENDPOINTS.get(selected_model)
                if not endpoint:
                    yield f"错误: 未知模型 '{selected_model}'"
                else:
                    messages = [
                        {"role": "system", "content": "你是C语言数据结构与算法的出题专家，请严格按输出格式生成题目并使用中文回答。"},
                        {"role": "user", "content": prompt},
                    ]
                    api_key = os.getenv("SIFLOW_API_KEY", "EMPTY")
                    for piece in stream_chat_completion(
                        url=endpoint["url"],
                        model=endpoint["model"],
                        messages=messages,
                        api_key=api_key,
                        timeout=0
                    ):
                        ai_response += piece
                        yield piece
            else:
                from config import chat_with_xiaohang
                for content_piece in chat_with_xiaohang(prompt):
                    yield content_piece  # 流式输出给前端
        except Exception as e:
            error_msg = f"生成题目时出错：{str(e)}"
            yield error_msg
    
    return Response(stream_with_context(generate_response()), mimetype='text/plain')

@app.route('/api/generate_exam', methods=['POST'])
def generate_exam():
    """生成完整试卷"""
    def generate_response():
        try:
            from config import chat_with_xiaohang
            for content_piece in chat_with_xiaohang(exam_generation_prompt):
                yield content_piece  # 流式输出给前端
        except Exception as e:
            error_msg = f"生成试卷时出错：{str(e)}"
            yield error_msg
    
    return Response(stream_with_context(generate_response()), mimetype='text/plain')

@app.route('/api/generate_testcases', methods=['POST'])
def generate_testcases():
    code = request.json.get('code')
    problem_description = request.json.get('problem_description', '')
    test_input = request.json.get('test_input', '')  # 用户提供的测试输入
    
    def generate_response():
        try:
            # 使用JDoodle API运行代码
            jdoodle_url = "https://api.jdoodle.com/v1/execute"
            jdoodle_data = {
                "clientId": "3794db0188300d79082006cf54a5aef",
                "clientSecret": "1bf8131ca9d7fdaeb4ec25c7442733c716f76cab9b5243712a626a8d33d2806b",
                "script": code,
                "language": "c",
                "versionIndex": "5",
                "stdin": test_input  # 添加用户输入的测试数据
            }
            
            # 执行代码
            response = requests.post(jdoodle_url, json=jdoodle_data)
            execution_result = response.json()
            
            if execution_result.get('error'):
                yield f"代码执行错误：{execution_result['error']}\n\n"
                return
            
            # 显示测试点结果
            output = execution_result.get('output', '').strip()
            yield f"## 测试点生成结果\n\n"
            yield f"**问题描述：** {problem_description}\n\n"
            yield f"**测试输入：**\n```\n{test_input}\n```\n\n"
            yield f"**程序输出：**\n```\n{output}\n```\n\n"
            yield f"**测试点状态：** {'✅ 执行成功' if not execution_result.get('error') else '❌ 执行失败'}\n\n"
            
            # 如果有编译警告或其他信息
            if execution_result.get('memory'):
                yield f"**内存使用：** {execution_result['memory']}\n\n"
            if execution_result.get('cpuTime'):
                yield f"**CPU时间：** {execution_result['cpuTime']}\n\n"
            
            yield f"---\n\n"
            yield f"💡 **说明：** 以上输入和输出构成一个测试点，可用于验证其他代码实现的正确性。\n"
            
        except Exception as e:
            yield f"错误: {str(e)}"

    return Response(stream_with_context(generate_response()), mimetype='text/event-stream')

@app.route('/api/generate_problem_testcases', methods=['POST'])
def generate_problem_testcases():
    problem_description = request.json.get('problem_description', '')
    count = request.json.get('count', 5)
    
    def generate_response():
        try:
            # yield "正在解析题目...\n\n"
            # time.sleep(0.5)
            yield f"## 智能生成的测试点\n\n"
            yield f"**问题描述：** {problem_description}\n\n"
            yield f"> 正在使用AI生成测试数据脚本，生成数量：{count}个...\n\n"
            
            # 使用 generator_kit 生成测试用例
            testcases = generate_cases(problem_description, count=count)
            
            yield f"### 生成成功！\n\n"
            
            for index, tc in enumerate(testcases):
                yield f"### 测试点 {index + 1}\n"
                yield f"**输入：**\n```\n{tc['input']}\n```\n"
                yield f"**预期输出：**\n```\n{tc['output']}\n```\n\n"
                # time.sleep(0.1) # 模拟流式效果
                
        except Exception as e:
            yield f"\n\n**生成失败:** {str(e)}"

    return Response(stream_with_context(generate_response()), mimetype='text/event-stream')

# 添加智能助教API端点
@app.route('/api/tutor/init', methods=['POST'])
def init_tutor_session():
    """
    初始化智能助教会话，AI主动提问需要什么帮助
    """
    # 若已有会话则复用；否则创建新的会话ID
    session_id = session.get('session_id')
    if not session_id:
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
    user_id = session.get('user_id', 'default_user')
    
    chat_history_key = f"chat_history:{user_id}:{session_id}"
    
    # 不再默认清空历史记录；仅在显式重置接口中清空
    
    def generate_response():
        try:
            # 构建提示词，让AI主动提问
            prompt = """你是一个C语言数据结构和算法的智能助教，请以引导式学习的方式帮助学生学习。请主动向学生打招呼并询问他们需要什么帮助。要求：
1. 用亲切友好的语气主动打招呼
2. 询问学生需要在哪个方面获得帮助（比如具体的数据结构或算法问题）
3. 只提出问题，不要自己回答
4. 不要输出任何评估结果标记（如[评估结果:好]等）

请开始你的提问："""
            
            # 调用AI模型
            llm = OllamaLLM()  # 或者使用 XiaohangLLM()
            full_response = ""
            for content_piece in llm._call(prompt):
                full_response += content_piece
                yield content_piece
                
            # 存储AI回复到Redis
            ai_message = {
                "role": "assistant",
                "content": full_response,
                "stage": "init",
                "timestamp": time.time()
            }
            app.config['SESSION_REDIS'].rpush(chat_history_key, json.dumps(ai_message))
            
        except Exception as e:
            yield f"错误: {str(e)}"
    
    return Response(stream_with_context(generate_response()), mimetype='text/event-stream')

@app.route('/api/xiaohang_integration/generate_problem', methods=['POST'])
def xiaohang_generate_problem():
    try:
        data = request.json
        tag = data.get('tag', 'Array')
        difficulty_str = data.get('difficulty', 'Easy')
        problem_type_str = data.get('problem_type', 'fill_in_the_blank')
        model = data.get('model', 'coder480b')

        # Map string to Enum
        try:
            difficulty = Difficulty(difficulty_str)
        except ValueError:
            difficulty = Difficulty.EASY # Default

        try:
            problem_type = ProblemType(problem_type_str)
        except ValueError:
            problem_type = ProblemType.FILL_IN_THE_BLANK # Default

        result = generate_problem(tag, difficulty, problem_type, model=model)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------- 答题记录查询 API (保留 20260212 版本) ----------------------

@app.route('/api/records/student/<student_id>', methods=['GET'])
def get_student_records(student_id):
    """查询某个学生的答题记录"""
    student = Student.query.filter_by(student_id=student_id).first()
    if not student:
        return jsonify({"error": "学生不存在", "records": []}), 404

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    topic = request.args.get('topic', None)

    query = AnswerRecord.query.filter_by(student_db_id=student.id)
    if topic:
        query = query.filter_by(topic=topic)
    query = query.order_by(AnswerRecord.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "student": student.to_dict(),
        "records": [r.to_dict() for r in pagination.items],
        "total": pagination.total,
        "page": page,
        "pages": pagination.pages
    })


@app.route('/api/records/student/<student_id>/mastery', methods=['GET'])
def get_student_mastery(student_id):
    """查询某个学生的知识点掌握度"""
    student = Student.query.filter_by(student_id=student_id).first()
    if not student:
        return jsonify({"error": "学生不存在"}), 404

    mastery_list = KnowledgeMastery.query.filter_by(student_db_id=student.id).all()
    return jsonify({
        "student": student.to_dict(),
        "mastery": [m.to_dict() for m in mastery_list]
    })


@app.route('/api/records/stats', methods=['GET'])
def get_overall_stats():
    """全校答题统计概览"""
    from sqlalchemy import func

    total_students = Student.query.count()
    total_records = AnswerRecord.query.count()
    correct_records = AnswerRecord.query.filter_by(is_correct=True).count()

    topic_stats = db.session.query(
        AnswerRecord.topic,
        func.count(AnswerRecord.id).label('total'),
        func.sum(db.case((AnswerRecord.is_correct == True, 1), else_=0)).label('correct')
    ).group_by(AnswerRecord.topic).all()

    return jsonify({
        "total_students": total_students,
        "total_records": total_records,
        "overall_accuracy": round(correct_records / total_records * 100, 1) if total_records > 0 else 0,
        "topic_stats": [
            {
                "topic": t.topic,
                "total": t.total,
                "correct": int(t.correct or 0),
                "accuracy": round(int(t.correct or 0) / t.total * 100, 1) if t.total > 0 else 0
            }
            for t in topic_stats
        ]
    })


@app.route('/api/records/register', methods=['POST'])
def register_student():
    """注册/更新学生信息"""
    data = request.json
    sid = data.get('student_id', '').strip()
    if not sid:
        return jsonify({"error": "学号不能为空"}), 400

    name = data.get('name', '')
    class_name = data.get('class_name', '')

    student = Student.query.filter_by(student_id=sid).first()
    if student:
        if name:
            student.name = name
        if class_name:
            student.class_name = class_name
        db.session.commit()
    else:
        student = Student(student_id=sid, name=name, class_name=class_name)
        db.session.add(student)
        db.session.commit()

    # 把 student_id 存入 session，后续答题自动关联
    session['student_id_number'] = sid
    return jsonify({"message": "注册成功", "student": student.to_dict()})


@app.route('/api/records/history', methods=['GET'])
def get_history_records():
    """查询当前学生的答题历史（按题目分组）"""
    student_id = session.get('student_id_number', 'anonymous')
    student = Student.query.filter_by(student_id=student_id).first()
    if not student:
        return jsonify({"records": [], "total": 0})

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    topic_filter = request.args.get('topic', None)

    query = AnswerRecord.query.filter_by(student_db_id=student.id)
    if topic_filter:
        query = query.filter(AnswerRecord.topic.like(f'%{topic_filter}%'))
    query = query.order_by(AnswerRecord.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    records = []
    for r in pagination.items:
        records.append({
            'id': r.id,
            'topic': r.topic,
            'difficulty': r.difficulty,
            'problem_text': r.problem_text,
            'submitted_code': r.submitted_code,
            'diagnosis_result': r.diagnosis_result,
            'is_correct': r.is_correct,
            'language': r.language,
            'created_at': r.created_at.strftime('%Y-%m-%d %H:%M') if r.created_at else ''
        })

    return jsonify({
        "student_id": student_id,
        "records": records,
        "total": pagination.total,
        "page": page,
        "pages": pagination.pages
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
