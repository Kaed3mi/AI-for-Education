function preprocessMath(text) {
    // 直接替换所有可能的LaTeX分隔符模式
    let processedText = text;

    // 处理 \\( ... \\) 模式
    processedText = processedText.replace(/\\\\\(/g, '$');
    processedText = processedText.replace(/\\\\\)/g, '$');

    // 处理 \\[ ... \\] 模式
    processedText = processedText.replace(/\\\\\[/g, '$$');
    processedText = processedText.replace(/\\\\\]/g, '$$');

    // 处理 \( ... \) 模式
    processedText = processedText.replace(/\\\(/g, '$');
    processedText = processedText.replace(/\\\)/g, '$');

    // 处理 \[ ... \] 模式
    processedText = processedText.replace(/\\\[/g, '$$');
    processedText = processedText.replace(/\\\]/g, '$$');

    return processedText;
}

// 配置marked选项
marked.setOptions({
    breaks: true,
    gfm: true
});

// Mermaid图表渲染函数
async function renderMermaidDiagrams(container) {
    // 查找所有mermaid代码块
    const mermaidBlocks = container.querySelectorAll('pre code.language-mermaid');
    
    for (let i = 0; i < mermaidBlocks.length; i++) {
        const block = mermaidBlocks[i];
        const code = block.textContent;
        const pre = block.parentElement;
        
        // 创建一个新的div来放置渲染后的图表
        const mermaidDiv = document.createElement('div');
        mermaidDiv.className = 'mermaid-diagram';
        
        try {
            // 生成唯一ID
            const id = `mermaid-${Date.now()}-${i}`;
            // 渲染Mermaid图表
            const { svg } = await mermaid.render(id, code);
            mermaidDiv.innerHTML = svg;
            // 替换原来的pre元素
            pre.parentNode.replaceChild(mermaidDiv, pre);
        } catch (error) {
            console.error('Mermaid渲染错误:', error);
            mermaidDiv.innerHTML = `<p style="color: red;">图表渲染失败: ${error.message}</p>`;
            mermaidDiv.innerHTML += `<pre><code>${code}</code></pre>`;
            pre.parentNode.replaceChild(mermaidDiv, pre);
        }
    }
    
    // 同时处理直接的mermaid类div（如果有的话）
    const mermaidDivs = container.querySelectorAll('.mermaid:not(.mermaid-diagram)');
    for (let i = 0; i < mermaidDivs.length; i++) {
        const div = mermaidDivs[i];
        const code = div.textContent;
        
        try {
            const id = `mermaid-div-${Date.now()}-${i}`;
            const { svg } = await mermaid.render(id, code);
            div.innerHTML = svg;
            div.classList.add('mermaid-diagram');
        } catch (error) {
            console.error('Mermaid渲染错误:', error);
        }
    }
}

// 页面切换功能
function switchPage(page) {
    // 隐藏所有页面
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));

    // 显示选中的页面
    document.getElementById(page + '-page').classList.add('active');

    // 设置激活的导航按钮
    const navButtons = document.querySelectorAll('.nav-btn');
    navButtons.forEach(btn => {
        if (btn.getAttribute('onclick').includes(page)) {
            btn.classList.add('active');
        }
    });

    // 如果切换到智能助教页面，初始化会话
    if (page === 'intelligent-tutor') {
        initTutorSession();
    }
    
    // 如果切换到小航辅导页面，初始化知识点网格
    if (page === 'xiaohang') {
        if (typeof xiaohangInitKnowledgeGrid === 'function') {
            xiaohangInitKnowledgeGrid();
        }
    }
}

// 编程助教功能
// 页面刷新时生成新的session_id和清理对话历史
let sessionId = Math.random().toString(36).substring(2, 15);
const userId = 'web_user_' + Math.random().toString(36).substring(2, 7);
let isProcessing = false;
let selectedLanguage = 'C'; // 默认选择C语言
let selectedModel = 'coder480b'; // 默认选择 coder480b
let selectedGeneratorModel = 'coder480b'; // 智能出题默认选择 coder480b

// 页面加载时重置对话历史
function resetConversationOnPageLoad() {
    console.log('重置对话历史 - 开始');
    
    // 生成新的session_id
    const oldSessionId = sessionId;
    sessionId = Math.random().toString(36).substring(2, 15);
    console.log('Session ID 更新:', oldSessionId, '->', sessionId);
    
    // 清空对话历史
    conversationHistory = [];
    console.log('对话历史已清空');
    
    // 清空输出区域
    const outputArea = document.getElementById('output');
    if (outputArea) {
        outputArea.innerHTML = '';
        console.log('输出区域已清空');
    }
    
    // 重置当前阶段显示
    const currentStage = document.getElementById('current-stage');
    if (currentStage) {
        currentStage.textContent = '等待输入...';
        console.log('当前阶段显示已重置');
    }
    
    // 清空问题输入框
    const questionInput = document.getElementById('question-input');
    if (questionInput) {
        questionInput.value = '';
        console.log('问题输入框已清空');
    }
    
    // 清空参考答案输入框
    const referenceInput = document.getElementById('reference-input');
    if (referenceInput) {
        referenceInput.value = '';
        console.log('参考答案输入框已清空');
    }
    
    console.log('重置对话历史 - 完成');
}

// 语言选择功能
function selectLanguage(language) {
    selectedLanguage = language;
    
    // 更新按钮状态 - 只针对语言按钮
    document.getElementById('btn-c').classList.remove('active');
    document.getElementById('btn-python').classList.remove('active');
    
    if (language === 'C') {
        document.getElementById('btn-c').classList.add('active');
    } else if (language === 'Python') {
        document.getElementById('btn-python').classList.add('active');
    }
    
    console.log('选择的编程语言:', selectedLanguage);
}

// 模型选择功能
function selectModel(model) {
    selectedModel = model;
    
    // 更新按钮状态
    document.getElementById('btn-model-480b').classList.remove('active');
    document.getElementById('btn-model-loopcoder').classList.remove('active');
    
    if (model === 'coder480b') {
        document.getElementById('btn-model-480b').classList.add('active');
    } else if (model === 'loopcoder') {
        document.getElementById('btn-model-loopcoder').classList.add('active');
    }
    
    console.log('选择的模型:', selectedModel);
}

// 智能出题模型选择功能
function selectGeneratorModel(model) {
    selectedGeneratorModel = model;
    
    // 更新按钮状态
    document.getElementById('btn-gen-model-480b').classList.remove('active');
    document.getElementById('btn-gen-model-loopcoder').classList.remove('active');
    
    if (model === 'coder480b') {
        document.getElementById('btn-gen-model-480b').classList.add('active');
    } else if (model === 'loopcoder') {
        document.getElementById('btn-gen-model-loopcoder').classList.add('active');
    }
    
    console.log('智能出题选择的模型:', selectedGeneratorModel);
}

// 切换参考答案区域显示/隐藏
function toggleReference() {
    const textarea = document.getElementById('reference-input');
    const button = document.getElementById('reference-lock-btn');
    
    if (textarea.style.display === 'none') {
        textarea.style.display = 'block';
        button.innerHTML = '🔓 展开';
        button.title = '收起参考答案区域';
        button.style.cursor = 'pointer';
        button.style.opacity = '1';
    } else {
        textarea.style.display = 'none';
        button.innerHTML = '🔒 暂时锁定';
        button.title = '功能暂时锁定';
        button.style.cursor = 'not-allowed';
        button.style.opacity = '0.7';
    }
}

// 在askQuestion函数中
// 存储对话历史的数组
let conversationHistory = [];

async function askQuestion(stage) {
    if (isProcessing) return;

    const questionInput = document.getElementById('question-input');
    const referenceInput = document.getElementById('reference-input');
    const outputArea = document.getElementById('output');
    const currentStage = document.getElementById('current-stage');
    const loadingIndicator = document.getElementById('loading-indicator');
    const buttons = document.querySelectorAll('.button-group button');

    const question = questionInput.value.trim();
    if (!question) {
        alert('请输入编程问题！');
        return;
    }

    // 禁用所有按钮并显示加载指示器
    isProcessing = true;
    buttons.forEach(btn => btn.disabled = true);
    loadingIndicator.style.display = 'inline-block';
    currentStage.textContent = `正在生成${stage}...`;
    outputArea.innerHTML = '';

    // 将用户问题添加到历史记录
    conversationHistory.push({
        role: 'user',
        content: question,
        stage: stage,
        timestamp: new Date().toISOString()
    });

    try {
        const response = await fetch('/api/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify({
                question: question,
                stage: stage,
                user_id: userId,
                session_id: sessionId,
                reference_answer: stage === '核心语句' ? referenceInput.value : '',
                language: selectedLanguage, // 添加语言参数
                model: selectedModel, // 添加模型参数
                history: conversationHistory.slice(-10) // 发送最近10条历史记录
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let markdown = '';
        let assistantResponse = '';
        const output = document.getElementById('output'); // 确保output在循环外定义

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const text = decoder.decode(value, { stream: true });
            markdown += text;
            assistantResponse += text;
            // 预处理数学公式后再转换为HTML
            const preprocessedMarkdown = preprocessMath(markdown);
            output.innerHTML = marked.parse(preprocessedMarkdown);

            // 重新渲染数学公式
            if (window.MathJax) {
                MathJax.typesetPromise([outputArea]).catch((err) => console.log(err.message));
            }
            
            // 渲染Mermaid图表
            if (window.mermaid) {
                renderMermaidDiagrams(outputArea);
            }

            outputArea.scrollTop = outputArea.scrollHeight; // 自动滚动到底部
        }

        // 将AI回复添加到历史记录
        conversationHistory.push({
            role: 'assistant',
            content: assistantResponse,
            stage: stage,
            timestamp: new Date().toISOString()
        });

        // 保持历史记录在合理范围内（最多20条）
        if (conversationHistory.length > 20) {
            conversationHistory = conversationHistory.slice(-20);
        }

    } catch (error) {
        console.error('Error:', error);
        outputArea.innerHTML = `<p>发生错误: ${error.message}</p>`;
    } finally {
        // 恢复按钮状态并隐藏加载指示器
        isProcessing = false;
        buttons.forEach(btn => btn.disabled = false);
        loadingIndicator.style.display = 'none';
        currentStage.textContent = `${stage}结果`;
    }
}

// 获取选中的知识点
function getSelectedTopics() {
    const topics = [];
    const checkboxes = document.querySelectorAll('.checkbox-item input[type="checkbox"]:checked');
    checkboxes.forEach(checkbox => {
        topics.push(checkbox.value);
    });
    return topics;
}

// 智能出题功能
let isGenerating = false;

// 切换答案显示状态
function toggleAnswer() {
    const answerDiv = document.getElementById('answer-output');
    if (answerDiv.style.display === 'none') {
        answerDiv.style.display = 'block';
    } else {
        answerDiv.style.display = 'none';
    }
}

// 在generateQuestions函数中
async function generateQuestions() {
    const questionType = document.getElementById('question-type').value;
    const difficulty = document.getElementById('difficulty').value;
    // 获取选中的知识点（单选）
    const selectedTag = document.querySelector('input[name="knowledge-tag"]:checked');
    const tag = selectedTag ? selectedTag.value : "Array"; // 默认 Array

    const generateBtn = document.getElementById('generate-btn');
    const output = document.getElementById('questions-output');
    const answerSection = document.getElementById('answer-section');
    const answerOutput = document.getElementById('answer-output');

    generateBtn.disabled = true;
    generateBtn.textContent = '生成中...';
    output.innerHTML = '<p>正在生成题目，请稍候...</p>';
    answerSection.style.display = 'none'; // 隐藏答案区域
    answerOutput.innerHTML = '';

    try {
        const response = await fetch('/api/xiaohang_integration/generate_problem', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({
                tag: tag,
                difficulty: difficulty,
                problem_type: questionType,
                model: selectedGeneratorModel
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const text = await response.text();
        let data;
        try {
            data = JSON.parse(text);
        } catch (e) {
            console.error("Failed to parse JSON:", text);
            // 兼容可能返回 Markdown 文本的情况
            if (text.trim().startsWith('#') || text.trim().startsWith('##')) {
                 output.innerHTML = marked.parse(text);
                 answerSection.style.display = 'none'; // 这种情况下没有分离的答案
                 return;
            }
            throw new Error(`Invalid JSON response: ${text.substring(0, 50)}...`);
        }

        if (data.error) {
            output.innerHTML = `<p style="color: red;">错误: ${data.error}</p>`;
        } else {
            // 渲染题目
            let problemContent = `### ${data.title}\n\n`;
            problemContent += `${data.problem}`;
            output.innerHTML = marked.parse(problemContent);
            
            // 渲染答案
            let answerContent = "";
            if (typeof data.answer === 'object') {
                // 如果是 JSON 对象（如性能分析）
                for (const [key, value] of Object.entries(data.answer)) {
                    answerContent += `**${key}**: ${value}\n\n`;
                }
            } else {
                answerContent = data.answer;
            }
            answerOutput.innerHTML = marked.parse(answerContent);
            
            // 显示答案切换按钮
            answerSection.style.display = 'block';

            // 重新渲染数学公式和Mermaid
            if (window.MathJax) {
                MathJax.typesetPromise([output, answerOutput]).catch((err) => console.log(err.message));
            }
            if (window.mermaid) {
                renderMermaidDiagrams(output);
                renderMermaidDiagrams(answerOutput);
            }
        }

    } catch (error) {
        console.error('Error:', error);
        output.innerHTML = `<p>发生错误: ${error.message}</p>`;
    } finally {
        generateBtn.disabled = false;
        generateBtn.textContent = '生成题目';
    }
}

// 导出题目功能
function exportQuestions() {
    const outputArea = document.getElementById('questions-output');
    const questionType = document.getElementById('question-type').value;
    const difficulty = document.getElementById('difficulty').value;
    const questionCount = document.getElementById('question-count').value;

    // 获取选中的知识点
    const knowledgePoints = [];
    const checkboxes = document.querySelectorAll('.checkbox-item input[type="checkbox"]:checked');
    checkboxes.forEach(checkbox => {
        knowledgePoints.push(checkbox.value);
    });

    if (!outputArea.innerHTML || outputArea.innerHTML.includes('点击"生成题目"按钮开始出题') || outputArea.innerHTML.includes('正在生成题目')) {
        alert('没有可导出的题目内容！');
        return;
    }

    // 获取纯文本内容（去除HTML标签）
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = outputArea.innerHTML;
    let textContent = tempDiv.textContent || tempDiv.innerText || '';

    // 添加题目信息头部
    const header = `数据结构题目\n` +
        `题目类型: ${getTypeText(questionType)}\n` +
        `难度等级: ${getDifficultyText(difficulty)}\n` +
        `题目数量: ${questionCount}\n` +
        `知识点: ${knowledgePoints.join(', ')}\n` +
        `生成时间: ${new Date().toLocaleString()}\n` +
        `${'='.repeat(50)}\n\n`;

    const fullContent = header + textContent;

    // 创建下载链接
    const blob = new Blob([fullContent], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `数据结构题目_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// 辅助函数：获取题目类型文本
function getTypeText(type) {
    const typeMap = {
        'choice': '选择题',
        'judge': '判断题',
        'fill': '填空题',
        'programming': '编程题',
        'mixed': '混合题型'
    };
    return typeMap[type] || type;
}

// 辅助函数：获取难度等级文本
function getDifficultyText(difficulty) {
    const difficultyMap = {
        'easy': '简单',
        'medium': '中等',
        'hard': '困难',
        'mixed': '混合难度'
    };
    return difficultyMap[difficulty] || difficulty;
}

// 生成测试点函数
function generateTestcases() {
    const problemDescription = document.getElementById('problem-description').value;
    const code = document.getElementById('code-input').value;
    const testInput = document.getElementById('test-input').value;
    const outputDiv = document.getElementById('testcase-output');
    const loadingIndicator = document.getElementById('loading-indicator-testcase');
    const exportBtn = document.getElementById('export-testcase-btn');

    if (!code.trim()) {
        alert('请输入参考代码！');
        return;
    }

    // 显示加载状态
    loadingIndicator.style.display = 'inline-block';
    outputDiv.innerHTML = '';
    exportBtn.style.display = 'none';

    // 发送请求到后端
    fetch('/api/generate_testcases', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
            problem_description: problemDescription,
            code: code,
            test_input: testInput
        })
    })
        .then(response => {
            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            function readStream() {
                reader.read().then(({ done, value }) => {
                    if (done) {
                        loadingIndicator.style.display = 'none';
                        exportBtn.style.display = 'inline-block';
                        return;
                    }

                    const chunk = decoder.decode(value);
                    outputDiv.innerHTML += chunk;

                    // 解析Markdown
                    // 解析Markdown
                    outputDiv.innerHTML = marked.parse(outputDiv.textContent || outputDiv.innerText || '');

                    // 删除这里的代码高亮调用
                    // outputDiv.querySelectorAll('pre code').forEach((block) => {
                    //     hljs.highlightElement(block);
                    // });

                    readStream();
                });
            }

            readStream();
        })
        .catch(error => {
            console.error('Error:', error);
            loadingIndicator.style.display = 'none';
            outputDiv.innerHTML = '<p style="color: red;">生成测试点时发生错误，请重试。</p>';
        });
}

// 智能生成测试点函数 (使用 generator_kit)
async function generateProblemTestcases() {
    const problemDescription = document.getElementById('problem-description').value;
    const count = document.getElementById('testcase-count').value;
    const outputDiv = document.getElementById('testcase-output');
    const loadingIndicator = document.getElementById('loading-indicator-testcase');
    const exportBtn = document.getElementById('export-testcase-btn');

    if (!problemDescription.trim()) {
        alert('请输入问题描述！');
        return;
    }

    // 显示加载状态
    loadingIndicator.style.display = 'inline-block';
    outputDiv.innerHTML = '';
    exportBtn.style.display = 'none';

    try {
        const response = await fetch('/api/generate_problem_testcases', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                problem_description: problemDescription,
                count: parseInt(count)
            })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let markdown = '';
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value, { stream: true });
            markdown += chunk;
            outputDiv.innerHTML = marked.parse(markdown);
            outputDiv.scrollTop = outputDiv.scrollHeight;
        }

        exportBtn.style.display = 'inline-block';
    } catch (error) {
        console.error('Error:', error);
        outputDiv.innerHTML += `<p style="color: red;">发生错误: ${error.message}</p>`;
    } finally {
        loadingIndicator.style.display = 'none';
    }
}

// 导出测试点函数
function exportTestcases() {
    const outputDiv = document.getElementById('testcase-output');
    const problemDescription = document.getElementById('problem-description').value;
    const testInput = document.getElementById('test-input').value;

    if (!outputDiv.textContent.trim()) {
        alert('没有可导出的测试点！');
        return;
    }

    // 获取当前时间
    const now = new Date();
    const timestamp = now.toLocaleString('zh-CN');

    // 构建导出内容
    let exportContent = `测试点导出\n`;
    exportContent += `导出时间：${timestamp}\n`;
    exportContent += `问题描述：${problemDescription || '无'}\n`;
    exportContent += `测试输入：${testInput || '无'}\n`;
    exportContent += `\n===================\n\n`;
    exportContent += outputDiv.textContent || outputDiv.innerText || '';

    // 创建下载链接
    const blob = new Blob([exportContent], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `测试点_${now.getFullYear()}${(now.getMonth() + 1).toString().padStart(2, '0')}${now.getDate().toString().padStart(2, '0')}_${now.getHours().toString().padStart(2, '0')}}${now.getMinutes().toString().padStart(2, '0')}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// 智能出卷功能
function generateExam() {
    const generateBtn = document.getElementById('generate-exam-btn');
    const loadingIndicator = document.getElementById('loading-indicator-exam');
    const outputArea = document.getElementById('exam-output');

    // 显示加载状态
    generateBtn.disabled = true;
    loadingIndicator.style.display = 'inline-block';
    outputArea.innerHTML = '';

    let accumulatedContent = '';

    fetch('/api/generate_exam', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        credentials: 'include'
    })
        .then(response => {
            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            function readStream() {
                return reader.read().then(({ done, value }) => {
                    if (done) {
                        // 流结束，进行最终渲染
                        outputArea.innerHTML = marked.parse(accumulatedContent);

                        // 重新渲染数学公式
                        if (window.MathJax) {
                            MathJax.typesetPromise([outputArea]).catch((err) => console.log(err.message));
                        }

                        // 滚动到底部
                        outputArea.scrollTop = outputArea.scrollHeight;

                        generateBtn.disabled = false;
                        loadingIndicator.style.display = 'none';
                        return;
                    }

                    const chunk = decoder.decode(value, { stream: true });
                    accumulatedContent += chunk;
                    // 预处理数学公式后再实时渲染累积的内容
                    const preprocessedContent = preprocessMath(accumulatedContent);
                    outputArea.innerHTML = marked.parse(preprocessedContent);

                    // 重新渲染数学公式
                    if (window.MathJax) {
                        MathJax.typesetPromise([outputArea]).catch((err) => console.log(err.message));
                    }

                    // 自动滚动
                    outputArea.scrollTop = outputArea.scrollHeight;

                    return readStream();
                });
            }

            return readStream();
        })
        .catch(error => {
            console.error('Error:', error);
            outputArea.innerHTML = '<p style="color: red;">生成试卷时发生错误，请重试。</p>';
            generateBtn.disabled = false;
            loadingIndicator.style.display = 'none';
        });
}

// 导出试卷功能
function exportExam() {
    const examContent = document.getElementById('exam-output').innerText;
    if (!examContent || examContent.includes('点击"生成试卷"按钮开始出卷')) {
        alert('请先生成试卷再导出！');
        return;
    }

    const blob = new Blob([examContent], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `C语言数据结构试卷_${new Date().toISOString().slice(0, 10)}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// 替换MathJax渲染函数
function renderMath(element) {
    if (window.renderMathInElement) {
        renderMathInElement(element, {
            delimiters: [
                { left: '$$', right: '$$', display: true },
                { left: '$', right: '$', display: false },
                { left: '\\(', right: '\\)', display: false },
                { left: '\\[', right: '\\]', display: true }
            ],
            throwOnError: false
        });
    }
}

// 智能助教功能
let currentMode = 'question'; // 默认为问题模式

// 初始化智能助教会话
async function initTutorSession() {
    const chatHistory = document.getElementById('tutor-chat-history');
    chatHistory.innerHTML = '';

    try {
        const response = await fetch('/api/tutor/init', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let markdown = '';

        // 添加AI消息气泡
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant';
        chatHistory.appendChild(messageDiv);

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const text = decoder.decode(value, { stream: true });
            markdown += text;
            messageDiv.innerHTML = marked.parse(markdown);
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }
    } catch (error) {
        console.error('Error:', error);
        const errorDiv = document.createElement('div');
        errorDiv.className = 'message assistant';
        errorDiv.innerHTML = `<p>发生错误: ${error.message}</p>`;
        chatHistory.appendChild(errorDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
}

// 发送消息到智能助教
async function sendTutorMessage() {
    const userInput = document.getElementById('tutor-user-input');
    const message = userInput.value.trim();

    if (!message) {
        alert('请输入消息！');
        return;
    }

    const chatHistory = document.getElementById('tutor-chat-history');

    // 添加用户消息到聊天历史
    const userMessageDiv = document.createElement('div');
    userMessageDiv.className = 'message user';
    userMessageDiv.textContent = message;
    chatHistory.appendChild(userMessageDiv);

    // 清空输入框
    userInput.value = '';

    // 滚动到底部
    chatHistory.scrollTop = chatHistory.scrollHeight;

    try {
        let response = await fetch('/api/tutor/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                type: currentMode // 'question' 或 'code'
            }),
            credentials: 'include'
        });
        // 若会话未初始化导致 400，则自动初始化并重试一次
        if (response.status === 400) {
            await initTutorSession();
            response = await fetch('/api/tutor/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    type: currentMode
                }),
                credentials: 'include'
            });
        }

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let markdown = '';

        // 添加AI消息气泡
        const aiMessageDiv = document.createElement('div');
        aiMessageDiv.className = 'message assistant';
        chatHistory.appendChild(aiMessageDiv);

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const text = decoder.decode(value, { stream: true });
            markdown += text;

            // 检查是否包含评估结果标记
            const assessmentRegex = /\[评估结果:([^\]]+)\]/;
            const assessmentMatch = markdown.match(assessmentRegex);

            if (assessmentMatch) {
                // 如果有评估结果，创建专门的评估消息
                const assessmentDiv = document.createElement('div');
                assessmentDiv.className = 'message assessment';
                assessmentDiv.textContent = `掌握程度评估: ${assessmentMatch[1]}`;
                chatHistory.appendChild(assessmentDiv);

                // 移除原始文本中的评估标记
                markdown = markdown.replace(assessmentRegex, '');
            }

            // 更新AI消息内容
            aiMessageDiv.innerHTML = marked.parse(markdown);
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }
    } catch (error) {
        console.error('Error:', error);
        const errorDiv = document.createElement('div');
        errorDiv.className = 'message assistant';
        errorDiv.innerHTML = `<p>发生错误: ${error.message}</p>`;
        chatHistory.appendChild(errorDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
}

// 切换输入模式（问题/代码）
function switchMode(mode) {
    currentMode = mode;

    // 更新按钮状态
    document.getElementById('question-mode-btn').classList.toggle('active', mode === 'question');
    document.getElementById('code-mode-btn').classList.toggle('active', mode === 'code');

    // 更新输入框提示
    const userInput = document.getElementById('tutor-user-input');
    if (mode === 'code') {
        userInput.placeholder = '请粘贴你的C语言代码...';
    } else {
        userInput.placeholder = '请输入你的问题...';
    }
}

// 重置智能助教会话
async function resetTutorSession() {
    try {
        const response = await fetch('/api/tutor/reset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // 重新初始化会话
        initTutorSession();
    } catch (error) {
        console.error('Error:', error);
        alert('重置会话时发生错误: ' + error.message);
    }
}

// 添加回车发送消息功能
document.addEventListener('DOMContentLoaded', function () {
    // 页面加载时重置对话历史
    resetConversationOnPageLoad();
    
    // 默认显示编程助教页面
    switchPage('tutor');
    
    // 初始化语言选择，默认选择C语言
    selectLanguage('C');
    // 初始化模型选择，默认选择coder480b
    selectModel('coder480b');
    // 初始化智能出题模型选择，默认选择coder480b
    selectGeneratorModel('coder480b');
    
    const userInput = document.getElementById('tutor-user-input');
    if (userInput) {
        userInput.addEventListener('keydown', function (e) {
            // 如果按下Ctrl+Enter，添加换行
            if (e.key === 'Enter' && e.ctrlKey) {
                const start = this.selectionStart;
                const end = this.selectionEnd;
                this.value = this.value.substring(0, start) + '\n' + this.value.substring(end);
                this.selectionStart = this.selectionEnd = start + 1;
                e.preventDefault();
            }
            // 如果只按下Enter，发送消息
            else if (e.key === 'Enter' && !e.ctrlKey) {
                sendTutorMessage();
                e.preventDefault();
            }
        });
    }
});