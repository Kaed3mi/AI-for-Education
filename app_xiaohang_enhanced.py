"""
小航辅导模块 - 增强版
新增功能：
1. 题目不包含提示
2. 正确答案模块
3. 追问功能
4. 渴求知识功能
5. 先答案后分解：生成题目时同时生成标准答案，各模块基于答案保持一致性
6. 模块间上下文传递链：思路→伪代码→框架→核心语句，后续模块基于前置模块输出
"""
from flask import Blueprint, request, jsonify, Response, stream_with_context, session
from config import XiaohangLLM, get_system_base_prompt, get_system_prompts, get_llm
from models import save_answer_record
import json
import uuid
import time
import os

# 创建Blueprint
xiaohang_enhanced_bp = Blueprint('xiaohang_enhanced', __name__, url_prefix='/api/xiaohang')

# 知识点列表
KNOWLEDGE_POINTS = [
    '栈', '队列', '数组', '链表', '哈希表', '散列表', '堆', '优先队列',
    '树', '二叉树', '二叉搜索树', 'AVL', '红黑树', 'B树', '字典树', 'Trie',
    '图', 'DFS', 'BFS', '最短路', '最小生成树', '拓扑排序',
    '排序', '查找', '动态规划', '贪心', '回溯', '递归'
]

# 难度级别对应的提示词
DIFFICULTY_PROMPTS = {
    "简单": "设计一道简单难度的编程题，适合初学者，主要考查基础概念和简单操作。",
    "中等": "设计一道中等难度的编程题，需要综合运用知识点，考查算法设计能力。",
    "困难": "设计一道困难难度的编程题，需要深入理解算法原理，考查优化和复杂场景处理能力。"
}

# 模块依赖关系定义
GUIDANCE_DEPENDENCIES = {
    '思路': [],                          # 思路无依赖，直接基于标准答案
    '框架': ['思路'],                     # 框架依赖思路（智能审题）
    '伪代码': ['思路', '框架'],            # 伪代码依赖思路和框架（智能审题+代码框架）
    '核心语句': ['思路', '框架', '伪代码']  # 核心语句依赖所有前置模块
}

def get_redis_client():
    """获取Redis客户端"""
    from flask import current_app
    return current_app.config['SESSION_REDIS']

def get_previous_guidance_outputs(session_id, guidance_type):
    """获取前置模块的输出，用于构建上下文传递链"""
    redis_client = get_redis_client()
    previous_outputs = {}
    
    dependencies = GUIDANCE_DEPENDENCIES.get(guidance_type, [])
    for dep in dependencies:
        key = f"xiaohang_guidance_output:{session_id}:{dep}"
        data = redis_client.get(key)
        if data:
            previous_outputs[dep] = data.decode('utf-8')
    
    return previous_outputs

def build_constraint_context(previous_outputs, standard_answer, guidance_type=None):
    """构建约束上下文，包含标准答案和前置模块输出。
    对于代码补全（核心语句）模块，标准答案会被脱敏处理，避免LLM直接输出完整代码。
    """
    context_parts = []
    
    # 标准答案作为核心约束（不直接展示给学生）
    if standard_answer:
        if guidance_type == '核心语句':
            # 代码补全模块：对标准答案进行脱敏，只提供结构描述，不提供完整可运行代码
            context_parts.append(f"""【标准答案（已脱敏 - 仅供参考代码结构和算法思路，严禁直接输出完整实现）】：
以下是标准答案的代码结构概要，你需要基于此结构生成带有 TODO 空缺的代码：
---
{_redact_standard_answer_for_completion(standard_answer)}
---
【再次警告】：上述内容仅用于了解代码结构和算法方向。你输出的代码中，TODO 标记处必须只有注释说明，绝对不能包含任何实现代码。""")
        else:
            context_parts.append(f"""【标准答案（内部参考，用于保证一致性，不要直接展示给学生）】：
{standard_answer}""")
    
    # 前置模块输出作为约束
    if '思路' in previous_outputs:
        context_parts.append(f"""【已生成的解题思路】：
{previous_outputs['思路']}""")
    
    if '伪代码' in previous_outputs:
        context_parts.append(f"""【已生成的伪代码】：
{previous_outputs['伪代码']}""")
    
    if '框架' in previous_outputs:
        context_parts.append(f"""【已生成的程序框架】：
{previous_outputs['框架']}""")
    
    return "\n\n".join(context_parts)


def _redact_standard_answer_for_completion(standard_answer):
    """对标准答案进行脱敏处理，移除核心实现细节，只保留结构框架描述。
    防止LLM在代码补全模块中直接复制完整代码。
    """
    import re
    lines = standard_answer.split('\n')
    redacted_lines = []
    in_code_block = False
    code_block_lang = ''
    func_signatures = []  # 收集函数签名
    
    for line in lines:
        stripped = line.strip()
        # 检测代码块开始
        if stripped.startswith('```') and not in_code_block:
            in_code_block = True
            code_block_lang = stripped[3:].strip()
            redacted_lines.append(f'[代码块 - {code_block_lang or "code"}]')
            redacted_lines.append('[此处为标准答案的完整实现代码，已隐藏]')
            redacted_lines.append('[你需要基于算法思路自行构建带TODO空缺的代码框架]')
            continue
        elif stripped.startswith('```') and in_code_block:
            in_code_block = False
            redacted_lines.append('[代码块结束]')
            continue
        
        if in_code_block:
            # 在代码块内，只提取函数签名和结构信息，不保留实现
            # 提取C语言函数签名
            func_match = re.match(r'^(\s*)((?:void|int|char|float|double|long|short|unsigned|struct\s+\w+)\s*\*?\s+\w+\s*\([^)]*\))\s*\{?\s*$', line)
            if func_match:
                func_signatures.append(f'  - 函数: {func_match.group(2).strip()}')
            # 提取Python函数定义
            py_func_match = re.match(r'^(\s*)def\s+(\w+\s*\([^)]*\))', line)
            if py_func_match:
                func_signatures.append(f'  - 函数: {py_func_match.group(2).strip()}')
            # 跳过代码块内的具体实现
            continue
        else:
            # 非代码块内容保留（如markdown说明文字）
            redacted_lines.append(line)
    
    result = '\n'.join(redacted_lines)
    if func_signatures:
        result += '\n\n[标准答案包含的函数结构]：\n' + '\n'.join(func_signatures)
    
    return result

def save_guidance_output(session_id, guidance_type, content):
    """保存模块输出到Redis，供后续模块使用"""
    redis_client = get_redis_client()
    key = f"xiaohang_guidance_output:{session_id}:{guidance_type}"
    redis_client.setex(key, 3600, content)

def clear_all_guidance_outputs(session_id):
    """清理所有模块输出（切换题目或重置时调用）"""
    redis_client = get_redis_client()
    for guidance_type in GUIDANCE_DEPENDENCIES.keys():
        key = f"xiaohang_guidance_output:{session_id}:{guidance_type}"
        redis_client.delete(key)
    # 同时清理叶子节点缓存
    leaf_key = f"xiaohang_framework_leaves:{session_id}"
    redis_client.delete(leaf_key)
    # 同时清理追问历史
    for guidance_type in GUIDANCE_DEPENDENCIES.keys():
        chat_key = f"xiaohang_guidance_chat:{session_id}:{guidance_type}"
        redis_client.delete(chat_key)
    # 清理右侧模块缓存（代码诊断结果、提示历史）
    diagnosis_key = f"xiaohang_diagnosis:{session_id}"
    redis_client.delete(diagnosis_key)
    hint_history_key = f"xiaohang_hint_history:{session_id}"
    redis_client.delete(hint_history_key)
    # 递增 generation token，使正在运行的 pregenerate_all 失效
    gen_token_key = f"xiaohang_gen_token:{session_id}"
    redis_client.incr(gen_token_key)
    redis_client.expire(gen_token_key, 3600)


def get_generation_token(session_id):
    """获取当前 generation token"""
    redis_client = get_redis_client()
    gen_token_key = f"xiaohang_gen_token:{session_id}"
    val = redis_client.get(gen_token_key)
    return int(val) if val else 0


def extract_leaf_nodes_from_framework(framework_text):
    """从框架JSON文本中提取叶子节点（needsFurtherDecomposition=false的子问题）
    
    如果所有子问题都不需要继续分解，则它们就是叶子节点。
    如果某些子问题需要继续分解，则它们不是叶子节点（等待用户进一步分解后更新）。
    """
    import re
    try:
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', framework_text)
        if json_match:
            data = json.loads(json_match.group(1))
        else:
            first_brace = framework_text.index('{')
            last_brace = framework_text.rindex('}')
            data = json.loads(framework_text[first_brace:last_brace + 1])
        
        if not data or 'subProblems' not in data:
            return []
        
        leaf_nodes = []
        for sub in data.get('subProblems', []):
            if not sub.get('needsFurtherDecomposition', True):
                leaf_nodes.append({
                    'name': sub.get('name', ''),
                    'description': sub.get('description', ''),
                    'controlType': sub.get('controlType', 'sequence'),
                    'ipo': sub.get('ipo', {}),
                    'codeHint': sub.get('codeHint', '')
                })
            else:
                # 需要继续分解的节点暂时也加入，标记为待分解
                leaf_nodes.append({
                    'name': sub.get('name', ''),
                    'description': sub.get('description', ''),
                    'controlType': sub.get('controlType', 'sequence'),
                    'ipo': sub.get('ipo', {}),
                    'codeHint': sub.get('codeHint', ''),
                    'pendingDecomposition': True
                })
        
        return leaf_nodes
    except Exception as e:
        print(f"提取叶子节点失败: {e}")
        return []


def format_leaf_nodes_for_prompt(leaf_nodes):
    """将叶子节点列表格式化为提示词中的约束文本"""
    if not leaf_nodes:
        return ""
    
    # 过滤掉待分解的节点，只保留真正的叶子节点
    final_leaves = [n for n in leaf_nodes if not n.get('pendingDecomposition', False)]
    if not final_leaves:
        return ""
    
    ctrl_icons = {'sequence': '📋 顺序结构', 'selection': '🔀 选择结构', 'loop': '🔄 循环结构'}
    
    text = "【代码框架最终分解结果 - 叶子节点列表（伪代码和代码补全必须与此一一对应）】：\n"
    text += f"共 {len(final_leaves)} 个最终子模块，按执行顺序排列：\n\n"
    
    for i, node in enumerate(final_leaves, 1):
        ctrl = ctrl_icons.get(node.get('controlType', 'sequence'), '📋 顺序结构')
        text += f"第{i}部分：{node['name']}（{ctrl}）\n"
        if node.get('description'):
            text += f"  描述：{node['description']}\n"
        ipo = node.get('ipo', {})
        if ipo.get('input'):
            text += f"  输入：{ipo['input']}\n"
        if ipo.get('storage'):
            text += f"  存储：{ipo['storage']}\n"
        if ipo.get('process'):
            text += f"  处理：{ipo['process']}\n"
        if ipo.get('output'):
            text += f"  输出：{ipo['output']}\n"
        text += "\n"
    
    text += "【一致性要求】：\n"
    text += f"1. 伪代码必须严格按照上述 {len(final_leaves)} 个子模块的顺序组织，每个子模块对应伪代码中的一个逻辑块\n"
    text += f"2. 代码补全的结构必须与上述 {len(final_leaves)} 个子模块一一对应\n"
    text += "3. 正确答案的代码结构也必须能映射到上述子模块\n"
    
    return text

@xiaohang_enhanced_bp.route('/init_session', methods=['POST'])
def init_session():
    """初始化小航辅导会话"""
    data = request.json
    selected_topics = data.get('topics', [])
    
    # 验证选择的知识点数量
    if len(selected_topics) > 3:
        return jsonify({"error": "最多只能选择3个知识点"}), 400
    
    if len(selected_topics) == 0:
        return jsonify({"error": "请至少选择1个知识点"}), 400
    
    # 创建新的会话ID
    session_id = str(uuid.uuid4())
    session['xiaohang_session_id'] = session_id
    session['xiaohang_topics'] = selected_topics
    session['xiaohang_difficulty'] = '简单'
    session['xiaohang_correct_count'] = 0
    session['xiaohang_model'] = 'loopcoder'  # 默认使用LoopCoder大模型
    session['xiaohang_language'] = 'C'  # 默认使用C语言
    
    return jsonify({
        "message": "会话初始化成功",
        "session_id": session_id,
        "topics": selected_topics
    })

@xiaohang_enhanced_bp.route('/change_language', methods=['POST'])
def change_language():
    """切换编程语言"""
    data = request.json
    language = data.get('language', 'C')
    if language not in ('C', 'Python'):
        return jsonify({"error": "不支持的语言"}), 400
    session['xiaohang_language'] = language
    return jsonify({"message": f"语言已切换为{language}"})

@xiaohang_enhanced_bp.route('/generate_problem', methods=['POST'])
def generate_problem():
    """生成编程题目（不包含提示）- 同时生成并缓存标准答案"""
    session_id = session.get('xiaohang_session_id')
    if not session_id:
        return jsonify({"error": "会话未初始化"}), 400
    
    topics = session.get('xiaohang_topics', [])
    difficulty = session.get('xiaohang_difficulty', '简单')
    
    # 提前获取 Redis 客户端，避免在生成器中获取
    redis_client = get_redis_client()
    problem_key = f"xiaohang_problem:{session_id}"
    
    def generate_response():
        try:
            # 清理之前的模块输出（新题目需要重新生成所有模块）
            clear_all_guidance_outputs(session_id)
            
            # 构建题目生成提示词（不包含提示部分）
            topics_str = '、'.join(topics)
            language = session.get('xiaohang_language', 'C')
            lang_name = 'C语言' if language == 'C' else 'Python'
            prompt = f"""你是一名专业的{lang_name}数据结构与算法出题专家。请生成一道{difficulty}难度的编程题。

【知识点要求】：
题目必须综合考查以下知识点：{topics_str}

【难度要求】：
{DIFFICULTY_PROMPTS[difficulty]}

【输出格式】：
## 编程题目

**题目描述：** [清晰描述问题，不要给出任何解题提示或思路]

**输入格式：** [输入说明]

**输出格式：** [输出说明]

**样例输入：**
```
[样例输入数据]
```

**样例输出：**
```
[样例输出数据]
```

**数据范围：** [数据规模约束]

请开始生成题目："""
            
            # 调用AI模型生成题目
            llm = get_llm(session.get('xiaohang_model', 'xhang'))
            problem_text = ""
            for content_piece in llm._call(prompt):
                problem_text += content_piece
                yield content_piece
            
            # 题目生成完成后，立即存储到Redis（先不含标准答案）
            # 这样用户可以立即开始使用辅导功能
            redis_client.setex(
                problem_key,
                3600,  # 1小时过期
                json.dumps({
                    "problem": problem_text,
                    "standard_answer": "",  # 先存空，稍后更新
                    "difficulty": difficulty,
                    "topics": topics,
                    "timestamp": time.time()
                })
            )
            
            # 后台生成标准答案（不展示给用户）
            lang_code_block = 'c' if language == 'C' else 'python'
            lang_desc = 'C语言' if language == 'C' else 'Python'
            main_func_req = '3. 包含必要的头文件和main函数' if language == 'C' else '3. 包含完整的可运行代码结构'
            answer_prompt = f"""你是一名专业的{lang_desc}数据结构与算法专家。请为以下题目提供完整的正确答案代码。

【题目】：
{problem_text}

【知识点】：{topics_str}

【要求】：
1. 提供完整的、可运行的{lang_desc}代码
2. 代码中必须包含详细、必要的注释，解释关键步骤和逻辑
{main_func_req}
4. 不需要在代码外单独说明算法思路

【输出格式】：
## 标准答案

**完整代码：**
```{lang_code_block}
[完整的{lang_desc}代码，包含详细注释]
```

**复杂度分析：**
- 时间复杂度：[分析]
- 空间复杂度：[分析]

请生成标准答案："""
            
            # 生成标准答案（不流式输出给用户）
            standard_answer = ""
            for content_piece in llm._call(answer_prompt):
                standard_answer += content_piece
            
            # 更新Redis中的标准答案
            redis_client.setex(
                problem_key,
                3600,  # 1小时过期
                json.dumps({
                    "problem": problem_text,
                    "standard_answer": standard_answer,
                    "standard_answer_language": language,
                    "difficulty": difficulty,
                    "topics": topics,
                    "timestamp": time.time()
                })
            )
            
        except Exception as e:
            yield f"\n\n错误: {str(e)}"
    
    return Response(stream_with_context(generate_response()), mimetype='text/event-stream')


@xiaohang_enhanced_bp.route('/set_custom_problem', methods=['POST'])
def set_custom_problem():
    """用户自主出题 - 将用户输入的题目存入Redis，并后台生成标准答案"""
    session_id = session.get('xiaohang_session_id')
    if not session_id:
        return jsonify({"error": "会话未初始化"}), 400

    data = request.get_json()
    problem_text = (data.get('problem_text') or '').strip()
    if not problem_text:
        return jsonify({"error": "题目内容不能为空"}), 400

    topics = session.get('xiaohang_topics', [])
    language = session.get('xiaohang_language', 'C')
    redis_client = get_redis_client()
    problem_key = f"xiaohang_problem:{session_id}"

    # 清理之前的模块输出
    clear_all_guidance_outputs(session_id)

    # 先存储题目（标准答案稍后更新）
    redis_client.setex(
        problem_key,
        3600,
        json.dumps({
            "problem": problem_text,
            "standard_answer": "",
            "difficulty": "自主出题",
            "topics": topics,
            "timestamp": time.time()
        })
    )

    # 后台生成标准答案
    try:
        topics_str = '、'.join(topics) if topics else '综合'
        lang_code_block = 'c' if language == 'C' else 'python'
        lang_desc = 'C语言' if language == 'C' else 'Python'
        main_func_req = '3. 包含必要的头文件和main函数' if language == 'C' else '3. 包含完整的可运行代码结构'
        answer_prompt = f"""你是一名专业的{lang_desc}数据结构与算法专家。请为以下题目提供完整的正确答案代码。

【题目】：
{problem_text}

【知识点】：{topics_str}

【要求】：
1. 提供完整的、可运行的{lang_desc}代码
2. 代码中必须包含详细、必要的注释，解释关键步骤和逻辑
{main_func_req}
4. 不需要在代码外单独说明算法思路

【输出格式】：
## 标准答案

**完整代码：**
```{lang_code_block}
[完整的{lang_desc}代码，包含详细注释]
```

**复杂度分析：**
- 时间复杂度：[分析]
- 空间复杂度：[分析]

请生成标准答案："""

        llm = get_llm(session.get('xiaohang_model', 'xhang'))
        standard_answer = ""
        for content_piece in llm._call(answer_prompt):
            standard_answer += content_piece

        redis_client.setex(
            problem_key,
            3600,
            json.dumps({
                "problem": problem_text,
                "standard_answer": standard_answer,
                "standard_answer_language": language,
                "difficulty": "自主出题",
                "topics": topics,
                "timestamp": time.time()
            })
        )
    except Exception as e:
        print(f"[自主出题] 标准答案生成失败: {e}")

    return jsonify({"message": "自主出题设置成功", "problem_text": problem_text})


@xiaohang_enhanced_bp.route('/submit_code', methods=['POST'])
def submit_code():
    """提交代码并判断正确性 - 简洁判定模式"""
    session_id = session.get('xiaohang_session_id')
    if not session_id:
        return jsonify({"result": "error", "message": "会话未初始化，请先选择知识点并生成题目"}), 400
    
    data = request.json
    user_code = data.get('code', '')
    
    # 获取当前题目
    redis_client = get_redis_client()
    problem_key = f"xiaohang_problem:{session_id}"
    problem_data = redis_client.get(problem_key)
    
    if not problem_data:
        return jsonify({"result": "error", "message": "未找到当前题目，请先生成题目"}), 400
    
    problem_info = json.loads(problem_data.decode('utf-8'))
    current_problem = problem_info['problem']
    standard_answer = problem_info.get('standard_answer', '')
    topics = problem_info.get('topics', [])
    
    def generate_response():
        try:
            language = session.get('xiaohang_language', 'C')
            lang_code_block = 'c' if language == 'C' else 'python'
            
            prompt = f"""你是一个代码判题器。请判断学生提交的代码是否能正确解决题目。

【题目】：
{current_problem}

【知识点标签】：{', '.join(topics)}

【学生提交的代码】：
```{lang_code_block}
{user_code}
```

【标准答案（内部参考）】：
{standard_answer if standard_answer else '暂无标准答案'}

**判定规则：**
1. 重点对比学生代码与标准答案的核心逻辑是否一致
2. 如果核心算法逻辑正确、数据结构使用正确、能正确处理题目要求的输入输出，则判定为正确
3. 变量名不同、代码风格不同、注释不同等不影响正确性判定
4. 仅当存在明确的逻辑错误、算法错误、遗漏关键步骤时才判定为错误或部分正确
5. 不要因为代码写法与标准答案不完全一致就判定为部分正确或错误

**要求：只输出判定结果，不要给出任何解释、分析或建议。**

请严格按照以下格式之一输出，只输出一行：

如果正确：✅ 正确
如果部分正确（核心逻辑正确但有明确的小错误）：⚠️ 部分正确（简要说明，不超过15个字）
如果错误：❌ 错误

只输出上面一行判定，不要输出任何其他内容。"""
            
            llm = get_llm(session.get('xiaohang_model', 'xhang'))
            full_response = ""
            for content_piece in llm._call(prompt):
                full_response += content_piece
                yield content_piece
            
            # 判断是否正确
            is_correct = "✅ 正确" in full_response and "部分正确" not in full_response
            
            # 持久化答题记录到 MySQL
            try:
                from flask import current_app
                student_id_number = session.get('student_id_number', 'anonymous')
                topic_str = ', '.join(topics) if topics else ''
                print(f"[DB] 准备保存答题记录: student={student_id_number}, topic={topic_str}, correct={is_correct}")
                save_answer_record(
                    student_id=student_id_number,
                    session_id=session_id,
                    topic=topic_str,
                    difficulty=session.get('xiaohang_difficulty', '简单'),
                    problem_text=current_problem,
                    submitted_code=user_code,
                    diagnosis_result=full_response,
                    is_correct=is_correct,
                    language=session.get('xiaohang_language', 'C')
                )
                print(f"[DB] 答题记录保存成功")
            except Exception as db_err:
                import traceback
                print(f"[DB] 保存答题记录失败: {db_err}")
                traceback.print_exc()

            # 获取当前难度和计数
            current_difficulty = session.get('xiaohang_difficulty', '简单')
            correct_count = session.get('xiaohang_correct_count', 0)
            
            if is_correct:
                correct_count += 1
                session['xiaohang_correct_count'] = correct_count
                
                if correct_count == 1 and current_difficulty == '简单':
                    session['xiaohang_difficulty'] = '中等'
                elif correct_count == 2 and current_difficulty == '中等':
                    session['xiaohang_difficulty'] = '困难'
            
        except Exception as e:
            yield f"错误: {str(e)}"
    
    return Response(stream_with_context(generate_response()), mimetype='text/event-stream')

@xiaohang_enhanced_bp.route('/get_guidance', methods=['POST'])
def get_guidance():
    """获取启发式指导（4个模块）- 基于标准答案 + 模块间上下文传递链"""
    session_id = session.get('xiaohang_session_id')
    if not session_id:
        def error_response():
            yield "错误: 会话未初始化，请先选择知识点并生成题目"
        return Response(stream_with_context(error_response()), mimetype='text/event-stream')
    
    data = request.json
    guidance_type = data.get('type', '思路')  # 思路、框架、伪代码、核心语句
    
    # 获取当前题目和标准答案
    redis_client = get_redis_client()
    problem_key = f"xiaohang_problem:{session_id}"
    problem_data = redis_client.get(problem_key)
    
    if not problem_data:
        def error_response():
            yield "错误: 未找到当前题目，请先生成题目"
        return Response(stream_with_context(error_response()), mimetype='text/event-stream')
    
    problem_info = json.loads(problem_data.decode('utf-8'))
    current_problem = problem_info['problem']
    standard_answer = problem_info.get('standard_answer', '')  # 获取标准答案
    topics = problem_info['topics']
    
    # 获取前置模块的输出（上下文传递链）
    previous_outputs = get_previous_guidance_outputs(session_id, guidance_type)
    
    # 构建约束上下文
    constraint_context = build_constraint_context(previous_outputs, standard_answer, guidance_type=guidance_type)
    
    # 初始化该类型的对话历史
    chat_history_key = f"xiaohang_guidance_chat:{session_id}:{guidance_type}"
    
    def generate_response():
        try:
            # 记录当前 generation token
            gen_token_at_start = get_generation_token(session_id)
            
            # 使用 config.py 中的 ISPO 结构化提示词
            language = session.get('xiaohang_language', 'C')
            system_prompts = get_system_prompts(language)
            
            # 根据类型获取对应的提示词，并加入一致性约束
            if guidance_type == '核心语句':
                # 代码补全模块不强调"与标准答案保持一致"，避免LLM直接输出标准答案代码
                consistency_instruction = """
【重要约束 - 一致性要求】：
你的输出必须与前置模块（思路、框架、伪代码）的输出保持高度一致。
- 你的内容必须是对前置模块的细化和具体化
- 不要引入与前置模块矛盾的新思路或方法
- TODO标记处必须是真正的空缺，不能包含实现代码
"""
            else:
                consistency_instruction = """
【重要约束 - 一致性要求】：
你的输出必须与标准答案和前置模块的输出保持高度一致。
- 如果有标准答案，你的指导必须引导学生走向这个答案
- 如果有前置模块输出，你的内容必须是对前置模块的细化和具体化
- 不要引入与标准答案或前置模块矛盾的新思路或方法
"""
            
            if guidance_type == '思路':
                system_prompt = system_prompts.get('思路', '')
                specific_instruction = """
【思路模块特殊要求】：
基于标准答案，提炼出解题的核心思路，但不要直接暴露答案。
用启发式问题引导学生思考，让学生能够自己推导出标准答案的思路。
"""
                
            elif guidance_type == '框架':
                # 框架使用特殊的 JSON 格式提示词（用于可视化）
                system_prompt = f"""你是一名程序设计教学专家。请将问题分解为子模块。

【极其重要 - ISPO模型】：
本系统采用 ISPO 模型（不是 IPO！），每个模块必须包含四个维度：
- I (Input)：输入 - 该模块需要什么输入数据
- S (Storage)：存储 - 建议使用什么数据结构或变量来存储数据（例如：数组、链表、栈、队列、整型变量、结构体等）
- P (Process)：处理 - 如何处理数据
- O (Output)：输出 - 产生什么输出

【重要】：你必须输出一个用 ```json 和 ``` 包裹的JSON对象，格式如下：

```json
{{
    "parentProblem": "问题描述",
    "level": 0,
    "subProblems": [
        {{
            "name": "模块名",
            "description": "描述",
            "controlType": "sequence",
            "ipo": {{
                "input": "该模块需要什么输入数据",
                "storage": "建议使用什么数据结构/变量来存储（如：用数组存储n个元素、用整型变量记录栈顶指针等）",
                "process": "如何处理数据",
                "output": "产生什么输出"
            }},
            "needsFurtherDecomposition": false,
            "codeHint": "建议性的语句提示（禁止给出代码，禁止单一确定方案）"
        }}
    ],
    "overallIPO": {{
        "input": "总输入",
        "storage": "整体需要的存储结构（如：需要一个栈结构来管理数据、需要数组存储输入等）",
        "process": "总处理",
        "output": "总输出"
    }}
}}
```

【controlType取值】：
- sequence：顺序执行（变量声明、赋值、输入输出）
- selection：条件判断（if-else、switch）
- loop：循环（for、while）

【分解要求】：
1. 分解为2-4个子模块
2. 每个模块标注controlType
3. 每个模块的ipo必须包含input、storage、process、output四个字段，缺少storage字段是严重错误
4. storage字段必须具体说明建议使用的数据结构或变量类型，不能为空或写"无"
5. needsFurtherDecomposition：简单模块设为false，复杂模块设为true
6. 简单模块的codeHint必须是建议性的自然语言描述，用"可以考虑""建议"等引导语气，提供多种可能的实现思路，绝对禁止直接给出代码或单一确定的方案
7. 【禁止】不要生成"全局定义模块"、"头文件引用模块"、"main函数模块"等与程序框架结构相关的模块，这些模块由系统自动添加。你只需要分解核心算法逻辑和功能模块（如数据输入、数据处理、结果输出等）

【storage字段示例】：
- "建议使用数组存储n个操作数据，用整型变量记录操作总数"
- "可以考虑用栈结构（数组模拟或链表实现）来管理数据的入栈出栈"
- "建议用整型变量存储两个待比较的数值和比较结果"
- "可以考虑用结构体数组存储学生信息，用整型变量记录学生总数"

题目知识点：{', '.join(topics)}"""
                specific_instruction = """
【框架模块特殊要求】：
基于标准答案的代码结构进行分解，确保分解出的模块与标准答案的实现结构一致。
框架必须与已生成的智能审题（思路）保持一致，是思路的结构化表达。
框架分解出的逻辑块必须能够直接对应到后续伪代码的逻辑块，保持严格一致。
再次强调：ipo字段必须包含input、storage、process、output四个字段，这是ISPO模型的核心要求。
【再次强调禁止】：不要在subProblems中生成任何关于"全局定义"、"头文件引用(#include)"、"宏定义(#define)"、"main函数"的模块，这些由系统自动添加。只分解核心算法逻辑模块。
"""
                
            elif guidance_type == '伪代码':
                system_prompt = system_prompts.get('伪代码', '')
                # 获取叶子节点约束
                leaf_key = f"xiaohang_framework_leaves:{session_id}"
                leaf_data = redis_client.get(leaf_key)
                leaf_constraint_text = ""
                if leaf_data:
                    leaf_nodes = json.loads(leaf_data.decode('utf-8'))
                    leaf_constraint_text = format_leaf_nodes_for_prompt(leaf_nodes)
                specific_instruction = f"""
【伪代码模块特殊要求】：
基于标准答案的算法逻辑，按代码框架模块划分，为每个模块生成对应的伪代码。
伪代码必须与已生成的智能审题（思路）和代码框架保持严格一致。
伪代码的每个逻辑块必须与代码框架分解出的模块一一对应。
伪代码的逻辑流程应该能够直接映射到标准答案的代码，也能直接映射到代码补全的结构。
不要在最后添加复杂度分析，只输出伪代码内容。

【输出格式强制要求】：
- 每个代码框架模块单独输出，先写模块名称标题，再输出该模块的伪代码块（使用```pseudocode标记）
- 伪代码使用 if-then-else-end if、for-do-end for、while-do-end while 等控制结构
- 赋值使用 ← 符号，用 // 添加中文注释
- 禁止使用任何具体编程语言语法（如C的printf/scanf/malloc/#include/花括号/分号，Python的print/def/import等）
- 用自然语言动作词代替语言特定函数（如"输出(result)"代替printf，"读取输入(str)"代替scanf）

【极其重要 - 必须包含可执行逻辑语句】：
每个伪代码块的主体必须是具体的逻辑操作语句（赋值←、条件if-then、循环for-do等），注释//只是辅助说明。
绝对禁止输出只有注释没有逻辑语句的伪代码块。

{leaf_constraint_text}
"""
                
            elif guidance_type == '核心语句':
                system_prompt = system_prompts.get('核心语句', '')
                # 获取叶子节点约束
                leaf_key = f"xiaohang_framework_leaves:{session_id}"
                leaf_data = redis_client.get(leaf_key)
                leaf_constraint_text = ""
                if leaf_data:
                    leaf_nodes = json.loads(leaf_data.decode('utf-8'))
                    leaf_constraint_text = format_leaf_nodes_for_prompt(leaf_nodes)
                specific_instruction = f"""
【代码补全模块特殊要求 - 严格执行】：
生成一份带有 TODO 标记的不完整代码，其中2-3个关键算法部分被替换为 TODO 注释标记。
{'使用 // TODO: 在这里补全代码：xxx 格式' if language == 'C' else '使用 # TODO: 在这里补全代码：xxx 格式'}

【核心规则 - TODO处绝对不能有实现代码】：
1. TODO 注释标记处只能有一行注释说明需要实现什么功能，下面不能跟任何实现代码
2. 正确示例：
   // TODO: 在这里补全代码：实现密钥处理功能，去除重复字母
   （这里什么都没有，留空让学生自己写）
3. 错误示例（绝对禁止）：
   // TODO: 在这里补全代码：实现密钥处理功能
   void process_key() {{  // ← 这就是泄露了完整实现！
       ...实际代码...
   }}
4. 只输出一份代码，不要分开展示完整代码和补全部分
5. 代码补全必须与已生成的框架逻辑一致
6. 代码中的每个功能块必须与代码框架的叶子节点一一对应

{leaf_constraint_text}
"""
            
            else:
                system_prompt = "请提供相应的指导。"
                specific_instruction = ""
            
            # 构建完整提示词，包含约束上下文
            prompt = f"""{system_prompt}

{consistency_instruction}

{specific_instruction}

{constraint_context}

【题目】：
{current_problem}

请开始提供指导（确保与标准答案和前置模块保持一致）："""
            
            # 调用AI模型
            llm = get_llm(session.get('xiaohang_model', 'xhang'))
            full_response = ""
            for content_piece in llm._call(prompt):
                full_response += content_piece
                yield content_piece
            
            # 保存本模块的输出（供后续模块使用）
            # 检查题目是否已切换，避免将旧题目的输出写入新题目的缓存
            if get_generation_token(session_id) == gen_token_at_start:
                save_guidance_output(session_id, guidance_type, full_response)
            
            # 存储本次对话到Redis（用于追问）
            redis_client.rpush(
                chat_history_key,
                json.dumps({
                    "role": "assistant",
                    "content": full_response,
                    "timestamp": time.time()
                })
            )
            redis_client.expire(chat_history_key, 3600)
            
        except Exception as e:
            yield f"错误: {str(e)}"
    
    return Response(stream_with_context(generate_response()), mimetype='text/event-stream')


@xiaohang_enhanced_bp.route('/pregenerate_all', methods=['POST'])
def pregenerate_all():
    """后台预生成指定模块（框架、伪代码、核心语句）。可通过 modules 参数指定仅生成部分模块。"""
    session_id = session.get('xiaohang_session_id')
    if not session_id:
        return jsonify({"error": "会话未初始化"}), 400
    
    req_data = request.get_json(silent=True) or {}
    modules_to_generate = req_data.get('modules', ['框架', '伪代码', '核心语句'])
    
    redis_client = get_redis_client()
    problem_key = f"xiaohang_problem:{session_id}"
    problem_data = redis_client.get(problem_key)
    
    if not problem_data:
        return jsonify({"error": "未找到当前题目"}), 400
    
    problem_info = json.loads(problem_data.decode('utf-8'))
    current_problem = problem_info['problem']
    standard_answer = problem_info.get('standard_answer', '')
    is_homework = problem_info.get('homework_mode', False)
    topics = problem_info['topics']
    language = session.get('xiaohang_language', 'C')
    
    def generate_all():
        try:
            # 记录当前 generation token，用于检测题目是否已切换
            gen_token_at_start = get_generation_token(session_id)
            
            llm = get_llm(session.get('xiaohang_model', 'xhang'))
            system_prompts_map = get_system_prompts(language)
            lang_code_block = 'c' if language == 'C' else 'python'
            lang_desc = 'C语言' if language == 'C' else 'Python'
            
            # 等待标准答案生成完成（可能还在generate_problem中生成）
            # 作业模式下不会异步生成标准答案，直接跳过等待
            if standard_answer:
                standard_answer_final = standard_answer
            elif is_homework:
                standard_answer_final = ''
            else:
                max_wait = 60
                waited = 0
                while waited < max_wait:
                    # 检查题目是否已切换
                    if get_generation_token(session_id) != gen_token_at_start:
                        yield json.dumps({"status": "cancelled", "message": "题目已切换"}) + "\n"
                        return
                    problem_data_check = redis_client.get(problem_key)
                    if problem_data_check:
                        info_check = json.loads(problem_data_check.decode('utf-8'))
                        if info_check.get('standard_answer', ''):
                            standard_answer_final = info_check['standard_answer']
                            break
                    time.sleep(1)
                    waited += 1
                else:
                    standard_answer_final = ''
            
            yield json.dumps({"status": "generating", "module": "框架"}) + "\n"
            
            # === 1. 生成框架（依赖：思路） ===
            thought_output = ""
            thought_key = f"xiaohang_guidance_output:{session_id}:思路"
            # 等待思路生成完成
            max_wait_thought = 120
            waited_t = 0
            while waited_t < max_wait_thought:
                # 检查题目是否已切换
                if get_generation_token(session_id) != gen_token_at_start:
                    yield json.dumps({"status": "cancelled", "message": "题目已切换"}) + "\n"
                    return
                thought_data = redis_client.get(thought_key)
                if thought_data:
                    thought_output = thought_data.decode('utf-8')
                    break
                time.sleep(1)
                waited_t += 1
            
            constraint_parts = []
            if standard_answer_final:
                constraint_parts.append(f"【标准答案（内部参考，用于保证一致性，不要直接展示给学生）】：\n{standard_answer_final}")
            if thought_output:
                constraint_parts.append(f"【已生成的解题思路】：\n{thought_output}")
            constraint_context_framework = "\n\n".join(constraint_parts)
            
            framework_system_prompt = f"""你是一名程序设计教学专家。请将问题分解为子模块。

【极其重要 - ISPO模型】：
本系统采用 ISPO 模型（不是 IPO！），每个模块必须包含四个维度：
- I (Input)：输入 - 该模块需要什么输入数据
- S (Storage)：存储 - 建议使用什么数据结构或变量来存储数据
- P (Process)：处理 - 如何处理数据
- O (Output)：输出 - 产生什么输出

【重要】：你必须输出一个用 ```json 和 ``` 包裹的JSON对象，格式如下：

```json
{{
    "parentProblem": "问题描述",
    "level": 0,
    "subProblems": [
        {{
            "name": "模块名",
            "description": "描述",
            "controlType": "sequence",
            "ipo": {{
                "input": "输入数据",
                "storage": "存储结构建议",
                "process": "处理方式",
                "output": "输出"
            }},
            "needsFurtherDecomposition": false,
            "codeHint": "建议性的语句提示"
        }}
    ],
    "overallIPO": {{
        "input": "总输入",
        "storage": "整体存储结构",
        "process": "总处理",
        "output": "总输出"
    }}
}}
```

【controlType取值】：sequence、selection、loop

【分解要求】：
1. 分解为2-4个子模块
2. 每个模块标注controlType
3. ipo必须包含input、storage、process、output四个字段
4. storage字段必须具体说明数据结构或变量类型
5. codeHint必须是建议性自然语言描述
6. 【禁止】不要生成"全局定义模块"、"头文件引用模块"、"main函数模块"等与程序框架结构相关的模块，这些模块由系统自动添加。你只需要分解核心算法逻辑和功能模块（如数据输入、数据处理、结果输出等）

题目知识点：{', '.join(topics)}"""

            framework_prompt = f"""{framework_system_prompt}

【重要约束 - 一致性要求】：
你的输出必须与标准答案保持高度一致。框架分解出的模块必须与标准答案的代码结构一一对应。

【框架模块特殊要求】：
基于标准答案的代码结构进行分解，确保分解出的模块与标准答案的实现结构一致。
框架分解出的逻辑块必须能够直接对应到后续伪代码的逻辑块，保持严格一致。
【再次强调禁止】：不要在subProblems中生成任何关于"全局定义"、"头文件引用(#include)"、"宏定义(#define)"、"main函数"的模块，这些由系统自动添加。只分解核心算法逻辑模块。

{constraint_context_framework}

【题目】：
{current_problem}

请开始提供指导（确保与标准答案和前置模块保持一致）："""

            framework_output = ""
            for piece in llm._call(framework_prompt):
                framework_output += piece
            
            # 检查题目是否已切换
            if get_generation_token(session_id) != gen_token_at_start:
                yield json.dumps({"status": "cancelled", "message": "题目已切换"}) + "\n"
                return
            
            save_guidance_output(session_id, '框架', framework_output)
            
            # 提取框架的叶子节点并保存，供伪代码和代码补全使用
            initial_leaf_nodes = extract_leaf_nodes_from_framework(framework_output)
            if initial_leaf_nodes:
                leaf_key = f"xiaohang_framework_leaves:{session_id}"
                redis_client.setex(leaf_key, 3600, json.dumps(initial_leaf_nodes, ensure_ascii=False))
            leaf_constraint_text = format_leaf_nodes_for_prompt(initial_leaf_nodes)
            
            yield json.dumps({"status": "done", "module": "框架"}) + "\n"
            
            # 如果仅请求生成框架，则提前结束
            if '伪代码' not in modules_to_generate:
                yield json.dumps({"status": "all_done"}) + "\n"
                return
            
            yield json.dumps({"status": "generating", "module": "伪代码"}) + "\n"
            
            # === 2. 生成伪代码（依赖：思路 + 框架 + 叶子节点约束） ===
            constraint_parts_pseudo = list(constraint_parts)
            constraint_parts_pseudo.append(f"【已生成的程序框架】：\n{framework_output}")
            constraint_context_pseudo = "\n\n".join(constraint_parts_pseudo)
            
            pseudo_system_prompt = system_prompts_map.get('伪代码', '')
            pseudo_prompt = f"""{pseudo_system_prompt}

【重要约束 - 一致性要求】：
你的输出必须与标准答案和前置模块的输出保持高度一致。
伪代码的每个逻辑块必须与代码框架分解出的模块一一对应。

【伪代码模块特殊要求】：
基于标准答案的算法逻辑，按代码框架模块划分，为每个模块生成对应的伪代码。
伪代码必须与已生成的智能审题（思路）和代码框架保持严格一致。
伪代码的逻辑流程应该能够直接映射到标准答案的代码，也能直接映射到代码补全的结构。
不要在最后添加复杂度分析，只输出伪代码内容。

【输出格式强制要求】：
- 每个代码框架模块单独输出，先写模块名称标题，再输出该模块的伪代码块（使用```pseudocode标记）
- 伪代码使用 if-then-else-end if、for-do-end for、while-do-end while 等控制结构
- 赋值使用 ← 符号，用 // 添加中文注释
- 禁止使用任何具体编程语言语法（如C的printf/scanf/malloc/#include/花括号/分号，Python的print/def/import等）
- 用自然语言描述功能代替语言特定函数（如"输出结果"代替printf，"读取输入"代替scanf）

【极其重要 - 必须包含可执行逻辑语句】：
每个伪代码块的主体必须是具体的逻辑操作语句（赋值←、条件if-then、循环for-do等），注释//只是辅助说明。
绝对禁止输出只有注释没有逻辑语句的伪代码块。

{leaf_constraint_text}

{constraint_context_pseudo}

【题目】：
{current_problem}

请开始提供指导（确保与标准答案和代码框架叶子节点保持一致，伪代码的每个逻辑块必须与框架叶子节点一一对应）："""

            pseudo_output = ""
            for piece in llm._call(pseudo_prompt):
                pseudo_output += piece
            
            # 检查题目是否已切换
            if get_generation_token(session_id) != gen_token_at_start:
                yield json.dumps({"status": "cancelled", "message": "题目已切换"}) + "\n"
                return
            
            save_guidance_output(session_id, '伪代码', pseudo_output)
            
            yield json.dumps({"status": "done", "module": "伪代码"}) + "\n"
            
            # 如果不需要生成核心语句，则提前结束
            if '核心语句' not in modules_to_generate:
                yield json.dumps({"status": "all_done"}) + "\n"
                return
            
            yield json.dumps({"status": "generating", "module": "核心语句"}) + "\n"
            
            # === 3. 生成核心语句/代码补全（依赖：思路 + 框架 + 伪代码 + 叶子节点约束） ===
            # 对标准答案做脱敏处理，防止LLM直接输出完整代码
            constraint_parts_core_safe = []
            if standard_answer_final:
                constraint_parts_core_safe.append(f"【标准答案（已脱敏 - 仅供参考代码结构和算法思路，严禁直接输出完整实现）】：\n{_redact_standard_answer_for_completion(standard_answer_final)}\n【再次警告】：上述内容仅用于了解代码结构和算法方向。你输出的代码中，TODO 标记处必须只有注释说明，绝对不能包含任何实现代码。")
            if thought_output:
                constraint_parts_core_safe.append(f"【已生成的解题思路】：\n{thought_output}")
            constraint_parts_core_safe.append(f"【已生成的程序框架】：\n{framework_output}")
            constraint_parts_core_safe.append(f"【已生成的伪代码】：\n{pseudo_output}")
            constraint_context_core = "\n\n".join(constraint_parts_core_safe)
            
            core_system_prompt = system_prompts_map.get('核心语句', '')
            todo_format = '使用 // TODO: 在这里补全代码：xxx 格式' if language == 'C' else '使用 # TODO: 在这里补全代码：xxx 格式'
            core_prompt = f"""{core_system_prompt}

【重要约束 - 一致性要求】：
你的输出必须与前置模块的输出保持高度一致。

【代码补全模块特殊要求 - 严格执行】：
生成一份带有 TODO 标记的不完整代码，其中2-3个关键算法部分被替换为 TODO 注释标记。
{todo_format}

【核心规则 - TODO处绝对不能有实现代码】：
1. TODO 注释标记处只能有一行注释说明需要实现什么功能，下面不能跟任何实现代码
2. 正确示例：
   // TODO: 在这里补全代码：实现密钥处理功能，去除重复字母
   （这里什么都没有，留空让学生自己写）
3. 错误示例（绝对禁止）：
   // TODO: 在这里补全代码：实现密钥处理功能
   void process_key() {{  // ← 这就是泄露了完整实现！
       ...实际代码...
   }}
4. 只输出一份代码，不要分开展示完整代码和补全部分
5. 代码补全必须与已生成的伪代码和框架逻辑严格一致
6. 代码中的每个功能块必须与代码框架的叶子节点一一对应，用注释标明对应关系

{leaf_constraint_text}

{constraint_context_core}

【题目】：
{current_problem}

请开始提供指导（确保与代码框架叶子节点保持一致，TODO处只有注释没有实现代码）："""

            core_output = ""
            for piece in llm._call(core_prompt):
                core_output += piece
            
            # 检查题目是否已切换
            if get_generation_token(session_id) != gen_token_at_start:
                yield json.dumps({"status": "cancelled", "message": "题目已切换"}) + "\n"
                return
            
            save_guidance_output(session_id, '核心语句', core_output)
            
            yield json.dumps({"status": "done", "module": "核心语句"}) + "\n"
            yield json.dumps({"status": "all_done"}) + "\n"
            
        except Exception as e:
            yield json.dumps({"status": "error", "message": str(e)}) + "\n"
    
    return Response(stream_with_context(generate_all()), mimetype='text/event-stream')


@xiaohang_enhanced_bp.route('/decompose_problem', methods=['POST'])
def decompose_problem():
    """层次化问题分解 - 支持多层递归分解"""
    session_id = session.get('xiaohang_session_id')
    if not session_id:
        def error_response():
            yield "错误: 会话未初始化，请先选择知识点并生成题目"
        return Response(stream_with_context(error_response()), mimetype='text/event-stream')
    
    data = request.json
    level = data.get('level', 1)  # 分解层级
    parent_problem = data.get('parentProblem', '')  # 父问题名称
    parent_description = data.get('parentDescription', '')  # 父问题描述
    parent_ipo = data.get('parentIpo', {})  # 父问题的ISPO信息
    parent_control_type = data.get('parentControlType', 'sequence')  # 父问题的控制结构
    decomposition_path = data.get('decompositionPath', [])  # 从根到当前的分解路径
    
    # 获取当前题目
    redis_client = get_redis_client()
    problem_key = f"xiaohang_problem:{session_id}"
    problem_data = redis_client.get(problem_key)
    
    if not problem_data:
        def error_response():
            yield "错误: 未找到当前题目，请先生成题目"
        return Response(stream_with_context(error_response()), mimetype='text/event-stream')
    
    problem_info = json.loads(problem_data.decode('utf-8'))
    current_problem = problem_info['problem']
    standard_answer = problem_info.get('standard_answer', '')
    topics = problem_info['topics']
    language = session.get('xiaohang_language', 'C')
    
    # 构建分解历史上下文
    path_context = ""
    if decomposition_path and len(decomposition_path) > 0:
        path_context = "\n【分解历史路径】：\n"
        for i, node in enumerate(decomposition_path):
            indent = "  " * i
            ctrl_icon = {'sequence': '📋', 'selection': '🔀', 'loop': '🔄'}.get(node.get('controlType', 'sequence'), '📋')
            path_context += f"{indent}L{node.get('layer', i)}: {ctrl_icon} {node.get('name', '未命名')}\n"
            if node.get('description'):
                path_context += f"{indent}   描述: {node.get('description')}\n"
            ipo = node.get('ipo', {})
            if ipo:
                if ipo.get('input'): path_context += f"{indent}   输入: {ipo.get('input')}\n"
                if ipo.get('storage'): path_context += f"{indent}   存储: {ipo.get('storage')}\n"
                if ipo.get('process'): path_context += f"{indent}   处理: {ipo.get('process')}\n"
                if ipo.get('output'): path_context += f"{indent}   输出: {ipo.get('output')}\n"
    
    # 构建当前要分解的模块上下文
    current_module_context = f"""
【当前要继续分解的模块】：
- 模块名称: {parent_problem}
- 模块描述: {parent_description if parent_description else '无'}
- 控制结构: {parent_control_type}
- ISPO信息:
  * 输入(I): {parent_ipo.get('input', '无')}
  * 存储(S): {parent_ipo.get('storage', '无')}
  * 处理(P): {parent_ipo.get('process', '无')}
  * 输出(O): {parent_ipo.get('output', '无')}
"""
    
    def generate_response():
        try:
            prompt = f"""你是一名专业的程序设计教学专家，精通"自顶向下、逐步求精"的结构化程序设计方法。

请对以下模块进行第{level}层分解。这是学生表示"还不能写出代码"后的进一步细化分解。

【核心程序设计思想】：
1. 任何程序都由三种基本控制结构组成：顺序、选择、循环
2. 通过"分而治之"将复杂问题分解成更小、更简单的子模块
3. 每个模块用ISPO模型描述：输入(Input)→存储(Storage)→处理(Process)→输出(Output)
4. 分解的目标：让每个子模块简单到学生能直接写出代码

【极其重要 - ISPO模型说明】：
本系统采用 ISPO 模型（不是 IPO！），ipo字段必须包含四个键：
- input：该模块需要什么输入数据
- storage：建议使用什么数据结构或变量来存储数据（如数组、栈、队列、整型变量、结构体等），这是ISPO区别于IPO的关键字段
- process：如何处理数据
- output：产生什么输出
缺少 storage 字段是严重错误！

【原始题目】：
{current_problem}

【标准答案（内部参考，用于保证分解与实现一致，不要直接展示给学生）】：
{standard_answer if standard_answer else '暂无'}
{path_context}
{current_module_context}

【第{level}层分解要求】：
1. 将当前模块「{parent_problem}」分解为2-4个更小的子模块
2. 每个子模块的粒度要比上一层更细，更接近可直接编码的程度
3. 分解必须基于父模块的ISPO信息，子模块的输入输出要与父模块衔接
4. 明确标注控制结构类型和ISPO（ipo字段必须包含input、storage、process、output四个键）
5. 判断每个子模块是否已经足够简单（needsFurtherDecomposition）
6. 对于简单的子模块，提供建议性的语句提示（codeHint），用"可以考虑""建议"等引导语气，不给确定性方案，绝对禁止直接给出代码

【输出格式】（严格JSON）：
```json
{{
    "parentProblem": "{parent_problem}",
    "level": {level},
    "subProblems": [
        {{
            "name": "子模块名称",
            "description": "具体要完成的任务",
            "controlType": "sequence|selection|loop",
            "ipo": {{
                "input": "需要什么输入（必须与父模块衔接）",
                "storage": "建议使用什么数据结构/变量来存储（必填！）",
                "process": "如何处理（自然语言）",
                "output": "产生什么输出（必须与父模块衔接）"
            }},
            "needsFurtherDecomposition": true或false,
            "codeHint": "建议性的语句提示（禁止给出代码）"
        }}
    ],
    "overallIPO": {{
        "input": "本层整体输入（应与父模块输入一致）",
        "storage": "本层整体存储结构建议",
        "process": "本层整体处理流程",
        "output": "本层整体输出（应与父模块输出一致）"
    }}
}}
```

【控制结构判断】：
- sequence📋：变量声明、赋值、函数调用等顺序执行
- selection🔀：if-else、switch条件分支
- loop🔄：for、while、do-while循环

【needsFurtherDecomposition 判断标准】：
设为 false（足够简单）的情况：
- 代码行数：≤5 行有效代码即可实现
- 控制结构：只有单一控制结构（纯顺序/单层条件/单层循环）
- 变量数量：涉及 ≤3 个变量
- 简单模块示例：
  * 声明整型变量并初始化
  * 使用格式化输入/输出读取或打印数据
  * 通过条件判断比较两个值的大小关系
  * 使用单层循环遍历数组元素
  * 对栈/队列执行一次基本操作（如入栈、出栈）

设为 true（需要继续分解）的情况：
- 嵌套结构：循环嵌套、条件嵌套、循环+条件嵌套
- 多步骤处理：需要先A再B再C的连续操作
- 复杂数据操作：涉及多个指针、多次遍历
- 算法核心逻辑：排序、查找、递归的核心部分
- 边界处理复杂：需要考虑多种边界情况

【codeHint 要求 - 极其重要】：
- codeHint 必须是建议性的自然语言描述，用"可以考虑"、"建议"等引导性语气
- 不能给出确定性、唯一性的实现方式，要让学生意识到有多种实现选择
- 绝对禁止在 codeHint 中出现任何代码片段、代码关键字、变量名、函数调用
- 正确示例："可以考虑使用循环结构（如for或while）来遍历数组元素，逐个累加求和"
- 正确示例："建议通过条件判断来比较两个数的大小关系，也可以考虑用三元运算的思路"
- 错误示例（禁止）："使用for循环遍历数组"
- 错误示例（禁止）："scanf(\"%d\", &n);"

题目知识点：{', '.join(topics)}
编程语言：{language}

请进行第{level}层分解，确保比上一层更加细化，且与父模块的ISPO信息保持衔接。
再次提醒：每个ipo对象必须包含input、storage、process、output四个字段！"""
            
            # 调用AI模型
            llm = get_llm(session.get('xiaohang_model', 'xhang'))
            full_response = ""
            for content_piece in llm._call(prompt):
                full_response += content_piece
                yield content_piece
            
            # 尝试解析并存储分解结果（用于追踪）
            try:
                import re
                json_match = re.search(r'```json\s*([\s\S]*?)\s*```', full_response)
                if json_match:
                    decomposition_data = json.loads(json_match.group(1))
                    # 存储当前层级的分解结果
                    decomposition_key = f"xiaohang_decomposition:{session_id}:L{level}:{parent_problem[:20]}"
                    redis_client.setex(
                        decomposition_key,
                        3600,
                        json.dumps(decomposition_data, ensure_ascii=False)
                    )
            except Exception as parse_error:
                print(f"解析分解结果失败: {parse_error}")
            
        except Exception as e:
            yield f"错误: {str(e)}"
    
    return Response(stream_with_context(generate_response()), mimetype='text/event-stream')


@xiaohang_enhanced_bp.route('/get_decomposition_history', methods=['GET'])
def get_decomposition_history():
    """获取分解历史"""
    session_id = session.get('xiaohang_session_id')
    if not session_id:
        return jsonify({"error": "会话未初始化"}), 400
    
    redis_client = get_redis_client()
    decomposition_key = f"xiaohang_decomposition:{session_id}"
    decomposition_history = redis_client.get(decomposition_key)
    
    if decomposition_history:
        return jsonify(json.loads(decomposition_history.decode('utf-8')))
    else:
        return jsonify({"message": "暂无分解历史"})


@xiaohang_enhanced_bp.route('/save_framework_leaf_nodes', methods=['POST'])
def save_framework_leaf_nodes():
    """前端在用户完成所有分解后，将最终叶子节点列表发送到后端保存"""
    session_id = session.get('xiaohang_session_id')
    if not session_id:
        return jsonify({"error": "会话未初始化"}), 400
    
    data = request.json
    leaf_nodes = data.get('leafNodes', [])
    
    if not leaf_nodes:
        return jsonify({"error": "叶子节点列表为空"}), 400
    
    redis_client = get_redis_client()
    leaf_key = f"xiaohang_framework_leaves:{session_id}"
    redis_client.setex(leaf_key, 3600, json.dumps(leaf_nodes, ensure_ascii=False))
    
    return jsonify({"message": "叶子节点已保存", "count": len(leaf_nodes)})


@xiaohang_enhanced_bp.route('/regenerate_with_leaf_nodes', methods=['POST'])
def regenerate_with_leaf_nodes():
    """基于最终叶子节点重新生成伪代码和代码补全，确保一一对应"""
    session_id = session.get('xiaohang_session_id')
    if not session_id:
        return jsonify({"error": "会话未初始化"}), 400
    
    data = request.json
    target_module = data.get('module', '')  # '伪代码' 或 '核心语句'
    
    if target_module not in ('伪代码', '核心语句'):
        return jsonify({"error": "无效的模块类型"}), 400
    
    redis_client = get_redis_client()
    
    # 获取叶子节点
    leaf_key = f"xiaohang_framework_leaves:{session_id}"
    leaf_data = redis_client.get(leaf_key)
    if not leaf_data:
        return jsonify({"error": "未找到叶子节点数据，请先完成框架分解"}), 400
    
    leaf_nodes = json.loads(leaf_data.decode('utf-8'))
    leaf_constraint = format_leaf_nodes_for_prompt(leaf_nodes)
    
    # 获取题目和标准答案
    problem_key = f"xiaohang_problem:{session_id}"
    problem_data = redis_client.get(problem_key)
    if not problem_data:
        return jsonify({"error": "未找到当前题目"}), 400
    
    problem_info = json.loads(problem_data.decode('utf-8'))
    current_problem = problem_info['problem']
    standard_answer = problem_info.get('standard_answer', '')
    topics = problem_info['topics']
    language = session.get('xiaohang_language', 'C')
    
    # 获取前置模块输出
    previous_outputs = get_previous_guidance_outputs(session_id, target_module)
    constraint_context = build_constraint_context(previous_outputs, standard_answer, guidance_type=target_module)
    
    def generate_response():
        try:
            llm = get_llm(session.get('xiaohang_model', 'xhang'))
            system_prompts_map = get_system_prompts(language)
            
            if target_module == '伪代码':
                system_prompt = system_prompts_map.get('伪代码', '')
                specific_instruction = f"""
【伪代码模块特殊要求 - 基于最终分解结果】：
基于标准答案的算法逻辑，按代码框架叶子节点划分，为每个模块生成对应的伪代码。
伪代码必须与代码框架的最终分解结果（叶子节点）严格一一对应。
不要在最后添加复杂度分析，只输出伪代码内容。

【输出格式强制要求】：
- 每个叶子节点模块单独输出，先写模块名称标题，再输出该模块的伪代码块（使用```pseudocode标记）
- 伪代码使用 if-then-else-end if、for-do-end for、while-do-end while 等控制结构
- 赋值使用 ← 符号，用 // 添加中文注释
- 禁止使用任何具体编程语言语法（如C的printf/scanf/malloc/#include/花括号/分号，Python的print/def/import等）
- 用自然语言描述功能代替语言特定函数（如"输出结果"代替printf，"读取输入"代替scanf）

【极其重要 - 必须包含可执行逻辑语句】：
每个伪代码块的主体必须是具体的逻辑操作语句（赋值←、条件if-then、循环for-do等），注释//只是辅助说明。
绝对禁止输出只有注释没有逻辑语句的伪代码块。

【极其重要 - 结构一致性】：
伪代码的每个代码块必须与下面列出的代码框架叶子节点一一对应。
每个叶子节点对应一个独立的模块标题+伪代码块。

{leaf_constraint}
"""
            else:  # 核心语句
                system_prompt = system_prompts_map.get('核心语句', '')
                todo_format = '使用 // TODO: 在这里补全代码：xxx 格式' if language == 'C' else '使用 # TODO: 在这里补全代码：xxx 格式'
                specific_instruction = f"""
【代码补全模块特殊要求 - 基于最终分解结果 - 严格执行】：
生成一份带有 TODO 标记的不完整代码。
代码的整体结构必须与代码框架的最终分解结果（叶子节点）严格一一对应。
{todo_format}

【核心规则 - TODO处绝对不能有实现代码】：
1. TODO 注释标记处只能有一行注释说明需要实现什么功能，下面不能跟任何实现代码
2. 正确示例：
   // TODO: 在这里补全代码：实现密钥处理功能，去除重复字母
   （这里什么都没有，留空让学生自己写）
3. 错误示例（绝对禁止）：
   // TODO: 在这里补全代码：实现密钥处理功能
   void process_key() {{  // ← 这就是泄露了完整实现！
       ...实际代码...
   }}
4. 只输出一份代码，不要分开展示完整代码和补全部分

【极其重要 - 结构一致性】：
代码中的每个功能块必须与下面列出的代码框架叶子节点一一对应。
在代码中用注释标明每个部分对应的叶子节点名称。

{leaf_constraint}
"""
            
            prompt = f"""{system_prompt}

【重要约束 - 一致性要求】：
你的输出必须与代码框架的最终分解结果和前置模块保持高度一致。
代码框架已经完成了所有层级的分解，最终的叶子节点就是程序的基本构建块。
你的输出必须与这些叶子节点一一对应。

{specific_instruction}

{constraint_context}

【题目】：
{current_problem}

请开始生成（确保与代码框架叶子节点一一对应，TODO处只有注释没有实现代码）："""
            
            full_response = ""
            for content_piece in llm._call(prompt):
                full_response += content_piece
                yield content_piece
            
            # 保存输出
            save_guidance_output(session_id, target_module, full_response)
            
        except Exception as e:
            yield f"错误: {str(e)}"
    
    return Response(stream_with_context(generate_response()), mimetype='text/event-stream')

@xiaohang_enhanced_bp.route('/get_correct_answer', methods=['POST'])
def get_correct_answer():
    """获取正确答案 - 直接返回缓存的标准答案"""
    session_id = session.get('xiaohang_session_id')
    if not session_id:
        def error_response():
            yield "错误: 会话未初始化，请先选择知识点并生成题目"
        return Response(stream_with_context(error_response()), mimetype='text/event-stream')
    
    # 获取当前题目和标准答案
    redis_client = get_redis_client()
    problem_key = f"xiaohang_problem:{session_id}"
    problem_data = redis_client.get(problem_key)
    
    if not problem_data:
        def error_response():
            yield "错误: 未找到当前题目，请先生成题目"
        return Response(stream_with_context(error_response()), mimetype='text/event-stream')
    
    problem_info = json.loads(problem_data.decode('utf-8'))
    standard_answer = problem_info.get('standard_answer', '')
    current_language = session.get('xiaohang_language', 'C')
    cached_language = problem_info.get('standard_answer_language', 'C')
    
    # 如果语言不匹配，需要重新生成
    if standard_answer and cached_language != current_language:
        standard_answer = ''  # 强制重新生成
    
    def generate_response():
        if standard_answer:
            # 直接返回缓存的标准答案
            yield standard_answer
        else:
            # 兜底：如果没有缓存的答案，重新生成
            current_problem = problem_info['problem']
            topics = problem_info['topics']
            language = session.get('xiaohang_language', 'C')
            lang_desc = 'C语言' if language == 'C' else 'Python'
            lang_code_block = 'c' if language == 'C' else 'python'
            main_func_req = '3. 包含必要的头文件和main函数' if language == 'C' else '3. 包含完整的可运行代码结构'
            
            prompt = f"""你是一名专业的{lang_desc}数据结构与算法专家。请为以下题目提供完整的正确答案代码。

【题目】：
{current_problem}【要求】：
1. 提供完整的、可运行的{lang_desc}代码
2. 代码中必须包含详细、必要的注释，解释关键步骤和逻辑
{main_func_req}
4. 不需要在代码外单独说明算法思路

【输出格式】：
## 标准答案

**完整代码：**
```{lang_code_block}
[完整的{lang_desc}代码，包含详细注释]
```

**复杂度分析：**
- 时间复杂度：[分析]
- 空间复杂度：[分析]

请生成标准答案："""
            
            try:
                llm = get_llm(session.get('xiaohang_model', 'xhang'))
                full_answer = ""
                for content_piece in llm._call(prompt):
                    full_answer += content_piece
                    yield content_piece
                
                # 更新缓存
                problem_info['standard_answer'] = full_answer
                problem_info['standard_answer_language'] = current_language
                redis_client.setex(problem_key, 3600, json.dumps(problem_info))
            except Exception as e:
                yield f"错误: {str(e)}"
    
    return Response(stream_with_context(generate_response()), mimetype='text/event-stream')

@xiaohang_enhanced_bp.route('/follow_up_question', methods=['POST'])
def follow_up_question():
    """新增：追问功能"""
    session_id = session.get('xiaohang_session_id')
    if not session_id:
        def error_response():
            yield "错误: 会话未初始化，请先选择知识点并生成题目"
        return Response(stream_with_context(error_response()), mimetype='text/event-stream')
    
    data = request.json
    guidance_type = data.get('type', '思路')  # 当前所在的模块
    user_question = data.get('question', '')
    
    if not user_question:
        def error_response():
            yield "错误: 请输入问题"
        return Response(stream_with_context(error_response()), mimetype='text/event-stream')
    
    # 获取当前题目
    redis_client = get_redis_client()
    problem_key = f"xiaohang_problem:{session_id}"
    problem_data = redis_client.get(problem_key)
    
    if not problem_data:
        def error_response():
            yield "错误: 未找到当前题目，请先生成题目"
        return Response(stream_with_context(error_response()), mimetype='text/event-stream')
    
    problem_info = json.loads(problem_data.decode('utf-8'))
    current_problem = problem_info['problem']
    
    # 获取该模块的对话历史
    chat_history_key = f"xiaohang_guidance_chat:{session_id}:{guidance_type}"
    history_data = redis_client.lrange(chat_history_key, 0, -1)
    
    def generate_response():
        try:
            # 构建对话历史
            history_text = ""
            if history_data:
                for item in history_data:
                    msg = json.loads(item.decode('utf-8'))
                    history_text += f"\nAI: {msg['content']}\n"
            
            # 构建追问提示词
            module_question_hints = {
                '思路': '围绕题目理解、ISPO分析、输入输出、解题思路等方面提出引导性问题，不要询问是否需要展示其他模块内容',
                '框架': '围绕代码框架结构、函数划分、模块设计等方面提出引导性问题，不要询问是否需要展示其他模块内容',
                '伪代码': '围绕伪代码逻辑、算法步骤、流程控制等方面提出引导性问题，不要询问是否需要展示其他模块内容',
                '核心语句': '围绕关键代码语句、语法细节、代码补全等方面提出引导性问题，不要询问是否需要展示其他模块内容'
            }
            
            module_next_step_hints = {
                '思路': '如果学生表示理解清楚了，可以建议他点击「代码框架」继续学习',
                '框架': '如果学生表示理解清楚了，可以建议他点击「伪代码」继续学习',
                '伪代码': '如果学生表示理解清楚了，可以建议他点击「代码补全」继续练习',
                '核心语句': '如果学生表示理解清楚了，可以建议他在右侧编辑器中编写完整代码并提交测试'
            }
            
            question_hint = module_question_hints.get(guidance_type, '围绕当前模块内容提出引导性问题')
            next_step_hint = module_next_step_hints.get(guidance_type, '')
            
            prompt = f"""你是一名智能AI助教，正在为学生提供【{guidance_type}】阶段的指导。

【题目】：
{current_problem}

【之前的对话历史】：
{history_text}

【学生的追问】：
{user_question}

请根据学生的追问，结合之前的指导内容和当前所在的【{guidance_type}】阶段，给出详细的回答。

要求：
1. 回答要针对学生的具体问题
2. 继续使用问题引导学生思考
3. 不要直接给出完整答案，要引导学生自己思考
4. 严格保持在【{guidance_type}】阶段的指导范围内
5. 回答结束后，{question_hint}
6. {next_step_hint}

请开始回答："""
            
            # 调用AI模型
            llm = get_llm(session.get('xiaohang_model', 'xhang'))
            full_response = ""
            for content_piece in llm._call(prompt):
                full_response += content_piece
                yield content_piece
            
            # 存储用户问题和AI回答到历史
            redis_client.rpush(
                chat_history_key,
                json.dumps({
                    "role": "user",
                    "content": user_question,
                    "timestamp": time.time()
                })
            )
            redis_client.rpush(
                chat_history_key,
                json.dumps({
                    "role": "assistant",
                    "content": full_response,
                    "timestamp": time.time()
                })
            )
            redis_client.expire(chat_history_key, 3600)
            
        except Exception as e:
            yield f"错误: {str(e)}"
    
    return Response(stream_with_context(generate_response()), mimetype='text/event-stream')

@xiaohang_enhanced_bp.route('/knowledge_seeking', methods=['POST'])
def knowledge_seeking():
    """新增：渴求知识功能 - 支持结合智能辅导提问历史进行个性化生成"""
    session_id = session.get('xiaohang_session_id')
    if not session_id:
        def error_response():
            yield "错误: 会话未初始化，请先选择知识点并生成题目"
        return Response(stream_with_context(error_response()), mimetype='text/event-stream')
    
    data = request.json
    user_question = data.get('question', '')  # 用户的追问（可选）
    
    # 获取当前题目和知识点
    redis_client = get_redis_client()
    problem_key = f"xiaohang_problem:{session_id}"
    problem_data = redis_client.get(problem_key)
    
    if not problem_data:
        def error_response():
            yield "错误: 未找到当前题目，请先生成题目"
        return Response(stream_with_context(error_response()), mimetype='text/event-stream')
    
    problem_info = json.loads(problem_data.decode('utf-8'))
    current_problem = problem_info['problem']
    topics = problem_info['topics']
    
    # 获取学生的提问历史（用于个性化生成）
    def get_student_question_history():
        """收集学生的提问历史，包括智能辅导和小航辅导的对话"""
        question_history = []
        
        # 1. 获取智能辅导的对话历史
        user_id = session.get('user_id', 'default_user')
        tutor_session_id = session.get('session_id')  # 智能辅导的session_id
        if tutor_session_id:
            tutor_history_key = f"chat_history:{user_id}:{tutor_session_id}"
            tutor_history = redis_client.lrange(tutor_history_key, 0, -1)
            if tutor_history:
                for item in tutor_history:
                    try:
                        msg = json.loads(item.decode('utf-8') if isinstance(item, bytes) else item)
                        if msg.get('role') == 'user':  # 只收集学生的提问
                            question_history.append({
                                'source': '智能辅导',
                                'content': msg.get('content', ''),
                                'type': msg.get('type', 'question')
                            })
                    except:
                        continue
        
        # 2. 获取小航辅导的指导对话历史（4个阶段）
        guidance_types = ['思路', '框架', '伪代码', '核心语句']
        for guidance_type in guidance_types:
            guidance_history_key = f"xiaohang_guidance_chat:{session_id}:{guidance_type}"
            guidance_history = redis_client.lrange(guidance_history_key, 0, -1)
            if guidance_history:
                for item in guidance_history:
                    try:
                        msg = json.loads(item.decode('utf-8') if isinstance(item, bytes) else item)
                        if msg.get('role') == 'user':  # 只收集学生的提问
                            question_history.append({
                                'source': f'小航辅导-{guidance_type}',
                                'content': msg.get('content', ''),
                                'type': 'question'
                            })
                    except:
                        continue
        
        return question_history
    
    # 分析提问历史，提取关键信息
    def analyze_question_history(question_history):
        """分析提问历史，提取学生的困惑点、薄弱环节等"""
        if not question_history:
            return ""
        
        # 提取所有学生提问
        student_questions = [q['content'] for q in question_history if q.get('content')]
        
        if not student_questions:
            return ""
        
        # 构建提问历史摘要
        questions_text = "\n".join([f"- {q}" for q in student_questions[-10:]])  # 只取最近10条
        
        return f"""
【学生在学习过程中的提问历史】：
{questions_text}

请特别关注学生在这些提问中表现出的困惑点、薄弱环节和需要重点加强的知识点。"""
    
    def generate_response():
        try:
            # 获取学生的提问历史
            question_history = get_student_question_history()
            history_analysis = analyze_question_history(question_history)
            
            # 构建渴求知识提示词
            language = session.get('xiaohang_language', 'C')
            lang_desc = 'C语言' if language == 'C' else 'Python'
            if user_question:
                prompt = f"""你是一名资深的{lang_desc}数据结构与算法教学专家。学生正在学习以下知识点并提出了问题。

【当前题目涉及的知识点】：
{', '.join(topics)}

【题目】：
{current_problem}

【学生的问题】：
{user_question}
{history_analysis}

请根据学生的问题、题目涉及的知识点，以及学生在学习过程中的提问历史，生成一个个性化的学习思路和详细解答。

【重要要求】：
1. 结合学生在智能辅导和小航辅导中的提问历史，识别学生的困惑点和薄弱环节
2. 针对学生经常提问的知识点，提供更详细的解释和更多练习建议
3. 根据学生的提问模式，判断学生的学习风格和接受能力，调整学习路径的难度和深度
4. 如果学生多次提问同一类问题，说明这是学生的薄弱点，需要重点加强

【输出格式】：
## 📚 知识点分析

**涉及的核心知识点：**
{', '.join(topics)}

**知识点详解：**
[详细解释每个知识点的概念、特点、应用场景，特别针对学生在提问历史中表现出的困惑点进行深入讲解]

## 🎯 针对你的问题

**问题分析：**
[分析学生的问题，结合提问历史中的相关困惑点]

**详细解答：**
[给出详细的解答，特别关注学生之前提问中暴露的理解盲区]

## 📖 个性化学习路径

**基于你的提问历史，我为你定制了以下学习路径：**

1. **基础概念理解**（重点关注你在提问中暴露的薄弱点）
   [针对性的学习内容，特别强调学生提问中涉及的概念]

2. **算法原理掌握**（结合你的理解难点）
   [根据学生的提问模式，调整讲解深度和方式]

3. **代码实现练习**（针对你的困惑点）
   [提供针对性的练习，帮助学生克服提问中表现出的困难]

4. **进阶优化思考**（基于你的学习进度）
   [根据学生的掌握情况，提供合适的进阶建议]

## 💡 特别提醒

[根据学生的提问历史，给出针对性的学习建议，指出需要重点加强的知识点]

请开始生成学习思路："""
            else:
                prompt = f"""你是一名资深的{lang_desc}数据结构与算法教学专家。请为学生生成一个系统的、个性化的学习思路。

【当前题目涉及的知识点】：
{', '.join(topics)}

【题目】：
{current_problem}
{history_analysis}

请根据题目涉及的知识点，以及学生在学习过程中的提问历史，生成一个个性化的学习思路和知识体系。

【重要要求】：
1. 仔细分析学生在智能辅导和小航辅导中的提问历史
2. 识别学生最常提问的知识点，这些通常是学生的薄弱环节
3. 根据学生的提问频率和类型，判断学生的学习难点和接受能力
4. 针对学生的提问模式，定制个性化的学习路径，重点加强薄弱环节
5. 如果学生提问较少，说明可能理解较好，可以提供更深入的内容；如果提问较多，说明需要更多基础练习

【输出格式】：
## 📚 知识点体系

**核心知识点：**
{', '.join(topics)}

**知识点详解：**
[详细解释每个知识点的概念、特点、应用场景、常见问题。特别针对学生在提问历史中表现出的困惑点进行深入讲解]

## 🎯 个性化学习思路

**基于你的学习情况，我为你定制了以下学习思路：**

**1. 理论基础**（重点关注你的薄弱点）
[根据学生的提问历史，识别需要重点加强的理论知识，提供针对性的讲解]

**2. 算法原理**（结合你的理解难点）
[根据学生的提问模式，调整算法原理的讲解深度，特别关注学生提问中涉及的部分]

**3. 实现技巧**（针对你的困惑点）
[提供针对性的实现技巧，帮助学生解决提问中表现出的编程困难]

**4. 常见陷阱**（基于你的提问历史）
[重点讲解学生在提问中暴露的容易出错的地方]

## 📖 个性化学习路径

**根据你的提问历史，我为你定制了以下学习路径：**

**阶段一：基础理解**（重点关注你的薄弱环节）
- [针对学生提问中暴露的基础概念薄弱点，提供强化学习内容]
- [根据学生的理解能力，调整学习难度]

**阶段二：算法掌握**（结合你的困惑点）
- [针对学生提问中涉及的算法难点，提供深入讲解]
- [根据学生的接受能力，提供合适的练习]

**阶段三：实战练习**（针对你的薄弱点）
- [提供针对性的练习，帮助学生克服提问中表现出的困难]
- [特别加强学生在提问中暴露的知识点]

**阶段四：进阶提升**（基于你的学习进度）
- [根据学生的掌握情况，提供合适的进阶方向]
- [如果学生提问较少，可以提供更深入的内容]

## 💡 个性化学习建议

[根据学生的提问历史，给出针对性的学习建议：
- 指出需要重点加强的知识点（基于提问频率）
- 分析学生的学习风格和接受能力
- 提供适合的学习方法和节奏
- 特别关注学生在提问中表现出的困惑点]

请开始生成学习思路："""
            
            # 调用AI模型
            llm = get_llm(session.get('xiaohang_model', 'xhang'))
            for content_piece in llm._call(prompt):
                yield content_piece
            
        except Exception as e:
            yield f"错误: {str(e)}"
    
    return Response(stream_with_context(generate_response()), mimetype='text/event-stream')

@xiaohang_enhanced_bp.route('/change_difficulty', methods=['POST'])
def change_difficulty():
    """切换难度"""
    session_id = session.get('xiaohang_session_id')
    if not session_id:
        return jsonify({"error": "会话未初始化"}), 400
    
    data = request.json
    new_difficulty = data.get('difficulty', '简单')
    
    # 验证难度值
    if new_difficulty not in ['简单', '中等', '困难']:
        return jsonify({"error": "无效的难度值"}), 400
    
    # 更新难度
    session['xiaohang_difficulty'] = new_difficulty
    
    return jsonify({
        "message": f"难度已切换到{new_difficulty}",
        "difficulty": new_difficulty
    })

@xiaohang_enhanced_bp.route('/change_model', methods=['POST'])
def change_model():
    """切换大模型"""
    session_id = session.get('xiaohang_session_id')
    if not session_id:
        return jsonify({"error": "会话未初始化"}), 400
    
    data = request.json
    new_model = data.get('model', 'xhang')
    
    if new_model not in ['xhang', 'loopcoder', 'normal', 'test_model']:
        return jsonify({"error": "无效的模型"}), 400
    
    session['xiaohang_model'] = new_model
    
    return jsonify({
        "message": f"模型已切换到{new_model}",
        "model": new_model
    })

@xiaohang_enhanced_bp.route('/reset_session', methods=['POST'])
def reset_session():
    """重置会话"""
    session_id = session.get('xiaohang_session_id')
    if session_id:
        redis_client = get_redis_client()
        # 清理所有相关的Redis数据
        problem_key = f"xiaohang_problem:{session_id}"
        redis_client.delete(problem_key)
        
        # 清理所有对话历史
        for guidance_type in ['思路', '框架', '伪代码', '核心语句']:
            chat_key = f"xiaohang_guidance_chat:{session_id}:{guidance_type}"
            redis_client.delete(chat_key)
        
        # 清理所有模块输出（上下文传递链数据）
        clear_all_guidance_outputs(session_id)
        
        # 清理分解历史
        decomposition_key = f"xiaohang_decomposition:{session_id}"
        redis_client.delete(decomposition_key)
    
    # 清理session
    session.pop('xiaohang_session_id', None)
    session.pop('xiaohang_topics', None)
    session.pop('xiaohang_difficulty', None)
    session.pop('xiaohang_correct_count', None)
    
    return jsonify({"message": "会话已重置"})


@xiaohang_enhanced_bp.route('/get_session_status', methods=['GET'])
def get_session_status():
    """获取当前会话状态，包括题目信息"""
    session_id = session.get('xiaohang_session_id')
    if not session_id:
        return jsonify({"error": "会话未初始化", "session_id": None}), 200
    
    redis_client = get_redis_client()
    
    # 获取题目信息
    problem_key = f"xiaohang_problem:{session_id}"
    problem_data = redis_client.get(problem_key)
    
    result = {
        "session_id": session_id,
        "topics": session.get('xiaohang_topics', []),
        "difficulty": session.get('xiaohang_difficulty', '简单'),
        "problem": None,
        "has_standard_answer": False
    }
    
    if problem_data:
        problem_info = json.loads(problem_data.decode('utf-8'))
        result["problem"] = problem_info.get('problem', '')
        result["has_standard_answer"] = bool(problem_info.get('standard_answer'))
    
    return jsonify(result)


@xiaohang_enhanced_bp.route('/get_guidance_status', methods=['GET'])
def get_guidance_status():
    """获取各模块的生成状态，用于前端显示进度和依赖关系"""
    session_id = session.get('xiaohang_session_id')
    if not session_id:
        return jsonify({"error": "会话未初始化"}), 400
    
    redis_client = get_redis_client()
    
    # 检查各模块是否已生成
    status = {}
    for guidance_type in ['思路', '框架', '伪代码', '核心语句']:
        key = f"xiaohang_guidance_output:{session_id}:{guidance_type}"
        data = redis_client.get(key)
        status[guidance_type] = {
            "generated": data is not None,
            "dependencies": GUIDANCE_DEPENDENCIES.get(guidance_type, []),
            "can_generate": True  # 默认可以生成
        }
    
    # 检查是否有标准答案
    problem_key = f"xiaohang_problem:{session_id}"
    problem_data = redis_client.get(problem_key)
    has_standard_answer = False
    if problem_data:
        problem_info = json.loads(problem_data.decode('utf-8'))
        has_standard_answer = bool(problem_info.get('standard_answer'))
    
    status['has_standard_answer'] = has_standard_answer
    status['dependencies_map'] = GUIDANCE_DEPENDENCIES
    
    return jsonify(status)


@xiaohang_enhanced_bp.route('/get_pregenerated', methods=['POST'])
def get_pregenerated():
    """获取已预生成的模块内容（框架、伪代码、核心语句）"""
    session_id = session.get('xiaohang_session_id')
    if not session_id:
        def error_response():
            yield "错误: 会话未初始化"
        return Response(stream_with_context(error_response()), mimetype='text/event-stream')
    
    data = request.json
    guidance_type = data.get('type', '')
    
    redis_client = get_redis_client()
    key = f"xiaohang_guidance_output:{session_id}:{guidance_type}"
    cached = redis_client.get(key)
    
    if cached:
        def return_cached():
            yield cached.decode('utf-8')
        return Response(stream_with_context(return_cached()), mimetype='text/event-stream')
    else:
        def not_ready():
            yield "错误: 该模块尚未生成完成，请稍候"
        return Response(stream_with_context(not_ready()), mimetype='text/event-stream')


# ==================== 脚手架理论新增功能 ====================

@xiaohang_enhanced_bp.route('/generate_counterexample', methods=['POST'])
def generate_counterexample():
    """反例生成器 - 构造随机反例帮助学生发现问题"""
    session_id = session.get('xiaohang_session_id')
    if not session_id:
        def error_response():
            yield "错误: 会话未初始化，请先选择知识点并生成题目"
        return Response(stream_with_context(error_response()), mimetype='text/event-stream')
    
    data = request.json
    user_code = data.get('code', '')
    
    # 获取当前题目和诊断结果
    redis_client = get_redis_client()
    problem_key = f"xiaohang_problem:{session_id}"
    problem_data = redis_client.get(problem_key)
    
    if not problem_data:
        def error_response():
            yield "错误: 未找到当前题目，请先生成题目"
        return Response(stream_with_context(error_response()), mimetype='text/event-stream')
    
    problem_info = json.loads(problem_data.decode('utf-8'))
    current_problem = problem_info['problem']
    standard_answer = problem_info.get('standard_answer', '')
    topics = problem_info.get('topics', [])
    
    # 获取之前的诊断结果
    diagnosis_key = f"xiaohang_diagnosis:{session_id}"
    diagnosis_data = redis_client.get(diagnosis_key)
    previous_diagnosis = ""
    if diagnosis_data:
        diag_info = json.loads(diagnosis_data.decode('utf-8'))
        previous_diagnosis = diag_info.get('diagnosis', '')
    
    def generate_response():
        try:
            language = session.get('xiaohang_language', 'C')
            lang_code_block = 'c' if language == 'C' else 'python'
            prompt = f"""**Role:** 你是一名专业的反例生成专家，专门帮助学生通过"让代码崩溃的输入"来发现问题。

**核心理念：**
最好的老师往往是一个"让代码崩溃的输入"。
你的任务是构造一个**随机反例 (Random Counter-example)**，让学生能够清楚地看到自己代码的问题。

【题目】：
{current_problem}

【知识点】：{', '.join(topics)}

【学生代码】：
```{lang_code_block}
{user_code}
```

【标准答案（内部参考）】：
{standard_answer if standard_answer else '暂无'}

【之前的诊断结果】：
{previous_diagnosis if previous_diagnosis else '暂无诊断'}

**Task:**
请按照以下步骤生成反例：

## 🎯 反例生成

### 1. 问题定位
首先，简要说明你发现的代码问题（1-2句话）。

### 2. 随机反例
构造一个**随机**的输入，能够暴露代码的问题：

**测试输入：**
```
[具体的输入数据]
```

**预期输出：**
```
[正确的输出结果]
```

**实际输出（学生代码）：**
```
[学生代码会产生的错误输出]
```

请生成反例："""
            
            llm = get_llm(session.get('xiaohang_model', 'xhang'))
            for content_piece in llm._call(prompt):
                yield content_piece
                
        except Exception as e:
            yield f"错误: {str(e)}"
    
    return Response(stream_with_context(generate_response()), mimetype='text/event-stream')


@xiaohang_enhanced_bp.route('/analyze_complexity', methods=['POST'])
def analyze_complexity():
    """复杂度分析卫士 - 静态分析代码复杂度并给出优化建议"""
    session_id = session.get('xiaohang_session_id')
    if not session_id:
        def error_response():
            yield "错误: 会话未初始化，请先选择知识点并生成题目"
        return Response(stream_with_context(error_response()), mimetype='text/event-stream')
    
    data = request.json
    user_code = data.get('code', '')
    
    # 获取当前题目
    redis_client = get_redis_client()
    problem_key = f"xiaohang_problem:{session_id}"
    problem_data = redis_client.get(problem_key)
    
    if not problem_data:
        def error_response():
            yield "错误: 未找到当前题目，请先生成题目"
        return Response(stream_with_context(error_response()), mimetype='text/event-stream')
    
    problem_info = json.loads(problem_data.decode('utf-8'))
    current_problem = problem_info['problem']
    topics = problem_info.get('topics', [])
    
    def generate_response():
        try:
            language = session.get('xiaohang_language', 'C')
            lang_code_block = 'c' if language == 'C' else 'python'
            prompt = f"""**Role:** 你是一名复杂度分析专家，专门帮助学生理解算法复杂度。

**核心理念：**
DSA课程非常看重复杂度。你需要：
1. 静态分析代码的循环嵌套层级和递归深度
2. 精确推导时间复杂度和空间复杂度
3. 对比题目数据规模判断是否满足要求

【题目】：
{current_problem}

【知识点】：{', '.join(topics)}

【学生代码】：
```{lang_code_block}
{user_code}
```

**Task:**
请严格按照以下格式进行复杂度分析，只输出以下4个部分，不要添加任何额外的优化建议、引导性问题或总结：

## ⏱️ 复杂度分析报告

### 1. 代码结构分析

**循环嵌套层级：** [详细分析代码中每一层循环的结构、作用和执行范围]

**递归深度：** [如果有递归，分析递归深度和终止条件；如果没有递归，说明"代码中没有递归调用"]

**关键操作：** [识别代码中的关键操作，如核心数据结构操作、I/O操作等]

### 2. 时间复杂度

**当前复杂度：** $O(?)$

**分析过程：**
[逐层详细推导，包括：
- 外层循环执行次数及其作用
- 内层循环执行次数（如果有）
- 递归调用次数（如果有）
- 每个关键操作的单次时间复杂度和总执行次数
- 最终综合得出总时间复杂度]

### 3. 空间复杂度

**当前复杂度：** $O(?)$

**分析过程：**
[详细分析额外空间使用，包括：
- **变量空间：** 基本变量占用的空间
- **数组/数据结构空间：** 动态分配或静态数组的空间
- **递归栈空间：** 递归调用栈的空间（如果有）]

### 4. 题目要求对比

**题目数据规模：** [从题目中提取所有数据范围约束]

**是否满足要求：** [是/否，并简要说明原因]

【重要约束】：
- 只输出以上4个部分，到"4. 题目要求对比"结束后立即停止
- 不要输出任何优化建议、引导性问题、复杂度对比表或总结性文字
- 分析过程要详细、严谨，每一步推导都要有理有据

请开始分析："""
            
            llm = get_llm(session.get('xiaohang_model', 'xhang'))
            for content_piece in llm._call(prompt):
                yield content_piece
                
        except Exception as e:
            yield f"错误: {str(e)}"
    
    return Response(stream_with_context(generate_response()), mimetype='text/event-stream')


@xiaohang_enhanced_bp.route('/get_hint', methods=['POST'])
def get_hint():
    """分层提示系统 - 根据学生需求提供不同级别的提示"""
    session_id = session.get('xiaohang_session_id')
    if not session_id:
        def error_response():
            yield "错误: 会话未初始化，请先选择知识点并生成题目"
        return Response(stream_with_context(error_response()), mimetype='text/event-stream')
    
    data = request.json
    hint_level = data.get('level', 1)  # 1-轻微提示, 2-反例提示, 3-概念回溯
    user_code = data.get('code', '')
    specific_question = data.get('question', '')  # 学生的具体问题
    
    # 获取当前题目和诊断结果
    redis_client = get_redis_client()
    problem_key = f"xiaohang_problem:{session_id}"
    problem_data = redis_client.get(problem_key)
    
    if not problem_data:
        def error_response():
            yield "错误: 未找到当前题目，请先生成题目"
        return Response(stream_with_context(error_response()), mimetype='text/event-stream')
    
    problem_info = json.loads(problem_data.decode('utf-8'))
    current_problem = problem_info['problem']
    standard_answer = problem_info.get('standard_answer', '')
    topics = problem_info.get('topics', [])
    
    # 获取之前的诊断结果
    diagnosis_key = f"xiaohang_diagnosis:{session_id}"
    diagnosis_data = redis_client.get(diagnosis_key)
    previous_diagnosis = ""
    if diagnosis_data:
        diag_info = json.loads(diagnosis_data.decode('utf-8'))
        previous_diagnosis = diag_info.get('diagnosis', '')
    
    # 获取提示历史
    hint_history_key = f"xiaohang_hint_history:{session_id}"
    hint_history = redis_client.lrange(hint_history_key, 0, -1)
    hint_history_text = ""
    if hint_history:
        hint_history_text = "\n【之前的提示历史】：\n"
        for h in hint_history:
            hint_history_text += json.loads(h.decode('utf-8')).get('content', '') + "\n---\n"
    
    def generate_response():
        try:
            language = session.get('xiaohang_language', 'C')
            lang_code_block = 'c' if language == 'C' else 'python'
            level_descriptions = {
                1: """**Level 1 - 代码诊断**
你需要从以下四个维度对学生代码进行全面诊断，找出所有存在的问题，并用提问的方式引导学生自己发现错误。

**划分原则：按"错误在什么阶段被发现"进行分类。**
- 编译阶段报错 → 语法错误
- 编译通过但运行时崩溃/异常终止 → 运行时错误
- 程序正常运行不崩溃但输出结果不正确 → 逻辑错误
- 代码写法合法但含义与程序员意图不符（逻辑错误的深层根因） → 语义错误

**诊断维度：**

**1. 语法错误 (Syntax Error)：**
判定标准：编译器/解释器在编译（解析）阶段直接报错，程序根本无法生成可执行文件或无法开始运行。
典型特征：违反了语言的语法规则，编译器会给出明确的错误信息和行号。
检查要点：
- 括号/花括号/方括号不匹配：如 `if (x > 0 {` 缺少右圆括号
- 缺少必要的分号（C）或冒号（Python）：如 `int a = 5` 末尾缺少分号
- 关键字拼写错误：如 `retrun 0;`、`whlie(1)`
- 字符串/字符引号不闭合：如 `printf("hello);`
- 非法的变量声明：如 C语言中 `int 2var = 5;`（变量名以数字开头）
- 缩进错误（Python）：如 `def foo():\nprint("hi")` 缺少缩进
- 非法的表达式结构：如 `for(;;` 缺少右括号
- 类型声明语法错误：如 `int[] a;`（C语言中应为 `int a[];`）

**注意：以下情况不属于语法错误（因为编译器不会报错）：**
- `scanf("%d", T)` 缺少 `&` → 编译可通过（可能有警告），属于语义错误
- `if (a = 1)` 用赋值代替比较 → C语言中语法合法，属于语义错误
- `for(i=0; i<=n; i++)` 多循环一次 → 语法合法，属于逻辑错误

**2. 运行时错误 (Runtime Error)：**
判定标准：代码能通过编译，但在运行过程中程序崩溃、异常终止或产生未定义行为，操作系统或运行时环境会报错（如段错误、浮点异常等）。
典型特征：程序在某些输入下直接崩溃退出，而非输出错误结果。
检查要点：
- 空指针/野指针解引用：如 `int *p = NULL; *p = 5;` 导致段错误(Segmentation Fault)
- 数组越界访问：如 `int a[5]; a[10] = 1;` 访问非法内存
- 除以零：如 `int result = x / 0;` 导致浮点异常(Floating Point Exception)
- 栈溢出：如无终止条件的递归 `void f() { f(); }` 导致 Stack Overflow
- 内存分配失败后未检查：如 `malloc` 返回 NULL 后直接使用
- 释放后使用(Use After Free)：如 `free(p); *p = 1;`
- 双重释放(Double Free)：如对同一指针调用两次 `free`
- 格式化字符串与参数不匹配导致崩溃：如 `printf("%s", 123);`（将整数当字符串指针）

**注意：以下情况不属于运行时错误：**
- 程序没有崩溃但输出了错误结果 → 属于逻辑错误
- `scanf("%d", T)` 缺少 `&` → 虽然可能导致崩溃，但根因是语义错误（误解了scanf的参数要求），应归为语义错误

**3. 逻辑错误 (Logic Error)：**
判定标准：代码能编译、能运行、不崩溃，但程序的输出结果与题目要求不一致。程序"做了错误的事情"但自己不知道。
典型特征：程序正常退出，但答案不对；编译器和运行时都不会报任何错误。
检查要点：
- 循环边界错误(Off-by-one)：如 `for(i=0; i<=n; i++)` 多循环了一次，应为 `i<n`
- 条件判断写反：如该用 `>` 写成了 `<`，或 `&&` 写成了 `||`
- 变量初始化位置不对：如累加器 `sum=0` 放在循环内部导致每次重置
- 累加器/计数器未正确更新：如忘记 `count++` 或放错了位置
- 过早返回：如在循环内 `return` 导致只检查了第一个元素
- 算法思路与题目要求不匹配：如题目要求逆序输出但代码正序输出
- 边界条件遗漏：如未处理空输入、单元素、最大值等特殊情况
- 状态更新顺序错误：如先修改了 capacity 再 realloc，失败时状态不一致
- 重复操作：如函数内部已打印了结果，调用处又打印一次

**注意：逻辑错误关注的是"结果不对"，而非"写法不对"。如果一个错误既导致结果不对，又涉及对语言特性的误解，应同时在逻辑错误和语义错误中指出。**

**4. 语义错误 (Semantic Error)：**
判定标准：代码语法合法、能编译通过，但代码实际表达的含义与程序员的意图不一致。程序员以为代码做的是A，实际做的是B。这类错误往往是逻辑错误的深层根因。
典型特征：代码"看起来对"但"意思不对"，通常源于对语言特性、运算符、API的误解。
检查要点：
- 赋值与比较混淆：如 `if (a = 1)` 本意是比较，实际是赋值（C语言中合法但含义完全不同）
- 取地址符遗漏：如 `scanf("%d", T)` 本意是读入T的值，实际传递的是T的值而非地址
- 运算符优先级误解：如 `a & b == c` 本意是 `(a & b) == c`，实际是 `a & (b == c)`
- 变量作用域误解：如以为修改了全局变量，实际修改的是同名局部变量
- 返回值含义误用：如用 `-1` 表示"栈为空"，但 `-1` 也可能是栈中的有效元素值
- 浅拷贝与深拷贝混淆：如 `b = a` 以为复制了数组，实际只复制了指针
- 类型隐式转换误解：如 `int a = 3/2;` 以为结果是1.5，实际是1（整数除法）
- 指针与数组混淆：如 `sizeof(ptr)` 以为得到数组长度，实际得到指针大小
- 字符串操作误解：如 `strcmp` 返回0表示相等，但学生以为返回0表示不等

**语义错误与逻辑错误的区别：**
- 逻辑错误：算法步骤/流程设计有误（"做错了事"）
- 语义错误：对语言特性理解有误导致写出的代码含义与意图不符（"说错了话"）
- 一个问题可能同时涉及两者：语义错误是根因，逻辑错误是表现。此时两个维度都应指出。

**输出要求：**
- 对每个维度，如果存在问题则指出，如果没有问题则标记为"✅ 未发现问题"
- 对于发现的问题，不要直接给出修正代码，而是用提问的方式引导学生思考
- 指出问题时，必须明确说明是第几行（或第几行到第几行）有问题，或者哪个函数有问题
- 分类时严格遵循上述判定标准，不要把能编译通过的问题归为语法错误
- 如果一个问题涉及多个维度（如语义错误导致了逻辑错误），在各相关维度中分别说明，并注明关联关系
- 最后给出1-2个引导性提问帮助学生改进（格式为"提问 1：..."、"提问 2：..."，禁止使用"苏格拉底式提问"这个词）

**【极其重要 - 必须遵守】在诊断报告的最末尾，你必须额外输出一个JSON错误定位块，用于前端在代码编辑器中高亮标记错误行。格式严格如下：**

```diagnosis-markers
[
  {"type": "syntax", "startLine": 行号, "endLine": 行号, "message": "错误描述"},
  {"type": "runtime", "startLine": 行号, "endLine": 行号, "message": "错误描述"},
  {"type": "logic", "startLine": 起始行号, "endLine": 结束行号, "message": "错误描述"},
  {"type": "semantic", "startLine": 行号, "endLine": 行号, "message": "错误描述"}
]
```

JSON规则：
- type 只能是: syntax, runtime, logic, semantic 四种之一
- startLine 和 endLine 是学生代码中的行号（从1开始计数）
- 如果错误只涉及一行，startLine 和 endLine 相同
- 如果错误涉及一个范围（如整个函数），startLine 是起始行，endLine 是结束行
- 如果某个维度没有错误，不需要在JSON中包含该类型的条目
- 如果所有维度都没有错误，输出空数组 `[]`
- 同一行代码如果涉及多个维度的错误，应在JSON中生成多条记录（type不同）
- 这个JSON块必须是你输出的最后一部分内容，放在思考问题之后
- 不要省略这个JSON块！即使没有错误也要输出 `[]`
""",
                2: """**Level 2 - 反例提示**
你需要构造一个具体的反例，让学生看到问题。
例如：
- "如果输入是空数组 []，你的代码会发生什么？"
- "试着输入 'A man, a plan'，看看你的程序输出了什么？这符合预期吗？"
- "当 n=1 时，你的循环会执行几次？"
""",
                3: """**Level 3 - 代码优化**
学生的代码已经通过了代码诊断（无语法错误、运行时错误、逻辑错误、语义错误），现在需要从优化角度给出建议。

**你需要做两件事：**

**第一：基于用户当前方法的优化**
- 分析用户当前代码的时间复杂度和空间复杂度
- 指出可以优化的具体位置（如：减少不必要的遍历、优化数据结构使用、减少内存分配等）
- 给出优化后的时间/空间复杂度对比
- 可以给出优化后的代码片段（因为代码本身已经正确，优化建议可以包含代码）

**第二：其他更优方法（如果存在）**
- 如果存在比用户当前方法更优的算法或思路，简要阐述该方法
- 在前面明确说明：该方法与用户方法的核心区别是什么（如算法思想不同、数据结构不同等）
- 给出该方法的时间/空间复杂度
- 给出该方法的代码实现

**注意：**
- 如果用户的方法已经是最优解，明确告知"你的方法已经是该问题的最优解"
- 优化建议要具体、可操作，不要泛泛而谈
"""
            }
            
            level_desc = level_descriptions.get(hint_level, level_descriptions[1])
            question_section = f"\n【学生的具体问题】：\n{specific_question}\n" if specific_question else ""
            
            # 构建输出模板
            if hint_level == 1:
                output_template = """## 🔬 代码诊断报告

### 1️⃣ 语法错误 (Syntax Error)
> 判定依据：编译阶段直接报错，程序无法生成可执行文件

[检查结果：列出发现的语法错误并标注行号，说明为什么编译器会报错，或标记 ✅ 未发现问题]

### 2️⃣ 运行时错误 (Runtime Error)
> 判定依据：编译通过，但运行时程序崩溃或异常终止

[检查结果：列出可能的运行时错误并标注行号/行范围，说明在什么输入/条件下会崩溃，或标记 ✅ 未发现问题]

### 3️⃣ 逻辑错误 (Logic Error)
> 判定依据：程序正常运行不崩溃，但输出结果与题目要求不一致

[检查结果：列出发现的逻辑错误并标注行号/行范围/函数名，说明会导致什么样的错误结果，或标记 ✅ 未发现问题]

### 4️⃣ 语义错误 (Semantic Error)
> 判定依据：代码写法合法，但实际含义与程序员意图不符

[检查结果：列出发现的语义错误并标注行号，说明代码实际做了什么vs程序员可能想做什么，或标记 ✅ 未发现问题]

## 🤔 思考问题
[针对发现的问题，提出1-2个引导性提问（格式为"提问 1：..."、"提问 2：..."），帮助学生自己发现并修正错误]

```diagnosis-markers
[{"type": "错误类型", "startLine": 行号, "endLine": 行号, "message": "简短错误描述"}, ...]
```"""
            elif hint_level == 3:
                output_template = """## 🚀 代码优化报告

### 📊 当前代码复杂度
- **时间复杂度：** [分析结果]
- **空间复杂度：** [分析结果]

### ✨ 基于当前方法的优化
[指出具体可优化的位置，给出优化方案和优化后的复杂度对比]

### 🔄 其他更优方法（如果存在）
[简要阐述与用户方法的核心区别，给出该方法的复杂度和实现]
（如果用户方法已是最优解，明确告知）"""
            else:
                output_template = f"""## 💡 Level {hint_level} 提示

[根据级别要求给出提示内容]

## 🤔 思考问题
[提出1-2个引导性问题]"""

            prompt = f"""**Role:** 你是数据结构与算法课程的资深助教，采用脚手架理论进行分层提示。

**核心原则：**
- 使用提问的方式引导思考（输出格式为"提问 1：..."、"提问 2：..."，不要使用"苏格拉底式提问"这个词）
- 根据提示级别控制信息量
{'- 代码优化模式：学生代码已通过诊断无错误，可以给出优化后的代码' if hint_level == 3 else '- 拒绝直接喂饭：严禁直接给出正确代码'}

{level_desc}

【题目】：
{current_problem}

【知识点】：{', '.join(topics)}

【学生代码】：
```{lang_code_block}
{user_code}
```

【标准答案（内部参考，绝对不要展示）】：
{standard_answer if standard_answer else '暂无'}

【之前的诊断结果】：
{previous_diagnosis if previous_diagnosis else '暂无'}
{hint_history_text}
{question_section}

**Task:**
请根据 Level {hint_level} 的要求，给出恰当的提示。
{"**【提醒】你必须在输出的最末尾包含 ```diagnosis-markers JSON块，这是前端渲染编辑器高亮所必需的。即使没有错误也要输出空数组[]。不要遗漏！**" if hint_level == 1 else ""}

{output_template}

请开始："""
            
            llm = get_llm(session.get('xiaohang_model', 'xhang'))
            full_response = ""
            for content_piece in llm._call(prompt):
                full_response += content_piece
                yield content_piece
            
            # 保存提示历史
            redis_client.rpush(
                hint_history_key,
                json.dumps({
                    "level": hint_level,
                    "content": full_response,
                    "timestamp": time.time()
                })
            )
            redis_client.expire(hint_history_key, 3600)
                
        except Exception as e:
            yield f"错误: {str(e)}"
    
    return Response(stream_with_context(generate_response()), mimetype='text/event-stream')


@xiaohang_enhanced_bp.route('/code_review', methods=['POST'])
def code_review():
    """代码行级评论 - 类似Code Review，在有问题的代码行旁边标记"""
    session_id = session.get('xiaohang_session_id')
    if not session_id:
        return jsonify({"error": "会话未初始化"}), 400
    
    data = request.json
    user_code = data.get('code', '')
    
    # 获取当前题目
    redis_client = get_redis_client()
    problem_key = f"xiaohang_problem:{session_id}"
    problem_data = redis_client.get(problem_key)
    
    if not problem_data:
        return jsonify({"error": "未找到当前题目"}), 400
    
    problem_info = json.loads(problem_data.decode('utf-8'))
    current_problem = problem_info['problem']
    standard_answer = problem_info.get('standard_answer', '')
    topics = problem_info.get('topics', [])
    
    def generate_response():
        try:
            language = session.get('xiaohang_language', 'C')
            lang_code_block = 'c' if language == 'C' else 'python'
            prompt = f"""**Role:** 你是一名代码审查专家，需要对学生代码进行行级评审。

**任务：**
分析学生代码，找出有问题的代码行，并给出简短的评论。
输出格式必须是JSON，便于前端渲染。

【题目】：
{current_problem}

【知识点】：{', '.join(topics)}

【学生代码】：
```{lang_code_block}
{user_code}
```

【标准答案（内部参考）】：
{standard_answer if standard_answer else '暂无'}

**输出格式（严格JSON）：**
```json
{{
    "overall": {{
        "status": "correct|partial|incorrect",
        "summary": "整体评价（1-2句话）"
    }},
    "comments": [
        {{
            "line": 行号,
            "type": "error|warning|suggestion",
            "message": "简短评论（不超过50字）",
            "hint": "引导性问题"
        }}
    ],
    "highlights": [
        {{
            "line": 行号,
            "type": "good",
            "message": "这里做得好的地方"
        }}
    ]
}}
```

**要求：**
1. comments 只标记有问题的行，不要标记正确的行
2. highlights 标记做得好的地方，给予肯定
3. message 要简短，使用苏格拉底式提问
4. 不要直接给出正确答案

请输出JSON："""
            
            llm = get_llm(session.get('xiaohang_model', 'xhang'))
            full_response = ""
            for content_piece in llm._call(prompt):
                full_response += content_piece
                yield content_piece
                
        except Exception as e:
            yield f"错误: {str(e)}"
    
    return Response(stream_with_context(generate_response()), mimetype='text/event-stream')


# ==================== 作业模式 - 测试用例判定 ====================

@xiaohang_enhanced_bp.route('/init_homework_session', methods=['POST'])
def init_homework_session():
    """初始化作业模式会话"""
    data = request.json
    homework_id = data.get('homework_id', '')  # e.g. "第一次作业"
    
    if not homework_id:
        return jsonify({"error": "请选择作业"}), 400
    
    session_id = str(uuid.uuid4())
    session['xiaohang_session_id'] = session_id
    session['xiaohang_topics'] = []
    session['xiaohang_difficulty'] = '简单'
    session['xiaohang_correct_count'] = 0
    session['xiaohang_model'] = 'loopcoder'
    session['xiaohang_language'] = 'C'
    session['xiaohang_mode'] = 'homework'  # 标记为作业模式
    session['xiaohang_homework_id'] = homework_id
    
    return jsonify({
        "message": "作业会话初始化成功",
        "session_id": session_id,
        "homework_id": homework_id
    })


@xiaohang_enhanced_bp.route('/switch_homework_problem', methods=['POST'])
def switch_homework_problem():
    """切换作业题目 - 轻量级：只清缓存+存题目，不生成标准答案（标准答案按需生成）"""
    session_id = session.get('xiaohang_session_id')
    if not session_id:
        return jsonify({"error": "会话未初始化"}), 400

    data = request.get_json()
    problem_text = (data.get('problem_text') or '').strip()
    if not problem_text:
        return jsonify({"error": "题目内容不能为空"}), 400

    redis_client = get_redis_client()
    problem_key = f"xiaohang_problem:{session_id}"

    # 1. 清理所有模块输出 + 递增 generation token（使正在运行的 pregenerate 失效）
    clear_all_guidance_outputs(session_id)

    # 2. 存储新题目（标准答案为空，后续按需生成）
    topics = session.get('xiaohang_topics', [])
    redis_client.setex(
        problem_key,
        3600,
        json.dumps({
            "problem": problem_text,
            "standard_answer": "",
            "homework_mode": True,
            "difficulty": session.get('xiaohang_difficulty', '简单'),
            "topics": topics,
            "timestamp": time.time()
        })
    )

    return jsonify({"message": "题目已切换", "problem_text": problem_text})


@xiaohang_enhanced_bp.route('/submit_code_homework', methods=['POST'])
def submit_code_homework():
    """作业模式提交代码 - 使用测试用例判定（本地gcc编译运行）"""
    import subprocess, tempfile, uuid
    
    session_id = session.get('xiaohang_session_id')
    if not session_id:
        return jsonify({"result": "error", "message": "会话未初始化"}), 400
    
    data = request.json
    user_code = data.get('code', '')
    test_cases = data.get('test_cases', [])
    language = session.get('xiaohang_language', 'C')
    
    if not user_code.strip():
        return jsonify({"result": "error", "message": "代码不能为空"}), 400
    
    if not test_cases:
        return jsonify({"result": "error", "message": "没有测试用例"}), 400
    
    results = []
    passed = 0
    total = len(test_cases)
    
    # 创建临时目录用于编译
    tmp_dir = tempfile.mkdtemp(prefix='homework_')
    unique_id = uuid.uuid4().hex[:8]
    src_file = os.path.join(tmp_dir, f'solution_{unique_id}.c')
    exe_file = os.path.join(tmp_dir, f'solution_{unique_id}')
    
    try:
        # 写入源代码文件 —— 自动修复 void main() 问题
        # void main() 在 Linux gcc 下会导致退出码不为0，被误判为运行时错误
        fixed_code = user_code
        import re
        fixed_code = re.sub(r'\bvoid\s+main\s*\(', 'int main(', fixed_code)
        # 如果用了 main() 但没有 return 语句，gcc 会自动补 return 0（C99+），
        # 但为了兼容旧标准，编译时加 -std=c99
        with open(src_file, 'w', encoding='utf-8') as f:
            f.write(fixed_code)
        
        if language == 'C':
            # 编译（移除 -std=c99 以支持更多旧式写法，添加 -w 忽略所有警告）
            compile_proc = subprocess.run(
                ['gcc', src_file, '-o', exe_file, '-lm', '-w'],
                capture_output=True, text=True, timeout=15
            )
            if compile_proc.returncode != 0:
                # 编译失败，所有测试点都标记为编译错误
                print(f"[Homework] 编译失败: {compile_proc.stderr[:500]}")
                for i in range(total):
                    results.append({'index': i + 1, 'passed': False, 'reason': '编译错误'})
                return jsonify({"passed": 0, "total": total, "all_passed": False, "results": results})
            
            # 逐个测试点运行
            for i, tc in enumerate(test_cases):
                tc_input = tc.get('input', '')
                tc_expected = tc.get('expected_output', '').strip()
                tc_files = tc.get('files', {})  # 获取测试用例定义的文件
                tc_expected_files = tc.get('expected_files', {}) # 获取预期的输出文件

                # 准备测试环境：将测试文件写入临时目录
                current_cwd = os.getcwd() # 记录当前工作目录
                try:
                    # 切换到临时目录运行，以便程序能找到文件
                    os.chdir(tmp_dir)
                    
                    # 写入输入文件
                    for filename, content in tc_files.items():
                        with open(os.path.join(tmp_dir, filename), 'w', encoding='utf-8') as f:
                            f.write(content)

                    run_proc = subprocess.run(
                        [exe_file],
                        input=tc_input, capture_output=True, text=True, timeout=10
                    )
                    
                    # 检查文件输出模式
                    file_check_passed = True
                    if tc_expected_files:
                        for filename, expected_content in tc_expected_files.items():
                            file_path = os.path.join(tmp_dir, filename)
                            if not os.path.exists(file_path):
                                file_check_passed = False
                                print(f"[Homework] 测试点{i+1} 缺少输出文件: {filename}")
                                break
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                actual_content = f.read().strip()
                                # 简单处理：去除首尾空白后比较
                                if actual_content != expected_content.strip():
                                    file_check_passed = False
                                    print(f"[Homework] 测试点{i+1} 文件 {filename} 内容不匹配: expected={repr(expected_content)}, actual={repr(actual_content)}")
                                    break
                    
                    # 综合判定：
                    # 1. 如果有预期文件输出，优先检查文件内容是否一致
                    # 2. 如果没有预期文件，或者文件一致，再检查标准输出（如果有 expected_output 的话）
                    
                    is_correct = False
                    if tc_expected_files:
                         # 文件模式：只要文件对就算过（忽略 stdout 和 returncode）
                         if file_check_passed:
                             is_correct = True
                    else:
                        # 标准输出模式
                        actual_output = run_proc.stdout.strip()
                        if actual_output == tc_expected:
                            is_correct = True
                    
                    if is_correct:
                        passed += 1
                        results.append({'index': i + 1, 'passed': True})
                    # 如果不正确，再检查是否是运行时错误
                    elif run_proc.returncode != 0:
                        print(f"[Homework] 测试点{i+1} 运行时错误: {run_proc.stderr[:200]}")
                        results.append({'index': i + 1, 'passed': False, 'reason': '运行时错误'})
                    else:
                        if not tc_expected_files:
                             print(f"[Homework] 测试点{i+1} 不匹配: expected={repr(tc_expected)}, actual={repr(actual_output)}")
                        results.append({'index': i + 1, 'passed': False, 'reason': '答案错误'})

                except subprocess.TimeoutExpired:
                    results.append({'index': i + 1, 'passed': False, 'reason': '超时'})
                except Exception as e:
                    print(f"[Homework] 测试点{i+1}执行异常: {e}")
                    results.append({'index': i + 1, 'passed': False, 'reason': '系统错误'})
                finally:
                    # 恢复工作目录
                    os.chdir(current_cwd)
        
        elif language == 'Python':
            # Python 直接运行，不需要编译
            for i, tc in enumerate(test_cases):
                tc_input = tc.get('input', '')
                tc_expected = tc.get('expected_output', '').strip()
                try:
                    run_proc = subprocess.run(
                        ['python3', src_file],
                        input=tc_input, capture_output=True, text=True, timeout=10
                    )
                    if run_proc.returncode != 0:
                        print(f"[Homework] 测试点{i+1} 运行错误: {run_proc.stderr[:200]}")
                        results.append({'index': i + 1, 'passed': False, 'reason': '运行时错误'})
                        continue
                    actual_output = run_proc.stdout.strip()
                    if actual_output == tc_expected:
                        passed += 1
                        results.append({'index': i + 1, 'passed': True})
                    else:
                        print(f"[Homework] 测试点{i+1} 不匹配: expected={repr(tc_expected)}, actual={repr(actual_output)}")
                        results.append({'index': i + 1, 'passed': False, 'reason': '答案错误'})
                except subprocess.TimeoutExpired:
                    results.append({'index': i + 1, 'passed': False, 'reason': '超时'})
                except Exception as e:
                    print(f"[Homework] 测试点{i+1}执行异常: {e}")
                    results.append({'index': i + 1, 'passed': False, 'reason': '系统错误'})
        else:
            return jsonify({"result": "error", "message": f"不支持的语言: {language}"}), 400
    
    finally:
        # 清理临时文件
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)
    
    all_passed = (passed == total)
    
    # 保存答题记录
    try:
        student_id_number = session.get('student_id_number', 'anonymous')
        homework_id = session.get('xiaohang_homework_id', '')
        
        redis_client = get_redis_client()
        problem_key = f"xiaohang_problem:{session_id}"
        problem_data = redis_client.get(problem_key)
        current_problem = ''
        if problem_data:
            problem_info = json.loads(problem_data.decode('utf-8'))
            current_problem = problem_info.get('problem', '')
        
        diagnosis_result = f"通过 {passed}/{total} 个测试点"
        save_answer_record(
            student_id=student_id_number,
            session_id=session_id,
            topic=homework_id,
            difficulty=session.get('xiaohang_difficulty', '简单'),
            problem_text=current_problem,
            submitted_code=user_code,
            diagnosis_result=diagnosis_result,
            is_correct=all_passed,
            language=language
        )
    except Exception as db_err:
        print(f"[DB] 保存作业答题记录失败: {db_err}")
    
    return jsonify({
        "passed": passed,
        "total": total,
        "all_passed": all_passed,
        "results": results
    })
