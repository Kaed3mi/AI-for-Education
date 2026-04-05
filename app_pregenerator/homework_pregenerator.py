import argparse
import json
import os
import re
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
HOMEWORK_JS_PATH = os.path.join(PROJECT_ROOT, "static", "homework_data.js")
OUTPUT_PATH = os.path.join(BASE_DIR, "homework_guidance_bank.json")
DEFAULT_BASE_URL = ""
DEFAULT_MODEL = ""
DEFAULT_API_KEY = ""


def extract_leaf_nodes_from_framework(framework_text: str) -> List[Dict[str, Any]]:
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
    except Exception:
        return []


def format_leaf_nodes_for_prompt(leaf_nodes: List[Dict[str, Any]]) -> str:
    if not leaf_nodes:
        return ""
    ctrl_icons = {'sequence': '顺序结构', 'selection': '选择结构', 'loop': '循环结构'}
    text = f"【代码框架最终叶子节点】共 {len(leaf_nodes)} 个，后续伪代码和代码补全必须一一对应：\n"
    for i, node in enumerate(leaf_nodes, 1):
        text += f"{i}. {node['name']}（{ctrl_icons.get(node.get('controlType', 'sequence'), '顺序结构')}）\n"
        ipo = node.get('ipo', {})
        for key in ['input', 'storage', 'process', 'output']:
            if ipo.get(key):
                text += f"   - {key}: {ipo[key]}\n"
    return text


def redact_standard_answer_for_completion(standard_answer: str) -> str:
    lines = standard_answer.split('\n')
    redacted_lines = []
    in_code_block = False
    func_signatures = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('```') and not in_code_block:
            in_code_block = True
            redacted_lines.append('[代码块开始，具体实现已隐藏]')
            continue
        elif stripped.startswith('```') and in_code_block:
            in_code_block = False
            redacted_lines.append('[代码块结束]')
            continue

        if in_code_block:
            func_match = re.match(r'^(\s*)((?:void|int|char|float|double|long|short|unsigned|struct\s+\w+)\s*\*?\s+\w+\s*\([^)]*\))\s*\{?\s*$', line)
            if func_match:
                func_signatures.append(f"- 函数: {func_match.group(2).strip()}")
            continue
        redacted_lines.append(line)

    if func_signatures:
        redacted_lines.append("\n[标准答案包含的函数结构]")
        redacted_lines.extend(func_signatures)
    return "\n".join(redacted_lines)


def llm_to_text(call_llm_fn, messages: List[Dict[str, str]]) -> str:
    return call_llm_fn(messages).strip()


def get_model_and_helpers(model_name: str):
    from openai import OpenAI

    client = OpenAI(
        api_key=os.getenv("AKR_API_KEY", DEFAULT_API_KEY),
        base_url=os.getenv("AKR_BASE_URL", DEFAULT_BASE_URL),
    )

    def call_llm(messages: List[Dict[str, str]], max_retries: int = 3) -> str:
        for i in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=0.6,
                    timeout=120,
                )
                return (response.choices[0].message.content or "").strip()
            except Exception as e:
                print(f"LLM 调用失败，重试 {i + 1}/{max_retries}: {e}")
                time.sleep(2)
        return ""

    return {
        "call_llm": call_llm,
        "extract_leaf_nodes_from_framework": extract_leaf_nodes_from_framework,
        "format_leaf_nodes_for_prompt": format_leaf_nodes_for_prompt,
        "redact_standard_answer": redact_standard_answer_for_completion,
    }


def convert_homework_js_to_json_text(js_text: str) -> str:
    match = re.search(r"const\s+HOMEWORK_DATA\s*=\s*(\{[\s\S]*\})\s*;\s*$", js_text)
    if not match:
        raise ValueError("未找到 HOMEWORK_DATA 对象")

    obj_text = match.group(1)

    def replace_js_strings(text: str) -> str:
        out: List[str] = []
        i = 0
        n = len(text)

        while i < n:
            ch = text[i]
            if ch not in ("'", "`"):
                out.append(ch)
                i += 1
                continue

            quote = ch
            i += 1
            buf: List[str] = []
            while i < n:
                cur = text[i]
                if cur == "\\" and i + 1 < n:
                    nxt = text[i + 1]
                    # 模板字符串中的 \`、\' 等都按字面值保留
                    buf.append(nxt)
                    i += 2
                    continue
                if cur == quote:
                    i += 1
                    break
                buf.append(cur)
                i += 1

            out.append(json.dumps("".join(buf)))

        return "".join(out)

    obj_text = replace_js_strings(obj_text)

    # 补齐对象 key 的引号
    obj_text = re.sub(r'([{\[,]\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*:)', r'\1"\2"\3', obj_text)

    # 去掉尾随逗号
    obj_text = re.sub(r",(\s*[}\]])", r"\1", obj_text)
    return obj_text


def load_homework_data(js_path: str = HOMEWORK_JS_PATH) -> Dict[str, Any]:
    try:
        node_script = (
            "const fs=require('fs');"
            "const vm=require('vm');"
            "const code=fs.readFileSync(process.argv[1],'utf8');"
            "const sandbox={};"
            "vm.createContext(sandbox);"
            "vm.runInContext(code + '\\nthis.__HOMEWORK_DATA__ = HOMEWORK_DATA;', sandbox);"
            "process.stdout.write(JSON.stringify(sandbox.__HOMEWORK_DATA__));"
        )
        result = subprocess.run(
            ["node", "-e", node_script, js_path],
            capture_output=True,
            check=True,
            cwd=BASE_DIR,
        )
        return json.loads(result.stdout.decode("utf-8"))
    except Exception:
        with open(js_path, "r", encoding="utf-8") as f:
            js_text = f.read()
        json_text = convert_homework_js_to_json_text(js_text)
        return json.loads(json_text)


def load_existing_output(path: str = OUTPUT_PATH) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def save_output(entries: List[Dict[str, Any]], path: str = OUTPUT_PATH) -> None:
    entries.sort(key=lambda x: (x.get("homework_key", ""), x.get("problem_index", -1)))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def build_standard_answer_prompt(problem_text: str) -> str:
    return f"""你是一名专业的C语言程序设计助教。请为下面这道作业题提供完整、可运行、尽量稳健的标准答案。

【要求】
1. 输出完整 C 语言代码
2. 代码中包含必要注释
3. 如果题目涉及文件操作，严格按题目指定文件名读写
4. 如果题目有格式要求，输出必须严格匹配
5. 代码后补充简短复杂度分析

【输出格式】
## 标准答案

**完整代码：**
```c
[完整代码]
```

**复杂度分析：**
- 时间复杂度：[分析]
- 空间复杂度：[分析]

【题目】
{problem_text}
"""


def build_thought_messages(problem_text: str, standard_answer: str) -> List[Dict[str, str]]:
    system_prompt = """你是一名C语言程序设计助教。请输出高质量的智能审题内容。
要求：
1. 用中文
2. 使用 ISPO 结构
3. 不直接泄露完整答案
4. 适合作业辅导场景
5. 结尾带一句引导学生继续学习的提示
"""
    user_prompt = f"""【题目】
{problem_text}

【内部标准答案】
{standard_answer}

请输出“智能审题/思路”内容。"""
    return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]


def build_framework_prompt(problem_text: str, standard_answer: str, thought: str) -> str:
    return f"""你是一名程序设计教学专家。请将下面这道作业题分解为可教学的程序模块，输出严格 JSON。

【目标】
1. 框架必须与标准答案结构一致
2. 只拆核心算法/功能模块，不要拆头文件、宏、main函数
3. 每个模块必须包含 input、storage、process、output 四个字段

【输出格式】
```json
{{
  "parentProblem": "问题描述",
  "level": 0,
  "subProblems": [
    {{
      "name": "模块名",
      "description": "模块说明",
      "controlType": "sequence",
      "ipo": {{
        "input": "输入",
        "storage": "存储",
        "process": "处理",
        "output": "输出"
      }},
      "needsFurtherDecomposition": false,
      "codeHint": "建议性提示"
    }}
  ],
  "overallIPO": {{
    "input": "总输入",
    "storage": "总体存储",
    "process": "总体处理",
    "output": "总体输出"
  }}
}}
```

【控制结构枚举】
- sequence
- selection
- loop

【内部参考 - 标准答案】
{standard_answer}

【内部参考 - 智能审题】
{thought}

【题目】
{problem_text}
"""


def build_pseudocode_messages(problem_text: str, standard_answer: str, thought: str, framework: str, helpers: Dict[str, Any]) -> List[Dict[str, str]]:
    leaf_nodes = helpers["extract_leaf_nodes_from_framework"](framework)
    leaf_constraint = helpers["format_leaf_nodes_for_prompt"](leaf_nodes)
    system_prompt = """你是一名C语言算法教学专家。请输出“伪代码”模块。
要求：
1. 必须按框架模块逐段输出
2. 使用 ```pseudocode 代码块
3. 使用 if-then-else、for-do、while-do、← 等伪代码写法
4. 不能写成具体C代码
5. 伪代码块必须有实际逻辑语句，不能只有注释
"""
    user_prompt = f"""【题目】
{problem_text}

【内部参考 - 标准答案】
{standard_answer}

【内部参考 - 智能审题】
{thought}

【内部参考 - 代码框架】
{framework}

{leaf_constraint}

请输出与框架一一对应的伪代码内容。
"""
    return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]


def build_core_messages(problem_text: str, standard_answer: str, thought: str, framework: str, pseudocode: str, helpers: Dict[str, Any]) -> List[Dict[str, str]]:
    leaf_nodes = helpers["extract_leaf_nodes_from_framework"](framework)
    leaf_constraint = helpers["format_leaf_nodes_for_prompt"](leaf_nodes)
    system_prompt = """你是一名C语言算法教学专家。请输出“代码补全/核心语句”模块。
要求：
1. 只输出一份带 TODO 标记的 C 代码
2. TODO 处只能有注释，不能直接给实现
3. 代码结构必须与框架和伪代码对应
4. 适合作业辅导场景
"""
    redacted = helpers["redact_standard_answer"](standard_answer)
    user_prompt = f"""【题目】
{problem_text}

【内部参考 - 已脱敏标准答案】
{redacted}

【内部参考 - 智能审题】
{thought}

【内部参考 - 代码框架】
{framework}

【内部参考 - 伪代码】
{pseudocode}

{leaf_constraint}

请输出一份带 TODO 标记的代码补全内容。
"""
    return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]


def generate_entry(call_llm_fn, helpers: Dict[str, Any], homework_key: str, homework_name: str, problem_index: int, problem: Dict[str, Any]) -> Dict[str, Any]:
    title = problem["title"]
    problem_text = problem["description"]

    print(f"\n=== 生成作业资产: {homework_key} #{problem_index} {title} ===")
    started_at = time.time()

    standard_answer = llm_to_text(call_llm_fn, [{"role": "user", "content": build_standard_answer_prompt(problem_text)}])
    thought = llm_to_text(call_llm_fn, build_thought_messages(problem_text, standard_answer))
    framework = llm_to_text(call_llm_fn, [{"role": "user", "content": build_framework_prompt(problem_text, standard_answer, thought)}])
    pseudocode = llm_to_text(call_llm_fn, build_pseudocode_messages(problem_text, standard_answer, thought, framework, helpers))
    core = llm_to_text(call_llm_fn, build_core_messages(problem_text, standard_answer, thought, framework, pseudocode, helpers))

    return {
        "homework_key": homework_key,
        "homework_name": homework_name,
        "problem_index": problem_index,
        "title": title,
        "problem": problem_text,
        "standard_answer": standard_answer,
        "modules": {
            "思路": thought,
            "框架": framework,
            "伪代码": pseudocode,
            "核心语句": core,
        },
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "elapsed_seconds": round(time.time() - started_at, 2),
    }


def main():
    parser = argparse.ArgumentParser(description="批量预生成作业题的智能审题/框架/伪代码/代码补全资产")
    parser.add_argument("--homework-key", help="仅生成指定作业，如 homework0")
    parser.add_argument("--problem-index", type=int, help="仅生成指定题号（0-based）")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"使用的模型名，默认 {DEFAULT_MODEL}")
    parser.add_argument("--overwrite", action="store_true", help="覆盖已存在的题目资产")
    args = parser.parse_args()

    homework_data = load_homework_data()
    existing_entries = load_existing_output()
    existing_map = {
        f"{item.get('homework_key')}:{item.get('problem_index')}": item
        for item in existing_entries
        if item.get("homework_key") is not None and item.get("problem_index") is not None
    }

    helpers = get_model_and_helpers(args.model)
    call_llm_fn = helpers["call_llm"]
    updated_map = dict(existing_map)

    for homework_key, homework_info in homework_data.items():
        if args.homework_key and homework_key != args.homework_key:
            continue

        problems = homework_info.get("problems", [])
        for idx, problem in enumerate(problems):
            if args.problem_index is not None and idx != args.problem_index:
                continue

            entry_key = f"{homework_key}:{idx}"
            if entry_key in updated_map and not args.overwrite:
                print(f"跳过已存在资产: {entry_key} {problem.get('title', '')}")
                continue

            updated_map[entry_key] = generate_entry(
                call_llm_fn=call_llm_fn,
                helpers=helpers,
                homework_key=homework_key,
                homework_name=homework_info.get("name", homework_key),
                problem_index=idx,
                problem=problem,
            )
            save_output(list(updated_map.values()))

    save_output(list(updated_map.values()))
    print(f"\n已输出到: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
