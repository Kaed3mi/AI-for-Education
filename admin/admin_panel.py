import json
import os
import sys
import time
import threading
from functools import wraps
from typing import Any, Dict, List, Optional

from flask import Blueprint, Response, current_app, jsonify, request, session
from openai import OpenAI

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from retriever import LeetCodeRetriever
from app_pregenerator.batch_generator import build_client as build_batch_client, generate_full_problem_pipeline
from app_pregenerator.homework_pregenerator import (
    DEFAULT_API_KEY,
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    build_core_messages,
    build_framework_prompt,
    build_pseudocode_messages,
    build_standard_answer_prompt,
    build_thought_messages,
    extract_leaf_nodes_from_framework,
    format_leaf_nodes_for_prompt,
    load_homework_data,
    redact_standard_answer_for_completion,
)

admin_bp = Blueprint("admin_panel", __name__)

ADMIN_SETTINGS_PATH = os.path.join(BASE_DIR, "admin_settings.json")
BATCH_JOBS_PATH = os.path.join(BASE_DIR, "admin_batch_jobs.json")
LOCAL_APP_PREGENERATOR_DIR = os.path.join(PROJECT_ROOT, "app_pregenerator")
KNOWLEDGE_BANK_PATH = os.path.join(LOCAL_APP_PREGENERATOR_DIR, "problem_bank.json")
HOMEWORK_BANK_PATH = os.path.join(LOCAL_APP_PREGENERATOR_DIR, "homework_guidance_bank.json")
LEETCODE_DB_PATH = os.path.join(PROJECT_ROOT, "leetcode_db.json")

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

KNOWLEDGE_TOPIC_ORDER = [
    '数组', '队列', '栈', '链表', '哈希表', '散列表', '堆', '优先队列',
    '树', '二叉树', '二叉搜索树', 'AVL', '红黑树', 'B树', '字典树', 'Trie',
    '图', 'DFS', 'BFS', '最短路', '最小生成树', '拓扑排序',
    '排序', '查找', '动态规划', '贪心', '回溯', '递归'
]

DIFF_MAP = {
    '简单': 'Easy',
    '中等': 'Medium',
    '困难': 'Hard'
}

BATCH_STATE = {
    "current_job_id": None,
    "jobs": [],
    "logs": {},
    "lock": threading.Lock(),
}


def default_admin_settings() -> Dict[str, Any]:
    return {
        "admin_password": os.getenv("ADMIN_PASSWORD", "zgl666"),
        "llm": {
            "base_url": os.getenv("AKR_BASE_URL", DEFAULT_BASE_URL),
            "api_key": os.getenv("AKR_API_KEY", DEFAULT_API_KEY),
            "model": os.getenv("ADMIN_MODEL", DEFAULT_MODEL),
        }
    }


def load_json_file(path: str, fallback):
    if not os.path.exists(path):
        return fallback
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return fallback


def save_json_file(path: str, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_jobs() -> List[Dict[str, Any]]:
    return load_json_file(BATCH_JOBS_PATH, [])


def persist_jobs() -> None:
    save_json_file(BATCH_JOBS_PATH, BATCH_STATE["jobs"])


def load_admin_settings() -> Dict[str, Any]:
    settings = load_json_file(ADMIN_SETTINGS_PATH, default_admin_settings())
    merged = default_admin_settings()
    merged.update({k: v for k, v in settings.items() if k != "llm"})
    merged["llm"].update(settings.get("llm", {}))
    return merged


def save_admin_settings(settings: Dict[str, Any]) -> None:
    current = load_admin_settings()
    current["admin_password"] = settings.get("admin_password", current["admin_password"])
    current["llm"].update(settings.get("llm", {}))
    save_json_file(ADMIN_SETTINGS_PATH, current)


def append_job_log(job_id: str, message: str) -> None:
    timestamp = time.strftime("%H:%M:%S")
    line = f"[{timestamp}] {message}"
    with BATCH_STATE["lock"]:
        logs = BATCH_STATE["logs"].setdefault(job_id, [])
        logs.append(line)
        BATCH_STATE["logs"][job_id] = logs[-300:]


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    for job in BATCH_STATE["jobs"]:
        if job.get("id") == job_id:
            return job
    return None


def update_job(job_id: str, **fields) -> Optional[Dict[str, Any]]:
    with BATCH_STATE["lock"]:
        job = get_job(job_id)
        if not job:
            return None
        job.update(fields)
        persist_jobs()
        return job


def serialize_job(job: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": job.get("id"),
        "type": job.get("type"),
        "scope": job.get("scope"),
        "status": job.get("status"),
        "created_at": job.get("created_at"),
        "started_at": job.get("started_at"),
        "finished_at": job.get("finished_at"),
        "total": job.get("total", 0),
        "completed": job.get("completed", 0),
        "failed": job.get("failed", 0),
        "meta": job.get("meta", {}),
    }


def summarize_job_meta(job: Dict[str, Any]) -> str:
    meta = job.get("meta", {})
    if job.get("type") == "knowledge_batch":
        return f"{meta.get('topic','')} / {meta.get('difficulty','')} / 目标 {meta.get('target_count',0)} 道"
    if job.get("type") == "homework_batch":
        items = meta.get("items", [])
        grouped: Dict[str, List[int]] = {}
        for item in items:
            grouped.setdefault(item.get("homework_key", ""), []).append(int(item.get("problem_index", 0)) + 1)
        parts = []
        for key, nums in grouped.items():
            nums.sort()
            parts.append(f"{key}: 第{', '.join(map(str, nums))}题")
        return "；".join(parts)
    return ""


def create_job(job_type: str, scope: str, total: int, meta: Dict[str, Any]) -> Dict[str, Any]:
    job = {
        "id": f"job_{int(time.time() * 1000)}",
        "type": job_type,
        "scope": scope,
        "status": "queued",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "started_at": None,
        "finished_at": None,
        "total": total,
        "completed": 0,
        "failed": 0,
        "meta": meta,
    }
    with BATCH_STATE["lock"]:
        BATCH_STATE["jobs"].insert(0, job)
        persist_jobs()
    append_job_log(job["id"], f"任务已创建：{scope}")
    return job


def bootstrap_batch_state() -> None:
    jobs = load_jobs()
    BATCH_STATE["jobs"] = jobs if isinstance(jobs, list) else []
    for job in BATCH_STATE["jobs"]:
        BATCH_STATE["logs"].setdefault(job.get("id", ""), [])
    # 进程重启后不恢复运行中的任务，只保留历史
    BATCH_STATE["current_job_id"] = None


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("admin_authenticated"):
            return jsonify({"error": "未登录"}), 401
        return fn(*args, **kwargs)
    return wrapper


def mask_api_key(api_key: str) -> str:
    if not api_key:
        return ""
    if len(api_key) <= 8:
        return "*" * len(api_key)
    return api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]


def build_client_and_model() -> tuple[OpenAI, str]:
    settings = load_admin_settings()
    llm = settings["llm"]
    base_url = (llm.get("base_url") or "").strip()
    api_key = (llm.get("api_key") or "").strip()
    model = (llm.get("model") or "").strip()
    if not base_url.startswith(("http://", "https://")):
        raise ValueError("Base URL 必须以 http:// 或 https:// 开头")
    if not api_key:
        raise ValueError("API Key 不能为空")
    if not model:
        raise ValueError("Model 不能为空")
    client = OpenAI(api_key=api_key, base_url=base_url)
    return client, llm["model"]


def call_llm(messages: List[Dict[str, str]], temperature: float = 0.6, timeout: int = 120) -> str:
    client, model = build_client_and_model()
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        timeout=timeout,
    )
    return (response.choices[0].message.content or "").strip()


def load_knowledge_bank() -> List[Dict[str, Any]]:
    return load_json_file(KNOWLEDGE_BANK_PATH, [])


def save_knowledge_bank(items: List[Dict[str, Any]]) -> None:
    save_json_file(KNOWLEDGE_BANK_PATH, items)


def load_homework_bank() -> List[Dict[str, Any]]:
    return load_json_file(HOMEWORK_BANK_PATH, [])


def save_homework_bank(items: List[Dict[str, Any]]) -> None:
    save_json_file(HOMEWORK_BANK_PATH, items)


def find_knowledge_item(item_id: str) -> Optional[Dict[str, Any]]:
    for item in load_knowledge_bank():
        if item.get("id") == item_id:
            return item
    return None


def upsert_knowledge_item(new_item: Dict[str, Any]) -> Dict[str, Any]:
    items = load_knowledge_bank()
    found = False
    for idx, item in enumerate(items):
        if item.get("id") == new_item.get("id"):
            items[idx] = new_item
            found = True
            break
    if not found:
        items.append(new_item)
    save_knowledge_bank(items)
    return new_item


def find_homework_item(homework_key: str, problem_index: int) -> Optional[Dict[str, Any]]:
    for item in load_homework_bank():
        if item.get("homework_key") == homework_key and item.get("problem_index") == problem_index:
            return item
    return None


def upsert_homework_item(new_item: Dict[str, Any]) -> Dict[str, Any]:
    items = load_homework_bank()
    found = False
    for idx, item in enumerate(items):
        if item.get("homework_key") == new_item.get("homework_key") and item.get("problem_index") == new_item.get("problem_index"):
            items[idx] = new_item
            found = True
            break
    if not found:
        items.append(new_item)
    save_homework_bank(items)
    return new_item


def build_knowledge_prompt(topic: str, difficulty: str, seed: Optional[Dict[str, Any]]) -> str:
    seed_context = ""
    if seed:
        seed_context = (
            f"【参考种子题目】\n"
            f"标题：{seed.get('title','')}\n"
            f"描述：{seed.get('content','')}\n"
            f"要求：请围绕其核心机制改写，不要照抄。"
        )

    return f"""你是一名专业的C语言数据结构与算法出题专家。请生成一道关于【{topic}】的【{difficulty}】难度编程题，并提供参考代码。

{seed_context}

输出要求：
1. 只输出 JSON
2. JSON 包含 `problem` 和 `standard_answer`
3. `problem` 为 Markdown 题面
4. `standard_answer` 为完整、可运行、带必要注释的 C 代码
"""


def generate_knowledge_pipeline(topic: str, difficulty: str, logger=None) -> Dict[str, Any]:
    retriever = LeetCodeRetriever(LEETCODE_DB_PATH)
    settings = load_admin_settings()
    llm = settings["llm"]
    client = build_batch_client(api_key=llm["api_key"], base_url=llm["base_url"])
    result = generate_full_problem_pipeline(
        retriever=retriever,
        topic=topic,
        difficulty=difficulty,
        client_instance=client,
        model_name=llm["model"],
        logger=logger,
    )
    if not result:
        raise ValueError("知识点题目生成失败，请检查模型配置或稍后重试")
    result["id"] = f"{topic}_{difficulty}_{int(time.time()*1000)}"
    return result


def generate_homework_pipeline(homework_key: str, problem_index: int, logger=None) -> Dict[str, Any]:
    homework_data = load_homework_data()
    homework_info = homework_data[homework_key]
    problem = homework_info["problems"][problem_index]
    problem_text = problem["description"]
    if logger:
        logger(f"开始生成作业题：{homework_key} / 第{problem_index + 1}题 / {problem.get('title','')}")

    if logger:
        logger("开始生成标准答案")
    standard_answer = call_llm([{"role": "user", "content": build_standard_answer_prompt(problem_text)}])
    if logger:
        logger("标准答案生成完成，开始生成思路")
    thought = call_llm(build_thought_messages(problem_text, standard_answer))
    if logger:
        logger("思路生成完成，开始生成代码框架")
    framework = call_llm([{"role": "user", "content": build_framework_prompt(problem_text, standard_answer, thought)}])
    helpers = {
        "extract_leaf_nodes_from_framework": extract_leaf_nodes_from_framework,
        "format_leaf_nodes_for_prompt": format_leaf_nodes_for_prompt,
        "redact_standard_answer": redact_standard_answer_for_completion,
    }
    if logger:
        logger("代码框架生成完成，开始生成伪代码")
    pseudocode = call_llm(build_pseudocode_messages(problem_text, standard_answer, thought, framework, helpers))
    if logger:
        logger("伪代码生成完成，开始生成代码补全")
    core = call_llm(build_core_messages(problem_text, standard_answer, thought, framework, pseudocode, helpers))
    if logger:
        logger("代码补全生成完成")

    return {
        "homework_key": homework_key,
        "homework_name": homework_info.get("name", homework_key),
        "problem_index": problem_index,
        "title": problem.get("title", ""),
        "problem": problem_text,
        "standard_answer": standard_answer,
        "modules": {
            "思路": thought,
            "框架": framework,
            "伪代码": pseudocode,
            "核心语句": core,
        },
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


def run_batch_job(job: Dict[str, Any], runner):
    job_id = job["id"]

    def _target():
        with BATCH_STATE["lock"]:
            BATCH_STATE["current_job_id"] = job_id
        update_job(job_id, status="running", started_at=time.strftime("%Y-%m-%d %H:%M:%S"))
        append_job_log(job_id, "任务开始执行")
        try:
            runner(job_id)
            update_job(job_id, status="completed", finished_at=time.strftime("%Y-%m-%d %H:%M:%S"))
            append_job_log(job_id, "任务执行完成")
        except Exception as e:
            update_job(job_id, status="failed", finished_at=time.strftime("%Y-%m-%d %H:%M:%S"))
            append_job_log(job_id, f"任务失败：{e}")
        finally:
            with BATCH_STATE["lock"]:
                if BATCH_STATE["current_job_id"] == job_id:
                    BATCH_STATE["current_job_id"] = None

    thread = threading.Thread(target=_target, daemon=True)
    thread.start()


def run_knowledge_batch(job_id: str, topic: str, difficulty: str, target_count: int):
    existing_items = [x for x in load_knowledge_bank() if x.get("topic") == topic and x.get("difficulty") == difficulty]
    current_count = len(existing_items)
    need = max(0, target_count - current_count)
    append_job_log(job_id, f"当前已有 {current_count} 道，目标 {target_count} 道，需要补 {need} 道")
    update_job(job_id, total=need, meta={**get_job(job_id).get("meta", {}), "current_count": current_count})
    if need == 0:
        append_job_log(job_id, "无需生成，已达到目标数量")
        return

    completed = 0
    failed = 0
    for i in range(need):
        append_job_log(job_id, f"开始生成第 {i + 1}/{need} 道")
        try:
            item = generate_knowledge_pipeline(topic, difficulty, logger=lambda msg: append_job_log(job_id, f"[知识点流水线] {msg}"))
            upsert_knowledge_item(item)
            completed += 1
            update_job(job_id, completed=completed, failed=failed)
            append_job_log(job_id, f"生成成功：{item.get('id')}")
        except Exception as e:
            failed += 1
            update_job(job_id, completed=completed, failed=failed)
            append_job_log(job_id, f"生成失败：{e}")


def run_homework_batch(job_id: str, homework_items: List[Dict[str, Any]]):
    total = len(homework_items)
    update_job(job_id, total=total)
    completed = 0
    failed = 0
    for idx, item in enumerate(homework_items, start=1):
        hk = item["homework_key"]
        pi = int(item["problem_index"])
        append_job_log(job_id, f"开始生成第 {idx}/{total} 题：{hk} / #{pi + 1}")
        try:
            result = generate_homework_pipeline(hk, pi, logger=lambda msg: append_job_log(job_id, f"[作业流水线] {msg}"))
            upsert_homework_item(result)
            completed += 1
            update_job(job_id, completed=completed, failed=failed)
            append_job_log(job_id, f"生成成功：{hk} / #{pi + 1}")
        except Exception as e:
            failed += 1
            update_job(job_id, completed=completed, failed=failed)
            append_job_log(job_id, f"生成失败：{hk} / #{pi + 1} / {e}")


def run_single_knowledge_job(job_id: str, topic: str, difficulty: str):
    update_job(job_id, total=1)
    append_job_log(job_id, "开始执行单题知识点生成")
    item = generate_knowledge_pipeline(topic, difficulty, logger=lambda msg: append_job_log(job_id, f"[知识点流水线] {msg}"))
    upsert_knowledge_item(item)
    update_job(job_id, completed=1)
    append_job_log(job_id, f"生成成功：{item.get('id')}")


def run_single_homework_job(job_id: str, homework_key: str, problem_index: int):
    update_job(job_id, total=1)
    append_job_log(job_id, "开始执行单题作业生成")
    item = generate_homework_pipeline(homework_key, int(problem_index), logger=lambda msg: append_job_log(job_id, f"[作业流水线] {msg}"))
    upsert_homework_item(item)
    update_job(job_id, completed=1)
    append_job_log(job_id, f"生成成功：{homework_key}/第{int(problem_index)+1}题")


@admin_bp.route("/admin")
def admin_page():
    return current_app.send_static_file("admin/index.html")


@admin_bp.route("/api/admin/session", methods=["GET"])
def admin_session():
    return jsonify({"authenticated": bool(session.get("admin_authenticated"))})


@admin_bp.route("/api/admin/login", methods=["POST"])
def admin_login():
    password = (request.json or {}).get("password", "")
    settings = load_admin_settings()
    if password != settings.get("admin_password"):
        return jsonify({"error": "密码错误"}), 401
    session["admin_authenticated"] = True
    return jsonify({"ok": True})


@admin_bp.route("/api/admin/logout", methods=["POST"])
@admin_required
def admin_logout():
    session.pop("admin_authenticated", None)
    return jsonify({"ok": True})


@admin_bp.route("/api/admin/settings", methods=["GET"])
@admin_required
def get_admin_settings():
    settings = load_admin_settings()
    return jsonify({
        "admin_password": settings.get("admin_password", ""),
        "llm": {
            "base_url": settings["llm"].get("base_url", ""),
            "api_key": settings["llm"].get("api_key", ""),
            "api_key_masked": mask_api_key(settings["llm"].get("api_key", "")),
            "model": settings["llm"].get("model", ""),
        }
    })


@admin_bp.route("/api/admin/settings", methods=["PUT"])
@admin_required
def update_admin_settings():
    data = request.json or {}
    llm = data.get("llm", {})
    settings = load_admin_settings()
    if data.get("admin_password"):
        settings["admin_password"] = data["admin_password"]
    settings["llm"].update({
        "base_url": llm.get("base_url", settings["llm"]["base_url"]),
        "api_key": llm.get("api_key", settings["llm"]["api_key"]),
        "model": llm.get("model", settings["llm"]["model"]),
    })
    save_admin_settings(settings)
    return jsonify({"ok": True})


@admin_bp.route("/api/admin/summary", methods=["GET"])
@admin_required
def admin_summary():
    homework_data = load_homework_data()
    knowledge_bank = load_knowledge_bank()
    homework_bank = load_homework_bank()
    return jsonify({
        "knowledge_count": len(knowledge_bank),
        "homework_generated_count": len(homework_bank),
        "current_job_id": BATCH_STATE["current_job_id"],
        "knowledge_topics": KNOWLEDGE_TOPIC_ORDER,
        "homework_catalog": [
            {
                "key": key,
                "name": value.get("name", key),
                "problem_count": len(value.get("problems", [])),
            }
            for key, value in homework_data.items()
        ],
    })


@admin_bp.route("/api/admin/knowledge/list", methods=["GET"])
@admin_required
def knowledge_list():
    topic = request.args.get("topic", "").strip()
    difficulty = request.args.get("difficulty", "").strip()
    items = load_knowledge_bank()
    if topic:
        items = [x for x in items if x.get("topic", "") == topic]
    if difficulty:
        items = [x for x in items if x.get("difficulty", "") == difficulty]
    simplified = [
        {
            "id": item.get("id"),
            "topic": item.get("topic", ""),
            "difficulty": item.get("difficulty", ""),
            "title": (item.get("problem", "").splitlines()[0] or "").replace("#", "").strip()[:80] if item.get("problem") else "",
            "preview": next((line.strip() for line in item.get("problem", "").splitlines() if line.strip() and not line.strip().startswith("#")), "")[:120],
        }
        for item in items
    ]
    return jsonify({"items": simplified})


@admin_bp.route("/api/admin/knowledge/item", methods=["GET"])
@admin_required
def knowledge_item():
    item_id = request.args.get("id", "")
    item = find_knowledge_item(item_id)
    if not item:
        return jsonify({"error": "题目不存在"}), 404
    return jsonify(item)


@admin_bp.route("/api/admin/knowledge/item", methods=["PUT"])
@admin_required
def update_knowledge_item():
    item = request.json or {}
    if not item.get("id"):
        return jsonify({"error": "缺少 id"}), 400
    upsert_knowledge_item(item)
    return jsonify({"ok": True})


@admin_bp.route("/api/admin/knowledge/generate", methods=["POST"])
@admin_required
def generate_knowledge():
    data = request.json or {}
    topic = data.get("topic", "").strip()
    difficulty = data.get("difficulty", "").strip()
    if not topic or not difficulty:
        return jsonify({"error": "缺少 topic 或 difficulty"}), 400
    job = create_job(
        job_type="knowledge_single",
        scope=f"知识点单题生成：{topic}/{difficulty}",
        total=1,
        meta={"topic": topic, "difficulty": difficulty},
    )
    run_batch_job(job, lambda job_id: run_single_knowledge_job(job_id, topic, difficulty))
    return jsonify({"job": serialize_job(job)})


@admin_bp.route("/api/admin/homework/list", methods=["GET"])
@admin_required
def homework_list():
    homework_key = request.args.get("homework_key", "").strip()
    homework_data = load_homework_data()
    bank_map = {
        (item.get("homework_key"), item.get("problem_index")): item
        for item in load_homework_bank()
    }
    items = []
    for key, info in homework_data.items():
        if homework_key and key != homework_key:
            continue
        for idx, problem in enumerate(info.get("problems", [])):
            existing = bank_map.get((key, idx))
            items.append({
                "homework_key": key,
                "homework_name": info.get("name", key),
                "problem_index": idx,
                "title": problem.get("title", ""),
                "generated": bool(existing),
            })
    return jsonify({"items": items})


@admin_bp.route("/api/admin/homework/item", methods=["GET"])
@admin_required
def homework_item():
    homework_key = request.args.get("homework_key", "")
    problem_index = request.args.get("problem_index", type=int)
    generated = find_homework_item(homework_key, problem_index)
    if generated:
        return jsonify(generated)

    homework_data = load_homework_data()
    if homework_key not in homework_data or problem_index is None or problem_index >= len(homework_data[homework_key]["problems"]):
        return jsonify({"error": "题目不存在"}), 404

    problem = homework_data[homework_key]["problems"][problem_index]
    return jsonify({
        "homework_key": homework_key,
        "homework_name": homework_data[homework_key].get("name", homework_key),
        "problem_index": problem_index,
        "title": problem.get("title", ""),
        "problem": problem.get("description", ""),
        "standard_answer": "",
        "modules": {"思路": "", "框架": "", "伪代码": "", "核心语句": ""},
    })


@admin_bp.route("/api/admin/homework/item", methods=["PUT"])
@admin_required
def update_homework_item():
    item = request.json or {}
    if item.get("homework_key") is None or item.get("problem_index") is None:
        return jsonify({"error": "缺少 homework_key 或 problem_index"}), 400
    upsert_homework_item(item)
    return jsonify({"ok": True})


@admin_bp.route("/api/admin/homework/generate", methods=["POST"])
@admin_required
def generate_homework():
    data = request.json or {}
    homework_key = data.get("homework_key", "")
    problem_index = data.get("problem_index")
    if homework_key == "" or problem_index is None:
        return jsonify({"error": "缺少 homework_key 或 problem_index"}), 400
    job = create_job(
        job_type="homework_single",
        scope=f"作业题单题生成：{homework_key}/第{int(problem_index)+1}题",
        total=1,
        meta={"homework_key": homework_key, "problem_index": int(problem_index)},
    )
    run_batch_job(job, lambda job_id: run_single_homework_job(job_id, homework_key, int(problem_index)))
    return jsonify({"job": serialize_job(job)})


@admin_bp.route("/api/admin/jobs", methods=["GET"])
@admin_required
def list_jobs():
    jobs = [serialize_job(job) for job in BATCH_STATE["jobs"][:50]]
    current_job = serialize_job(get_job(BATCH_STATE["current_job_id"])) if BATCH_STATE["current_job_id"] else None
    return jsonify({"current_job": current_job, "jobs": jobs})


@admin_bp.route("/api/admin/jobs/logs", methods=["GET"])
@admin_required
def job_logs():
    job_id = request.args.get("job_id", "")
    logs = BATCH_STATE["logs"].get(job_id, [])
    return jsonify({"job_id": job_id, "logs": logs[-200:]})


@admin_bp.route("/api/admin/jobs/knowledge-batch", methods=["POST"])
@admin_required
def create_knowledge_batch():
    if BATCH_STATE["current_job_id"]:
        return jsonify({"error": "当前已有批处理任务在运行"}), 409

    data = request.json or {}
    topic = data.get("topic", "").strip()
    difficulty = data.get("difficulty", "").strip()
    target_count = int(data.get("target_count", 0))
    if not topic or not difficulty or target_count <= 0:
        return jsonify({"error": "缺少 topic/difficulty/target_count"}), 400

    existing_count = len([x for x in load_knowledge_bank() if x.get("topic") == topic and x.get("difficulty") == difficulty])
    job = create_job(
        job_type="knowledge_batch",
        scope=f"知识点题批量生成：{topic}/{difficulty}",
        total=max(0, target_count - existing_count),
        meta={
            "topic": topic,
            "difficulty": difficulty,
            "target_count": target_count,
            "existing_count": existing_count,
        },
    )
    run_batch_job(job, lambda job_id: run_knowledge_batch(job_id, topic, difficulty, target_count))
    return jsonify({"job": serialize_job(job)})


@admin_bp.route("/api/admin/jobs/homework-batch", methods=["POST"])
@admin_required
def create_homework_batch():
    if BATCH_STATE["current_job_id"]:
        return jsonify({"error": "当前已有批处理任务在运行"}), 409

    data = request.json or {}
    items = data.get("items", [])
    valid_items = []
    for item in items:
        hk = item.get("homework_key")
        pi = item.get("problem_index")
        if hk is None or pi is None:
            continue
        valid_items.append({"homework_key": hk, "problem_index": int(pi)})
    if not valid_items:
        return jsonify({"error": "没有可生成的题目"}), 400

    job = create_job(
        job_type="homework_batch",
        scope=f"作业题批量生成：共 {len(valid_items)} 题",
        total=len(valid_items),
        meta={"items": valid_items},
    )
    run_batch_job(job, lambda job_id: run_homework_batch(job_id, valid_items))
    return jsonify({"job": serialize_job(job)})


bootstrap_batch_state()
