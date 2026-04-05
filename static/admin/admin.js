const state = {
    mode: 'knowledge',
    selectedKnowledgeId: null,
    selectedHomeworkKey: null,
    selectedProblemIndex: null,
    selectedJobId: null,
    homeworkCatalog: [],
    homeworkListItems: [],
    currentItem: null,
    pollTimer: null,
};

function $(id) { return document.getElementById(id); }

async function api(path, options = {}) {
    const res = await fetch(path, {
        credentials: 'include',
        headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
        ...options,
    });
    const text = await res.text();
    let data = {};
    try { data = text ? JSON.parse(text) : {}; } catch { data = { raw: text }; }
    if (!res.ok) {
        const raw = data.raw || '';
        const fallback = raw.includes('<!doctype html>') || raw.includes('<html')
            ? '服务端返回了非 JSON 错误，请检查模型配置或后端日志'
            : raw;
        throw new Error(data.error || fallback || `HTTP ${res.status}`);
    }
    return data;
}

function setStatus(id, text, isError = false) {
    const el = $(id);
    if (!el) return;
    el.textContent = text || '';
    el.style.color = isError ? '#b42318' : '#1d4ed8';
}

function clearEditor() {
    state.currentItem = null;
    $('editor-title').textContent = '请选择题目';
    $('modal-editor-meta').textContent = '';
    $('field-problem').value = '';
    $('field-answer').value = '';
    $('field-thought').value = '';
    $('field-framework').value = '';
    $('field-pseudocode').value = '';
    $('field-core').value = '';
}

function fillEditor(item) {
    state.currentItem = item;
    $('editor-title').textContent = item.title || item.id || '未命名题目';
    $('modal-editor-meta').textContent =
        state.mode === 'knowledge'
            ? `${item.topic || ''} / ${item.difficulty || ''} / ${item.id || ''}`
            : `${item.homework_name || ''} / 第 ${Number(item.problem_index) + 1} 题 / ${item.homework_key || ''}`;
    $('field-problem').value = item.problem || '';
    $('field-answer').value = item.standard_answer || '';
    $('field-thought').value = (item.modules || {})['思路'] || '';
    $('field-framework').value = (item.modules || {})['框架'] || '';
    $('field-pseudocode').value = (item.modules || {})['伪代码'] || '';
    $('field-core').value = (item.modules || {})['核心语句'] || '';
    $('editor-modal-wrap').classList.remove('hidden');
}

function currentPayload() {
    return {
        problem: $('field-problem').value,
        standard_answer: $('field-answer').value,
        modules: {
            '思路': $('field-thought').value,
            '框架': $('field-framework').value,
            '伪代码': $('field-pseudocode').value,
            '核心语句': $('field-core').value,
        }
    };
}

function switchMode(mode) {
    state.mode = mode;
    $('tab-knowledge').classList.toggle('active', mode === 'knowledge');
    $('tab-homework').classList.toggle('active', mode === 'homework');
    $('tab-knowledge').classList.toggle('secondary', mode !== 'knowledge');
    $('tab-homework').classList.toggle('secondary', mode !== 'homework');
    $('knowledge-controls').classList.toggle('hidden', mode !== 'knowledge');
    $('homework-controls').classList.toggle('hidden', mode !== 'homework');
    $('item-list').innerHTML = '';
    clearEditor();
    if (mode === 'knowledge') loadKnowledgeList();
    else loadHomeworkList();
}

function renderKnowledgeList(items) {
    const box = $('item-list');
    box.innerHTML = '';
    if (!items.length) {
        box.innerHTML = '<div class="muted" style="padding:12px;">当前 Tag 下还没有已生成题目。</div>';
        return;
    }
    items.forEach(item => {
        const div = document.createElement('div');
        div.className = 'list-item';
        if (state.selectedKnowledgeId === item.id) div.classList.add('active');
        const diffClass = item.difficulty === '简单' ? 'easy' : item.difficulty === '中等' ? 'medium' : 'hard';
        div.innerHTML = `
            <div class="list-item-title">${item.title || '未命名题目'}</div>
            <div class="list-item-subtitle">${item.preview || item.id || ''}</div>
            <div class="list-item-meta">
                <span class="pill ${diffClass}">${item.difficulty || ''}</span>
                <span class="muted">${item.id || ''}</span>
            </div>
        `;
        div.onclick = async () => {
            state.selectedKnowledgeId = item.id;
            await loadKnowledgeItem(item.id);
            renderKnowledgeList(items);
        };
        box.appendChild(div);
    });
}

function renderHomeworkList(items) {
    state.homeworkListItems = items;
    const box = $('item-list');
    box.innerHTML = '';
    const checkWrap = document.createElement('div');
    checkWrap.className = 'check-list';
    items.forEach(item => {
        const row = document.createElement('label');
        row.className = 'check-row';
        const checked = state.selectedHomeworkKey === item.homework_key && state.selectedProblemIndex === item.problem_index;
        row.innerHTML = `
            <input type="checkbox" class="homework-batch-checkbox" data-homework-key="${item.homework_key}" data-problem-index="${item.problem_index}" style="width:auto;">
            <div style="flex:1;">
                <div><strong>第 ${item.problem_index + 1} 题</strong>${item.generated ? '<span class="pill">已生成</span>' : ''}</div>
                <div class="muted">${item.title}</div>
            </div>
        `;
        row.onclick = async (e) => {
            if (e.target.type === 'checkbox') return;
            state.selectedHomeworkKey = item.homework_key;
            state.selectedProblemIndex = item.problem_index;
            await loadHomeworkItem(item.homework_key, item.problem_index);
            renderHomeworkList(items);
        };
        if (checked) row.style.border = '1px solid #1d4ed8';
        checkWrap.appendChild(row);
    });
    box.appendChild(checkWrap);
}

function renderJobList(currentJob, jobs) {
    $('current-job-box').innerHTML = currentJob
        ? `<strong>${currentJob.scope}</strong><br><span class="muted">${currentJob.status} / ${currentJob.completed || 0}/${currentJob.total || 0}</span>`
        : '当前没有运行中的任务';
    $('current-job-meta').textContent = currentJob ? formatJobMeta(currentJob) : '暂无任务详情';

    if (!state.selectedJobId && currentJob) state.selectedJobId = currentJob.id;
    if (!state.selectedJobId && jobs.length) state.selectedJobId = jobs[0].id;

    const box = $('job-list');
    box.innerHTML = '';
    jobs.forEach(job => {
        const div = document.createElement('div');
        div.className = 'job-item';
        if (state.selectedJobId === job.id) div.classList.add('active');
        div.innerHTML = `
            <strong>${job.scope}</strong>
            <div class="muted">${job.status} / 完成 ${job.completed || 0} / 失败 ${job.failed || 0} / 总数 ${job.total || 0}</div>
            <div class="muted">${job.created_at || ''}</div>
            <div class="muted">${formatJobMeta(job)}</div>
        `;
        div.onclick = async () => {
            state.selectedJobId = job.id;
            await loadJobLogs(job.id);
            renderJobList(currentJob, jobs);
        };
        box.appendChild(div);
    });
}

function formatJobMeta(job) {
    const meta = job.meta || {};
    if (job.type === 'knowledge_batch') {
        return `知识点 ${meta.topic || ''} / 难度 ${meta.difficulty || ''} / 目标 ${meta.target_count || 0} / 当前已有 ${meta.existing_count ?? meta.current_count ?? 0}`;
    }
    if (job.type === 'homework_batch') {
        const grouped = {};
        (meta.items || []).forEach(item => {
            const key = item.homework_key || '';
            if (!grouped[key]) grouped[key] = [];
            grouped[key].push(Number(item.problem_index) + 1);
        });
        return Object.entries(grouped).map(([key, nums]) => `${key}: 第${nums.join('、')}题`).join('；') || '无明细';
    }
    return '';
}

async function loadJobLogs(jobId) {
    if (!jobId) {
        $('terminal-box').textContent = '等待任务输出...';
        return;
    }
    try {
        const data = await api(`/api/admin/jobs/logs?job_id=${encodeURIComponent(jobId)}`);
        $('terminal-box').textContent = (data.logs || []).join('\n') || '暂无输出';
        $('terminal-box').scrollTop = $('terminal-box').scrollHeight;
    } catch (e) {
        $('terminal-box').textContent = e.message;
    }
}

async function refreshJobs() {
    try {
        const data = await api('/api/admin/jobs');
        renderJobList(data.current_job, data.jobs || []);
        await loadJobLogs(state.selectedJobId);
    } catch (e) {
        $('terminal-box').textContent = e.message;
    }
}

function startPolling() {
    if (state.pollTimer) clearInterval(state.pollTimer);
    state.pollTimer = setInterval(refreshJobs, 3000);
}

async function loadSession() {
    const data = await api('/api/admin/session');
    $('login-view').classList.toggle('hidden', data.authenticated);
    $('admin-view').classList.toggle('hidden', !data.authenticated);
    if (data.authenticated) {
        await loadSettings();
        await loadSummary();
        switchMode('knowledge');
        await refreshJobs();
        startPolling();
    }
}

async function login() {
    try {
        setStatus('login-status', '登录中...');
        await api('/api/admin/login', {
            method: 'POST',
            body: JSON.stringify({ password: $('login-password').value }),
        });
        $('login-password').value = '';
        setStatus('login-status', '');
        await loadSession();
    } catch (e) {
        setStatus('login-status', e.message, true);
    }
}

async function logout() {
    await api('/api/admin/logout', { method: 'POST' });
    location.reload();
}

async function loadSettings() {
    const data = await api('/api/admin/settings');
    $('base-url').value = data.llm.base_url || '';
    $('api-key').value = data.llm.api_key || '';
    $('model-name').value = data.llm.model || '';
    $('admin-password').value = '';
}

async function saveSettings() {
    try {
        setStatus('settings-status', '保存中...');
        await api('/api/admin/settings', {
            method: 'PUT',
            body: JSON.stringify({
                admin_password: $('admin-password').value,
                llm: {
                    base_url: $('base-url').value,
                    api_key: $('api-key').value,
                    model: $('model-name').value,
                }
            }),
        });
        $('admin-password').value = '';
        setStatus('settings-status', '已保存');
    } catch (e) {
        setStatus('settings-status', e.message, true);
    }
}

async function loadSummary() {
    const data = await api('/api/admin/summary');
    state.homeworkCatalog = data.homework_catalog || [];
    $('summary-box').innerHTML = `
        知识点题：${data.knowledge_count}<br>
        已生成作业题：${data.homework_generated_count}<br>
        作业集合：${state.homeworkCatalog.length}
    `;
    const select = $('homework-key');
    select.innerHTML = '';
    state.homeworkCatalog.forEach(item => {
        const opt = document.createElement('option');
        opt.value = item.key;
        opt.textContent = `${item.name} (${item.problem_count}题)`;
        select.appendChild(opt);
    });
    if (!state.selectedHomeworkKey && state.homeworkCatalog.length) {
        state.selectedHomeworkKey = state.homeworkCatalog[0].key;
        select.value = state.selectedHomeworkKey;
    } else if (state.selectedHomeworkKey) {
        select.value = state.selectedHomeworkKey;
    }
    const topicSelect = $('knowledge-topic');
    topicSelect.innerHTML = '<option value="">选择知识点 Tag</option>';
    (data.knowledge_topics || []).forEach(topic => {
        const opt = document.createElement('option');
        opt.value = topic;
        opt.textContent = topic;
        topicSelect.appendChild(opt);
    });
}

async function loadKnowledgeList() {
    try {
        const topic = $('knowledge-topic').value.trim();
        if (!topic) {
            $('item-list').innerHTML = '<div class="muted" style="padding:12px;">先选择一个知识点 Tag，再查看这个 Tag 下已生成的题目。</div>';
            setStatus('list-status', '未选择 Tag');
            return;
        }
        setStatus('list-status', '加载知识点题列表...');
        const difficulty = $('knowledge-difficulty').value;
        const query = new URLSearchParams();
        if (topic) query.set('topic', topic);
        if (difficulty) query.set('difficulty', difficulty);
        const data = await api(`/api/admin/knowledge/list?${query.toString()}`);
        renderKnowledgeList(data.items || []);
        setStatus('list-status', `${topic} 下共 ${data.items.length} 条${difficulty ? `（${difficulty}）` : ''}`);
    } catch (e) {
        setStatus('list-status', e.message, true);
    }
}

async function loadKnowledgeItem(id) {
    const item = await api(`/api/admin/knowledge/item?id=${encodeURIComponent(id)}`);
    fillEditor(item);
}

async function generateKnowledge() {
    try {
        const topic = $('knowledge-topic').value.trim();
        const difficulty = $('knowledge-difficulty').value;
        if (!topic || !difficulty) throw new Error('请先填写知识点和难度');
        setStatus('editor-status', '正在生成知识点题，请稍候...');
        const data = await api('/api/admin/knowledge/generate', {
            method: 'POST',
            body: JSON.stringify({ topic, difficulty }),
        });
        const item = data.item;
        state.selectedKnowledgeId = item.id;
        state.selectedJobId = data.job?.id || state.selectedJobId;
        $('knowledge-topic').value = item.topic || topic;
        $('knowledge-difficulty').value = item.difficulty || difficulty;
        fillEditor(item);
        await loadKnowledgeList();
        await refreshJobs();
        setStatus('editor-status', '知识点题生成完成');
    } catch (e) {
        setStatus('editor-status', e.message, true);
    }
}

async function createKnowledgeBatch() {
    try {
        const topic = $('knowledge-topic').value.trim();
        const difficulty = $('knowledge-difficulty').value;
        const targetCount = Number($('knowledge-target-count').value || 0);
        if (!topic || !difficulty || targetCount <= 0) throw new Error('请填写知识点、难度和目标数量');
        setStatus('editor-status', '正在创建知识点批任务...');
        await api('/api/admin/jobs/knowledge-batch', {
            method: 'POST',
            body: JSON.stringify({ topic, difficulty, target_count: targetCount }),
        });
        await refreshJobs();
        setStatus('editor-status', '知识点批任务已创建');
    } catch (e) {
        setStatus('editor-status', e.message, true);
    }
}

async function saveKnowledge() {
    if (!state.selectedKnowledgeId) throw new Error('当前没有选中的知识点题');
    const payload = {
        id: state.selectedKnowledgeId,
        topic: state.currentItem?.topic || $('knowledge-topic').value.trim(),
        difficulty: state.currentItem?.difficulty || $('knowledge-difficulty').value,
        title: state.currentItem?.title || $('editor-title').textContent,
        ...currentPayload()
    };
    await api('/api/admin/knowledge/item', { method: 'PUT', body: JSON.stringify(payload) });
}

async function loadHomeworkList() {
    try {
        setStatus('list-status', '加载作业题列表...');
        state.selectedHomeworkKey = $('homework-key').value;
        const data = await api(`/api/admin/homework/list?homework_key=${encodeURIComponent(state.selectedHomeworkKey || '')}`);
        renderHomeworkList(data.items || []);
        setStatus('list-status', `共 ${data.items.length} 条`);
    } catch (e) {
        setStatus('list-status', e.message, true);
    }
}

async function loadHomeworkItem(homeworkKey, problemIndex) {
    const item = await api(`/api/admin/homework/item?homework_key=${encodeURIComponent(homeworkKey)}&problem_index=${problemIndex}`);
    fillEditor(item);
}

async function generateHomework() {
    try {
        if (state.selectedProblemIndex == null) throw new Error('请先从列表选择一道作业题');
        setStatus('editor-status', '正在生成作业题教学资产，请稍候...');
        const data = await api('/api/admin/homework/generate', {
            method: 'POST',
            body: JSON.stringify({
                homework_key: state.selectedHomeworkKey,
                problem_index: state.selectedProblemIndex,
            }),
        });
        const item = data.item;
        state.selectedJobId = data.job?.id || state.selectedJobId;
        fillEditor(item);
        await loadHomeworkList();
        await refreshJobs();
        setStatus('editor-status', '作业题生成完成');
    } catch (e) {
        setStatus('editor-status', e.message, true);
    }
}

function getCheckedHomeworkItems() {
    return Array.from(document.querySelectorAll('.homework-batch-checkbox:checked')).map(el => ({
        homework_key: el.dataset.homeworkKey,
        problem_index: Number(el.dataset.problemIndex),
    }));
}

async function createHomeworkBatch() {
    try {
        const items = getCheckedHomeworkItems();
        if (!items.length) throw new Error('请先勾选要生成的作业题');
        setStatus('editor-status', '正在创建作业批任务...');
        await api('/api/admin/jobs/homework-batch', {
            method: 'POST',
            body: JSON.stringify({ items }),
        });
        await refreshJobs();
        setStatus('editor-status', '作业批任务已创建');
    } catch (e) {
        setStatus('editor-status', e.message, true);
    }
}

async function saveHomework() {
    if (state.selectedHomeworkKey == null || state.selectedProblemIndex == null) throw new Error('当前没有选中的作业题');
    const payload = {
        homework_key: state.selectedHomeworkKey,
        problem_index: state.selectedProblemIndex,
        homework_name: state.currentItem?.homework_name || state.homeworkCatalog.find(x => x.key === state.selectedHomeworkKey)?.name || '',
        title: state.currentItem?.title || $('editor-title').textContent,
        ...currentPayload()
    };
    await api('/api/admin/homework/item', { method: 'PUT', body: JSON.stringify(payload) });
}

async function saveCurrentItem() {
    try {
        setStatus('editor-status', '保存中...');
        if (state.mode === 'knowledge') await saveKnowledge();
        else await saveHomework();
        setStatus('editor-status', '保存成功');
    } catch (e) {
        setStatus('editor-status', e.message, true);
    }
}

async function regenerateCurrentItem() {
    if (state.mode === 'knowledge') await generateKnowledge();
    else await generateHomework();
}

window.addEventListener('DOMContentLoaded', async () => {
    $('login-btn').onclick = login;
    $('logout-btn').onclick = logout;
    $('save-settings-btn').onclick = saveSettings;
    $('tab-knowledge').onclick = () => switchMode('knowledge');
    $('tab-homework').onclick = () => switchMode('homework');
    $('knowledge-refresh-btn').onclick = loadKnowledgeList;
    $('homework-refresh-btn').onclick = loadHomeworkList;
    $('knowledge-generate-btn').onclick = generateKnowledge;
    $('knowledge-batch-btn').onclick = createKnowledgeBatch;
    $('homework-batch-btn').onclick = createHomeworkBatch;
    $('save-item-btn').onclick = saveCurrentItem;
    $('generate-item-btn').onclick = regenerateCurrentItem;
    $('homework-key').onchange = loadHomeworkList;
    $('knowledge-topic').onchange = loadKnowledgeList;
    $('knowledge-difficulty').onchange = () => {
        if ($('knowledge-topic').value) loadKnowledgeList();
    };
    $('close-editor-modal').onclick = () => $('editor-modal-wrap').classList.add('hidden');
    $('editor-modal-wrap').onclick = (e) => {
        if (e.target === $('editor-modal-wrap')) $('editor-modal-wrap').classList.add('hidden');
    };
    $('login-password').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') login();
    });
    await loadSession();
});
