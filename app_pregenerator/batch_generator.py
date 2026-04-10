import os
import sys
import json
import time
from typing import Dict, Any, List
from openai import OpenAI

# Add parent path to allow importing retriever and local AI-for-Education modules
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Import the retriever from our own project
try:
    from retriever import LeetCodeRetriever
except ImportError:
    try:
        from ..retriever import LeetCodeRetriever
    except Exception:
        print("Warning: Failed to import LeetCodeRetriever. Make sure leetcode_db.json and retriever.py are available.")
        class LeetCodeRetriever:
            def retrieve(self, tag=None, difficulty=None): return None

# Import prompts from current AI-for-Education project
try:
    from config import get_system_prompts
except ImportError:
    try:
        from ..config import get_system_prompts
    except Exception:
        print("Failed to import config from current AI-for-Education project. Verify paths.")
        sys.exit(1)

DEFAULT_API_KEY = "sk-AKR-api-ah23fua9f8w392noifa"
DEFAULT_BASE_URL = "https://api-akr.top/v1/"
DEFAULT_MODEL = "gpt-5.4"

client = OpenAI(
    api_key=DEFAULT_API_KEY,
    base_url=DEFAULT_BASE_URL
)
MODEL = DEFAULT_MODEL

# Map Chinese topics to LeetCode tags
TOPIC_TO_LEETCODE = {
    '栈': 'Stack',
    '队列': 'Queue',
    '数组': 'Array',
    '链表': 'Linked List',
    '哈希表': 'Hash Table',
    '散列表': 'Hash Table',
    '堆': 'Heap (Priority Queue)',
    '优先队列': 'Heap (Priority Queue)',
    '树': 'Tree',
    '二叉树': 'Binary Tree',
    '二叉搜索树': 'Binary Search Tree',
    '图': 'Graph',
    'DFS': 'Depth-First Search',
    'BFS': 'Breadth-First Search',
    '最短路': 'Shortest Path',
    '最小生成树': 'Minimum Spanning Tree',
    '拓扑排序': 'Topological Sort',
    '排序': 'Sorting',
    '查找': 'Binary Search',
    '动态规划': 'Dynamic Programming',
    '贪心': 'Greedy',
    '回溯': 'Backtracking',
    '递归': 'Recursion'
}

# The actual topics to generate and their target amounts according to user request
TARGETS = {
    '简单': 30,
    '中等': 20,
    '困难': 10
}

# Ensure retriever matches leetcode difficulty
DIFF_MAP = {
    '简单': 'Easy',
    '中等': 'Medium',
    '困难': 'Hard'
}

def build_client(api_key=None, base_url=None):
    return OpenAI(
        api_key=api_key or DEFAULT_API_KEY,
        base_url=base_url or DEFAULT_BASE_URL
    )


def call_llm(messages, max_retries=3, client_instance=None, model_name=None, logger=None):
    client_to_use = client_instance or client
    model_to_use = model_name or MODEL
    for i in range(max_retries):
        try:
            response = client_to_use.chat.completions.create(
                model=model_to_use,
                messages=messages,
                temperature=0.6,
                timeout=60
            )
            return response.choices[0].message.content
        except Exception as e:
            message = f"Error calling LLM: {e}. Retrying {i+1}/{max_retries}..."
            print(message)
            if logger:
                logger(message)
            time.sleep(2)
    return ""

def _redact_standard_answer_for_completion(standard_answer):
    import re
    lines = standard_answer.split('\n')
    redacted_lines = []
    in_code_block = False
    code_block_lang = ''
    func_signatures = []

    for line in lines:
        stripped = line.strip()
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
            func_match = re.match(r'^(\s*)((?:void|int|char|float|double|long|short|unsigned|struct\s+\w+)\s*\*?\s+\w+\s*\([^)]*\))\s*\{?\s*$', line)
            if func_match:
                func_signatures.append(f'  - 函数: {func_match.group(2).strip()}')
            continue
        else:
            redacted_lines.append(line)

    result = '\n'.join(redacted_lines)
    if func_signatures:
        result += '\n\n[标准答案包含的函数结构]：\n' + '\n'.join(func_signatures)

    return result

def extract_leaf_nodes_from_framework(framework_text):
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
        return leaf_nodes
    except Exception as e:
        return []

def format_leaf_nodes_for_prompt(leaf_nodes):
    if not leaf_nodes: return ""
    ctrl_icons = {'sequence': '📋 顺序结构', 'selection': '🔀 选择结构', 'loop': '🔄 循环结构'}
    text = f"【代码框架最终分解结果 - 叶子节点列表（伪代码和代码补全必须与此一一对应）】：\n共 {len(leaf_nodes)} 个最终子模块，按执行顺序排列：\n\n"
    for i, node in enumerate(leaf_nodes, 1):
        ctrl = ctrl_icons.get(node.get('controlType', 'sequence'), '📋 顺序结构')
        text += f"第{i}部分：{node['name']}（{ctrl}）\n"
        ipo = node.get('ipo', {})
        for k in ['input', 'storage', 'process', 'output']:
            if ipo.get(k): text += f"  {k}：{ipo[k]}\n"
    text += "\n【一致性要求】：\n1. 伪代码必须严格按照上述模块组织\n2. 代码补全结构必须对应\n"
    return text

def generate_full_problem_pipeline(retriever, topic, difficulty, client_instance=None, model_name=None, logger=None):
    tag = TOPIC_TO_LEETCODE.get(topic, "")
    seed = retriever.retrieve(tag=tag, difficulty=DIFF_MAP[difficulty])
    if logger:
        logger(f"开始生成知识点题：{topic}/{difficulty}")
        logger(f"英文标签：{tag or '无'}")
        logger("已检索到英文种子题" if seed else "未检索到英文种子题，将直接生成")
    
    seed_context = ""
    if seed:
        seed_context = f"【参考种子题目】\n限制：请以该题为参考出题，切记！\n标题：{seed.get('title')}\n描述：{seed.get('content')}"
        
    base_prompt = f"""你是一名专业的C语言数据结构与算法出题专家。请生成一道关于【{topic}】的【{difficulty}】难度的编程题，并提供参考代码。
    
{seed_context}

要求：
1. 你的题目描述应改编自种子题目，确保考察核心机制，避免题目过于直白。
2. 请直接以JSON格式返回：包含 `problem` 和 `standard_answer` 字段。
`problem` 是Markdown格式的问题描述。
`standard_answer` 是完整的带注释的C语言代码。
3. 请只输出纯JSON，不要输出多余的包装或思考过程。
"""
    prob_ans_text = call_llm(
        [{"role": "user", "content": base_prompt}],
        client_instance=client_instance,
        model_name=model_name,
        logger=logger
    )
    try:
        import re
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', prob_ans_text)
        if json_match:
            data = json.loads(json_match.group(1))
        else:
            first_brace = prob_ans_text.find('{')
            last_brace = prob_ans_text.rfind('}')
            data = json.loads(prob_ans_text[first_brace:last_brace + 1])
        problem = data.get("problem", "")
        standard_answer = data.get("standard_answer", "")
    except Exception as e:
        print(f"Failed to parse problem JSON: {e}")
        return None
        
    system_prompts = get_system_prompts("C")
    if logger:
        logger("标准答案生成完成，开始生成思路")
    
    silu_sys = system_prompts.get("思路", "")
    silu_user = f"【当前题目】\n{problem}\n\n【内部标准答案】\n{standard_answer}\n\n请按ISPO结构给出【思路】。"
    silu_res = call_llm(
        [{"role": "system", "content": silu_sys}, {"role": "user", "content": silu_user}],
        client_instance=client_instance,
        model_name=model_name,
        logger=logger
    )
    if logger:
        logger("思路生成完成，开始生成代码框架")
    
    kuangjia_sys = f"""你是一名程序设计教学专家。请将问题分解为子模块（至少包含input, storage, process, output四个维度）。必须输出带有 ```json 和 ``` 包裹的JSON格式，包含 parentProblem, level, subProblems (name, description, controlType, ipo, needsFurtherDecomposition, codeHint). 知识点：{topic}"""
    kuangjia_user = f"【当前题目】\n{problem}\n\n【内部标准答案】\n{standard_answer}\n\n【前置思路】\n{silu_res}\n\n请严格分解框架，输出JSON。"
    
    kuangjia_res = call_llm(
        [{"role": "system", "content": kuangjia_sys}, {"role": "user", "content": kuangjia_user}],
        client_instance=client_instance,
        model_name=model_name,
        logger=logger
    )
    if logger:
        logger("代码框架生成完成，开始生成伪代码")
    
    leaf_nodes = extract_leaf_nodes_from_framework(kuangjia_res)
    leaf_text = format_leaf_nodes_for_prompt(leaf_nodes)
    weidaima_sys = system_prompts.get("伪代码", "") + "\n" + leaf_text
    weidaima_user = f"【内部标准答案】\n{standard_answer}\n\n【前置框架】\n{kuangjia_res}\n\n请严格按框架模块输出独立伪代码块。"
    weidaima_res = call_llm(
        [{"role": "system", "content": weidaima_sys}, {"role": "user", "content": weidaima_user}],
        client_instance=client_instance,
        model_name=model_name,
        logger=logger
    )
    if logger:
        logger("伪代码生成完成，开始生成代码补全")
    
    hexin_sys = system_prompts.get("核心语句", "")
    hexin_user = f"【标准代码脱敏】\n{_redact_standard_answer_for_completion(standard_answer)}\n\n【前置伪代码】\n{weidaima_res}\n\n请生成带TODO挖空的代码骨架。"
    hexin_res = call_llm(
        [{"role": "system", "content": hexin_sys}, {"role": "user", "content": hexin_user}],
        client_instance=client_instance,
        model_name=model_name,
        logger=logger
    )
    if logger:
        logger("代码补全生成完成")
    
    return {
        "problem": problem,
        "standard_answer": standard_answer,
        "topic": topic,
        "difficulty": difficulty,
        "modules": {
            "思路": silu_res,
            "框架": kuangjia_res,
            "伪代码": weidaima_res,
            "核心语句": hexin_res
        }
    }

def main():
    retriever = LeetCodeRetriever(os.path.join(project_root, "leetcode_db.json"))
    db_file = os.path.join(os.path.dirname(__file__), "problem_bank.json")
    
    if os.path.exists(db_file):
        with open(db_file, "r", encoding="utf-8") as f:
            bank = json.load(f)
    else:
        bank = []
        
    def get_count(topic, diff):
        return sum(1 for p in bank if p.get("topic") == topic and p.get("difficulty") == diff)

    print("Starting batch generation...")
    
    # We will test first to prevent running all of them if script fails.
    test_run = os.environ.get("TEST_RUN", "0") == "1"
    
    for topic, leetcode_tag in TOPIC_TO_LEETCODE.items():
        if not leetcode_tag: continue
        
        for diff, target_count in TARGETS.items():
            if test_run: target_count = 1  
            current_count = get_count(topic, diff)
            if current_count >= target_count:
                print(f"[{topic}] - {diff} Already met target ({current_count}/{target_count})")
                if test_run: continue
                continue
                
            tasks_to_do = target_count - current_count
            print(f"Generating [{topic}] - {diff}: need {tasks_to_do} more...")
            
            for i in range(tasks_to_do):
                print(f"  Generating {i+1}/{tasks_to_do} ...")
                result = generate_full_problem_pipeline(retriever, topic, diff)
                if result:
                    result["id"] = f"{topic}_{diff}_{int(time.time()*1000)}"
                    bank.append(result)
                    with open(db_file, "w", encoding="utf-8") as f:
                        json.dump(bank, f, ensure_ascii=False, indent=2)
                    print(f"  -> Saved!")
                else:
                    print(f"  -> Failed to generate.")
                
                if test_run: break
        if test_run: break

if __name__ == "__main__":
    main()
