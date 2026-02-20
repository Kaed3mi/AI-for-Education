// 编程教学 Agent - 前端应用

class AgentApp {
    constructor() {
        this.currentAgent = 'core_teaching';
        // this.currentMode = 'knowledge_learning'; // Deprecated
        this.sessionId = null;
        this.messageCount = 0;
        this.isStreaming = false;
        this.currentMessageElement = null;

        // Agent 配置
        this.agentConfig = {
            feynman: {
                icon: '📚',
                title: '费曼学习法导师',
                description: '帮你深入理解复杂的编程概念'
            },
            reverse_turing: {
                icon: '🎯',
                title: '编程思维评估专家',
                description: '评估你的编程思维能力'
            },
            socratic: {
                icon: '💡',
                title: '苏格拉底式导师',
                description: '引导你自己找到代码问题'
            },
            core_teaching: {
                icon: '📖',
                title: '知识点学习',
                description: '循序渐进掌握核心概念'
            },
            error_analysis: {
                icon: '🐛',
                title: '错误代码分析',
                description: '识别并修复代码陷阱'
            }
        };

        this.init();
    }

    init() {
        this.setupMarkdown();
        this.cacheElements();
        this.bindEvents();
        this.loadSessionFromStorage();
    }

    setupMarkdown() {
        // 配置 marked.js 使用 highlight.js
        marked.setOptions({
            highlight: function(code, lang) {
                if (lang && hljs.getLanguage(lang)) {
                    try {
                        return hljs.highlight(code, { language: lang }).value;
                    } catch (err) {}
                }
                return hljs.highlightAuto(code).value;
            },
            breaks: true,  // 支持换行
            gfm: true,     // 支持 GitHub 风格 Markdown
        });
    }

    cacheElements() {
        // 聊天相关元素
        this.messagesContainer = document.getElementById('messagesContainer');
        this.messageInput = document.getElementById('messageInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.welcomeMessage = document.getElementById('welcomeMessage');
        this.typingIndicator = document.getElementById('typingIndicator');

        // Agent 选择元素
        this.agentNavItems = document.querySelectorAll('.nav-item');

        // 头部元素
        this.agentAvatar = document.getElementById('agentAvatar');
        this.agentTitle = document.getElementById('agentTitle');
        this.agentDescription = document.getElementById('agentDescription');

        // 会话信息元素
        this.messageCountEl = document.getElementById('messageCount');
        this.stageInfo = document.getElementById('stageInfo');
        this.currentStageEl = document.getElementById('currentStage');
        this.sessionInfo = document.getElementById('sessionInfo');

        // 信息面板元素
        this.infoPanel = document.getElementById('infoPanel');
        this.closePanelBtn = document.getElementById('closePanelBtn');
        this.progressSection = document.getElementById('progressSection'); // cache progressSection
        this.progressContent = document.getElementById('progressContent');
        this.codeSection = document.getElementById('codeSection');
        this.codeContent = document.getElementById('codeContent');
        this.scoresSection = document.getElementById('scoresSection');
        this.scoresContent = document.getElementById('scoresContent');
        this.summarySection = document.getElementById('summarySection');
        this.summaryContent = document.getElementById('summaryContent');

        // 按钮元素
        this.newChatBtn = document.getElementById('newChatBtn');
        this.clearHistoryBtn = document.getElementById('clearHistoryBtn');
        this.quickActions = document.getElementById('quickActions');

        // Toast 容器
        this.toastContainer = document.getElementById('toastContainer');

        // 知识点选择模态框元素
        this.selectionModal = document.getElementById('selectionModal');
        this.knowledgeList = document.getElementById('knowledgeList');
        this.selectedCountEl = document.getElementById('selectedCount');
        this.startLearningBtn = document.getElementById('startLearningBtn');
        this.nextQuestionBtn = document.getElementById('nextQuestionBtn');
        
        this.selectedTopics = new Set();
    }

    bindEvents() {
        // 发送消息
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // 下一题按钮
        if (this.nextQuestionBtn) {
            this.nextQuestionBtn.addEventListener('click', () => this.nextQuestion());
        }

        // 模态框事件
        this.startLearningBtn.addEventListener('click', () => this.submitTopicSelection());

        // 输入框自适应高度
        this.messageInput.addEventListener('input', () => {
            this.messageInput.style.height = 'auto';
            this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 150) + 'px';
            this.updateSendButton();
        });

        // Agent 切换
        this.agentNavItems.forEach(item => {
            item.addEventListener('click', () => {
                const agentType = item.dataset.agent;
                if (agentType !== this.currentAgent) {
                    this.switchAgent(agentType);
                }
            });
        });

        // 新对话
        this.newChatBtn.addEventListener('click', () => this.resetSession());

        // 清空历史
        this.clearHistoryBtn.addEventListener('click', () => {
            if (confirm('确定要清空聊天记录吗？')) {
                this.clearMessages();
            }
        });

        // 信息面板
        this.closePanelBtn.addEventListener('click', () => {
            this.infoPanel.classList.add('collapsed');
        });

        // 快捷操作
        this.quickActions.addEventListener('click', (e) => {
            if (e.target.classList.contains('action-btn')) {
                const action = e.target.dataset.action;
                this.handleQuickAction(action);
            }
        });
    }

    updateSendButton() {
        const hasContent = this.messageInput.value.trim().length > 0;
        this.sendBtn.disabled = !hasContent || this.isStreaming;
    }

    async switchAgent(agentType) {
        if (this.isStreaming) {
            this.showToast('请等待当前消息发送完成', 'warning');
            return;
        }

        // 更新当前 Agent
        this.currentAgent = agentType;

        // 更新导航高亮
        this.agentNavItems.forEach(item => {
            item.classList.toggle('active', item.dataset.agent === agentType);
        });

        // 更新头部信息
        const config = this.agentConfig[agentType];
        
        this.agentAvatar.textContent = config.icon;
        this.agentTitle.textContent = config.title;
        this.agentDescription.textContent = config.description;

        // 重置会话
        await this.resetSession();

        this.showToast(`已切换到${config.title}`, 'success');
    }

    async resetSession() {
        try {
            // 如果没有 session_id，生成一个新的
            if (!this.sessionId) {
                this.sessionId = crypto.randomUUID();
            }

            // 调用重置/创建接口
            const response = await fetch(`/api/session/${this.sessionId}/reset?agent_type=${this.currentAgent}`, {
                method: 'POST'
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.session_id) {
                    this.sessionId = data.session_id;
                }
            }

            this.messageCount = 0;
            
            // 必须先更新信息，这样才能获取到 Agent 的初始状态（如是否需要选课）
            await this.updateSessionInfo();
            
            // 强制检查一次知识点选择（针对 Core Teaching Agent 和 Error Analysis Agent）
            if (this.currentAgent === 'core_teaching' || this.currentAgent === 'error_analysis') {
                await this.checkTopicSelection({}); 
            }

            // 清空消息
            this.clearMessages();

            // 显示欢迎消息
            if (this.welcomeMessage) {
                this.welcomeMessage.style.display = 'flex';
            }

            // 隐藏快捷操作
            this.quickActions.style.display = 'none';

            this.showToast('已开始新对话', 'success');
        } catch (error) {
            this.showToast('重置会话失败: ' + error.message, 'error');
        }
    }

    clearMessages() {
        const messages = this.messagesContainer.querySelectorAll('.message');
        messages.forEach(msg => msg.remove());
    }

    async sendMessage() {
        const content = this.messageInput.value.trim();
        if (!content || this.isStreaming) return;

        // 隐藏欢迎消息
        if (this.welcomeMessage) {
            this.welcomeMessage.style.display = 'none';
        }

        // 显示快捷操作
        this.quickActions.style.display = 'flex';

        // 添加用户消息
        this.addMessage('user', content);

        // 清空输入框
        this.messageInput.value = '';
        this.messageInput.style.height = 'auto';
        this.updateSendButton();

        // 禁用输入
        this.isStreaming = true;
        this.updateSendButton();
        this.showTypingIndicator();

        try {
            // 使用流式 API
            await this.streamResponse(content);
        } catch (error) {
            this.hideTypingIndicator();
            this.isStreaming = false;
            this.updateSendButton();
            this.showToast('发送消息失败: ' + error.message, 'error');
        }
    }

    async streamResponse(userMessage) {
        const response = await fetch('/api/chat/stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                agent_type: this.currentAgent,
                message: userMessage,
                session_id: this.sessionId
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // 隐藏打字指示器
        this.hideTypingIndicator();

        // 创建助手消息容器
        const messageContent = this.addMessage('assistant', '');
        this.currentMessageElement = messageContent;

        // 累积完整内容用于 markdown 渲染
        let fullContent = '';

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        try {
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop(); // 保留不完整的行

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = JSON.parse(line.slice(6));

                        if (data.error) {
                            throw new Error(data.content);
                        }

                        // 保存 session_id
                        if (data.session_id) {
                            this.sessionId = data.session_id;
                        }

                        if (data.content) {
                            fullContent += data.content;
                            // 流式显示：先显示纯文本，提供即时反馈
                            this.currentMessageElement.innerHTML += this.escapeHtml(data.content);
                            this.scrollToBottom();
                        }

                        if (data.done) {
                            // 流式完成后，渲染 markdown
                            this.currentMessageElement.innerHTML = marked.parse(fullContent);
                            // 代码高亮
                            this.currentMessageElement.querySelectorAll('pre code').forEach((block) => {
                                hljs.highlightElement(block);
                            });
                            this.scrollToBottom();

                            // 消息完成，更新会话信息
                            await this.updateSessionInfo();
                            await this.updatePanelInfo();
                        }
                    }
                }
            }
        } finally {
            this.isStreaming = false;
            this.currentMessageElement = null;
            this.updateSendButton();
        }
    }

    addMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = role === 'user' ? '👤' : this.agentConfig[this.currentAgent].icon;

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';

        if (content) {
            messageContent.innerHTML = this.escapeHtml(content);
        }

        const meta = document.createElement('div');
        meta.className = 'message-meta';
        meta.innerHTML = `
            <span>${role === 'user' ? '你' : 'AI 导师'}</span>
            <span>${new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}</span>
        `;

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        messageDiv.appendChild(meta);

        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();

        return messageContent;
    }

    async updateSessionInfo() {
        if (!this.sessionId) return;

        try {
            const response = await fetch(`/api/session/${this.sessionId}/info`);
            if (response.ok) {
                const info = await response.json();
                
                // 更新消息数
                this.messageCount = info.message_count;
                this.messageCountEl.textContent = this.messageCount;
                
                // 更新阶段
                if (info.current_stage) {
                    this.stageInfo.style.display = 'flex';
                    this.currentStageEl.textContent = info.current_stage;
                }
                
                // 更新进度和特定 Agent 的 UI
                if (info.agent_type === 'core_teaching') {
                    this.infoPanel.classList.remove('expanded');
                    this.codeSection.style.display = 'none';
                    this.progressSection.style.display = 'block';
                    this.renderProgress(info.progress);
                } else if (info.agent_type === 'error_analysis') {
                    this.infoPanel.classList.add('expanded');
                    this.codeSection.style.display = 'block';
                    
                    if (info.current_code_snippet) {
                        this.codeContent.textContent = info.current_code_snippet;
                        hljs.highlightElement(this.codeContent);
                    }
                    
                    // 更新进度显示
                    this.renderErrorAnalysisProgress(info.progress);
                }

                // 检查是否需要选择知识点
                await this.checkTopicSelection(info);
                
                // 更新评分信息 (如果存在)
                if (info.scores) {
                    this.scoresSection.style.display = 'block';
                    this.scoresContent.innerHTML = this.formatScores ? this.formatScores(info.scores) : JSON.stringify(info.scores);
                }

                // 更新摘要信息 (如果存在)
                if (info.learning_summary) {
                    this.summarySection.style.display = 'block';
                    this.summaryContent.innerHTML = this.formatSummary ? this.formatSummary(info.learning_summary) : JSON.stringify(info.learning_summary);
                }
            }
        } catch (error) {
            console.error('Failed to update session info:', error);
        }
    }

    async nextQuestion() {
        if (!this.sessionId) return;
        
        try {
            const response = await fetch(`/api/session/${this.sessionId}/next-topic`, {
                method: 'POST'
            });
            
            if (response.ok) {
                const data = await response.json();
                this.showToast('已切换到下一题', 'success');
                // 刷新界面
                await this.updateSessionInfo();
                
                // 如果有返回新的开场白，作为 Agent 消息显示
                if (data.response) {
                     this.addMessage('agent', data.response);
                }
            } else {
                this.showToast('切换失败', 'error');
            }
        } catch (error) {
             this.showToast('请求失败: ' + error.message, 'error');
        }
    }

    renderErrorAnalysisProgress(progress) {
        if (!progress) {
            this.progressSection.style.display = 'none';
            return;
        }

        const { current_topic, found_bugs, total_bugs } = progress;
        
        // 只有当有选中题目且总数大于0时才显示
        if (current_topic && current_topic !== "完成") {
             const percentage = total_bugs > 0 ? (found_bugs / total_bugs * 100) : 0;
             
             this.progressContent.innerHTML = `
                <div class="progress-item">
                    <div class="progress-label">当前题目: ${current_topic}</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${percentage}%"></div>
                    </div>
                    <div class="progress-text">已发现错误: ${found_bugs} / ${total_bugs}</div>
                </div>
            `;
            this.progressSection.style.display = 'block';
        } else if (current_topic === "完成") {
             this.progressContent.innerHTML = `
                <div class="progress-item">
                    <div class="progress-label">🎉 全部完成</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: 100%; background: var(--success-color)"></div>
                    </div>
                    <div class="progress-text">任务结束</div>
                </div>
            `;
            this.progressSection.style.display = 'block';
        } else {
            this.progressSection.style.display = 'none';
        }
    }

    renderProgress(progress) {
        if (!progress) return;
        
        const { completed_topics, current_topic, details } = progress;
        
        let html = '';
        
        if (current_topic) {
            html += `<div class="current-topic-card">
                <h5>📚 当前学习: ${current_topic}</h5>
            </div>`;
        }
        
        if (details) {
            html += '<div class="topic-list">';
            for (const [topicId, status] of Object.entries(details)) {
                const isCompleted = status.completed;
                const isCurrent = topicId === current_topic;
                
                // 构建子步骤 HTML
                let milestonesHtml = '';
                let hasMilestones = false;
                if (status.milestones && status.milestone_names) {
                    hasMilestones = true;
                    milestonesHtml = '<div class="milestones-container" style="display: none;">'; // 默认隐藏
                    const stepOrder = ["concept", "example", "practice", "summary"];
                    
                    stepOrder.forEach(stepKey => {
                        const stepName = status.milestone_names[stepKey] || stepKey;
                        const stepStatus = status.milestones[stepKey] || "pending";
                        
                        let icon = '⚪';
                        let colorClass = 'pending';
                        if (stepStatus === 'completed') {
                            icon = '✅';
                            colorClass = 'completed';
                        } else if (stepStatus === 'active') {
                            icon = '▶️';
                            colorClass = 'active';
                        }
                        
                        milestonesHtml += `
                            <div class="milestone-item ${colorClass}">
                                <span class="milestone-icon">${icon}</span>
                                <span class="milestone-name">${stepName}</span>
                            </div>
                        `;
                    });
                    milestonesHtml += '</div>';
                }

                const toggleAction = hasMilestones ? "var el = this.nextElementSibling; if(el) el.style.display = el.style.display === 'none' ? 'block' : 'none'" : "";
                const cursorStyle = hasMilestones ? "cursor: pointer;" : "cursor: default;";
                const toggleIcon = hasMilestones ? '<span class="toggle-icon">▼</span>' : '';

                html += `
                    <div class="topic-wrapper">
                        <div class="topic-item ${isCompleted ? 'completed' : ''} ${isCurrent ? 'active' : ''}" 
                             style="${cursorStyle}"
                             onclick="${toggleAction}">
                            <span class="status-icon">${isCompleted ? '✅' : (isCurrent ? '▶️' : '⚪')}</span>
                            <span class="topic-name">${topicId}</span>
                            ${toggleIcon}
                        </div>
                        ${milestonesHtml}
                    </div>
                `;
            }
            html += '</div>';
        }
        
        this.progressContent.innerHTML = html;
    }

    async updatePanelInfo() {
        try {
            if (!this.sessionId) return;

            const response = await fetch(`/api/session/${this.sessionId}/info`);
            if (response.ok) {
                const info = await response.json();
                
                // 如果是 core_teaching 或 error_analysis，由 updateSessionInfo 接管 UI 更新
                if (info.agent_type === 'core_teaching' || info.agent_type === 'error_analysis') {
                    return;
                }

                // 更新进度信息
                if (info.progress) {
                    const mode = info.progress.mode;

                    if (mode === 'error_analysis') {
                        // 错误代码分析模式
                        this.infoPanel.classList.add('expanded'); // 宽度增加到30%
                        if (this.progressSection) this.progressSection.style.display = 'none';
                        if (this.codeSection) {
                            this.codeSection.style.display = 'block';

                            const header = this.codeSection.querySelector('h4');
                            if (header) header.textContent = '📝 代码分析 (C语言)';

                            if (info.progress.current_code) {
                                this.codeContent.className = 'language-c';
                                this.codeContent.textContent = info.progress.current_code;
                                hljs.highlightElement(this.codeContent);
                            }
                            
                            // 添加或更新切换代码按钮
                            this.updateNextCodeButton(info.progress);
                        }
                    } else {
                        // 知识点学习模式
                        this.infoPanel.classList.remove('expanded'); // 恢复默认宽度
                        if (this.codeSection) this.codeSection.style.display = 'none';
                        if (this.progressSection) this.progressSection.style.display = 'block';
                        this.progressContent.innerHTML = this.formatProgress(info.progress);
                    }
                }

                // 更新评分信息
                if (info.scores) {
                    this.scoresSection.style.display = 'block';
                    this.scoresContent.innerHTML = this.formatScores(info.scores);
                }

                // 更新摘要信息
                if (info.learning_summary) {
                    this.summarySection.style.display = 'block';
                    this.summaryContent.innerHTML = this.formatSummary(info.learning_summary);
                }

                // 显示信息面板
                this.infoPanel.classList.remove('collapsed');
            }
        } catch (error) {
            console.error('更新面板信息失败:', error);
        }
    }

    updateNextCodeButton(progress) {
        let btn = document.getElementById('nextCodeBtn');
        if (!btn) {
            btn = document.createElement('button');
            btn.id = 'nextCodeBtn';
            btn.className = 'btn-secondary';
            btn.style.width = '100%';
            btn.style.marginTop = '16px';
            btn.innerHTML = '<span>🔄</span> 切换代码 / 下一个案例';
            btn.onclick = () => this.triggerNextCode();
            this.codeSection.appendChild(btn);
        }
        
        // 如果已经完成了所有，可以禁用或隐藏
        // 这里暂时保持一直显示
    }

    async triggerNextCode() {
        if(confirm('确定要切换到下一个错误代码案例吗？')) {
            this.addMessage('user', '[NEXT_CODE]');
            this.isStreaming = true;
            this.updateSendButton();
            this.showTypingIndicator();
            try {
                await this.streamResponse('[NEXT_CODE]');
            } catch (error) {
                this.hideTypingIndicator();
                this.isStreaming = false;
                this.updateSendButton();
                this.showToast('操作失败: ' + error.message, 'error');
            }
        }
    }

    formatProgress(progress) {
        let html = '<div style="display: flex; flex-direction: column; gap: 16px;">';

        // 总体进度
        if (progress["总体进度"]) {
            html += `
                <div style="padding: 12px; background: var(--background-medium); border-radius: 8px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="color: var(--text-secondary); font-size: 12px;">总体进度</span>
                        <span style="color: var(--primary-color); font-weight: 600;">${progress["总体进度"]}</span>
                    </div>
                    <div style="width: 100%; height: 4px; background: #333; border-radius: 2px;">
                        <div style="width: ${eval(progress["总体进度"]) * 100}%; height: 100%; background: var(--primary-color); border-radius: 2px; transition: width 0.3s ease;"></div>
                    </div>
                </div>
            `;
        }

        // 详细知识点列表
        if (progress.topics_status && progress.topics_status.length > 0) {
            html += '<div style="display: flex; flex-direction: column; gap: 8px;">';
            progress.topics_status.forEach(topic => {
                const isCurrent = topic.is_current;
                const isCompleted = topic.is_completed;
                const mastery = topic.mastery || 0;
                
                let statusIcon = '○';
                let statusColor = 'var(--text-secondary)';
                
                if (isCompleted) {
                    statusIcon = '✓';
                    statusColor = 'var(--success-color)';
                } else if (isCurrent) {
                    statusIcon = '▶';
                    statusColor = 'var(--primary-color)';
                }

                html += `
                    <div style="padding: 10px; background: ${isCurrent ? 'rgba(74, 144, 226, 0.1)' : 'var(--background-medium)'}; border-radius: 8px; border: 1px solid ${isCurrent ? 'var(--primary-color)' : 'transparent'};">
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <span style="color: ${statusColor}; font-weight: bold;">${statusIcon}</span>
                                <span style="color: var(--text-primary); font-size: 13px;">${topic.name}</span>
                            </div>
                            <span style="color: ${statusColor}; font-size: 12px;">${mastery}%</span>
                        </div>
                        <div style="width: 100%; height: 3px; background: #333; border-radius: 1.5px; overflow: hidden;">
                            <div style="width: ${mastery}%; height: 100%; background: ${statusColor}; transition: width 0.5s ease;"></div>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
        }

        // 下一个主题按钮
        if (progress["当前知识点"]) {
             html += `
                <button id="nextTopicBtn" class="btn-secondary" style="width: 100%; margin-top: 8px;">
                    <span>⏭</span> 跳过/进入下一章
                </button>
            `;
            
            // 绑定事件 (需要延迟到DOM渲染后)
            setTimeout(() => {
                const btn = document.getElementById('nextTopicBtn');
                if (btn) {
                    btn.onclick = () => {
                        if(confirm('确定要强制结束当前知识点的学习，进入下一个吗？')) {
                            this.forceNextTopic();
                        }
                    };
                }
            }, 100);
        }

        html += '</div>';
        return html;
    }

    async forceNextTopic() {
        this.addMessage('user', '[FORCE_NEXT_TOPIC]');
        this.isStreaming = true;
        this.updateSendButton();
        this.showTypingIndicator();
        try {
            await this.streamResponse('[FORCE_NEXT_TOPIC]');
        } catch (error) {
            this.hideTypingIndicator();
            this.isStreaming = false;
            this.updateSendButton();
            this.showToast('操作失败: ' + error.message, 'error');
        }
    }

    formatScores(scores) {
        let html = '<div style="display: flex; flex-direction: column; gap: 8px;">';

        for (const [dimension, score] of Object.entries(scores)) {
            const percentage = Math.round(score * 100);
            const color = percentage >= 70 ? 'var(--success-color)' :
                         percentage >= 50 ? 'var(--warning-color)' :
                         'var(--error-color)';

            html += `
                <div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px; font-size: 12px;">
                        <span>${dimension}</span>
                        <span style="color: ${color};">${percentage}%</span>
                    </div>
                    <div style="width: 100%; height: 6px; background: var(--background-medium); border-radius: 3px; overflow: hidden;">
                        <div style="width: ${percentage}%; height: 100%; background: ${color}; transition: width 0.3s ease;"></div>
                    </div>
                </div>
            `;
        }

        html += '</div>';
        return html;
    }

    formatSummary(summary) {
        return `<div style="white-space: pre-wrap; line-height: 1.8;">${this.escapeHtml(summary)}</div>`;
    }

    getStageDisplayName(stage) {
        const stageNames = {
            'concept_selection': '概念选择',
            'explanation': '尝试解释',
            'gap_analysis': '发现盲点',
            'code_simplification': '代码简化',
            'problem_statement': '问题描述',
            'hypothesis': '提出假设',
            'testing': '测试验证',
            'root_cause': '根因分析',
            'solution': '解决方案',
            'prevention': '预防措施'
        };
        return stageNames[stage] || stage;
    }

    handleQuickAction(action) {
        switch (action) {
            case 'hint':
                this.showToast('提示功能开发中...', 'warning');
                break;
            case 'summary':
                this.infoPanel.classList.toggle('collapsed');
                break;
            case 'progress':
                this.infoPanel.classList.toggle('collapsed');
                break;
        }
    }

    async checkTopicSelection(sessionInfo) {
        // 如果是核心教学 Agent 或 错误分析 Agent，且还没有选定主题
        if (this.currentAgent === 'core_teaching' || this.currentAgent === 'error_analysis') {
            const hasSelectedTopics = sessionInfo && 
                                      sessionInfo.selected_topics && 
                                      sessionInfo.selected_topics.length > 0;
            
            if (!hasSelectedTopics) {
                // 显示选择模态框
                await this.showTopicSelectionModal();
            } else {
                this.selectionModal.style.display = 'none';
            }
        } else {
            this.selectionModal.style.display = 'none';
        }

        // 更新输入框提示
        this.updateInputPlaceholder();
    }

    updateInputPlaceholder() {
        if (this.currentAgent === 'error_analysis') {
            this.messageInput.placeholder = "请指出代码中的错误，或询问提示...";
        } else if (this.currentAgent === 'core_teaching') {
            this.messageInput.placeholder = "回答导师的问题，或提出你的疑问...";
        } else {
            this.messageInput.placeholder = "输入你的问题或代码...";
        }
    }

    async showTopicSelectionModal() {
        this.selectionModal.style.display = 'flex';
        this.selectedTopics.clear();
        this.startLearningBtn.textContent = '开始学习'; // 重置按钮文本
        this.updateSelectionUI();
        
        try {
            const response = await fetch('/api/knowledge-points');
            if (response.ok) {
                const points = await response.json();
                this.renderKnowledgePoints(points);
            }
        } catch (error) {
            this.showToast('获取知识点失败: ' + error.message, 'error');
        }
    }

    renderKnowledgePoints(points) {
        this.knowledgeList.innerHTML = '';
        
        points.forEach(point => {
            const item = document.createElement('div');
            item.className = 'knowledge-item';
            item.dataset.id = point.id;
            item.onclick = (e) => {
                // 防止点击 checkbox 时触发两次
                if (e.target.tagName !== 'INPUT') {
                    this.toggleTopicSelection(point.id, item);
                }
            };
            
            // 检查是否已选中
            const isSelected = this.selectedTopics.has(point.id);
            if (isSelected) item.classList.add('selected');

            item.innerHTML = `
                <input type="checkbox" ${isSelected ? 'checked' : ''} onchange="this.parentElement.click()">
                <div class="knowledge-info">
                    <h4>${point.name}</h4>
                    <p>${point.description}</p>
                </div>
            `;
            
            this.knowledgeList.appendChild(item);
        });
    }

    toggleTopicSelection(id, element) {
        const checkbox = element.querySelector('input[type="checkbox"]');
        
        if (this.selectedTopics.has(id)) {
            this.selectedTopics.delete(id);
            element.classList.remove('selected');
            if (checkbox) checkbox.checked = false;
        } else {
            this.selectedTopics.add(id);
            element.classList.add('selected');
            if (checkbox) checkbox.checked = true;
        }
        this.updateSelectionUI();
    }

    updateSelectionUI() {
        const count = this.selectedTopics.size;
        this.selectedCountEl.textContent = count;
        this.startLearningBtn.disabled = count === 0;
    }

    async submitTopicSelection() {
        if (this.selectedTopics.size === 0) return;
        
        const topicIds = Array.from(this.selectedTopics);
        
        // 获取选中的难度
        const difficultyInputs = document.querySelectorAll('input[name="difficulty"]');
        let selectedDifficulty = 'medium';
        for (const input of difficultyInputs) {
            if (input.checked) {
                selectedDifficulty = input.value;
                break;
            }
        }
        
        try {
            this.startLearningBtn.disabled = true;
            this.startLearningBtn.textContent = '正在启动...';
            
            // 确保有 session_id
            if (!this.sessionId) {
                // 如果没有，先重置/创建
                await this.resetSession();
            }

            let response = await fetch(`/api/session/${this.sessionId}/select-topics`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    topic_ids: topicIds,
                    mode: this.currentMode,
                    difficulty: selectedDifficulty
                })
            });

            // 如果 session 不存在 (404)，尝试重置 session 并重试
            if (response.status === 404) {
                console.log('Session not found, resetting...');
                await this.resetSession();
                
                response = await fetch(`/api/session/${this.sessionId}/select-topics`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ 
                        topic_ids: topicIds,
                        mode: this.currentMode,
                        difficulty: selectedDifficulty
                    })
                });
            }

            if (response.ok) {
                const data = await response.json();
                this.selectionModal.style.display = 'none';
                
                // 重置按钮状态
                this.startLearningBtn.disabled = false;
                this.startLearningBtn.textContent = '开始学习';

                // 添加初始消息
                if (data.initial_response) {
                    this.addMessage('assistant', data.initial_response);
                }
                
                this.showToast('学习计划已生成', 'success');
                // 更新会话信息以同步状态
                this.updateSessionInfo();
            } else {
                throw new Error('提交失败');
            }
        } catch (error) {
            this.showToast('提交选择失败: ' + error.message, 'error');
            this.startLearningBtn.disabled = false;
            this.startLearningBtn.textContent = '开始学习';
        }
    }

    showTypingIndicator() {
        this.typingIndicator.style.display = 'flex';
    }

    hideTypingIndicator() {
        this.typingIndicator.style.display = 'none';
    }

    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML.replace(/\n/g, '<br>');
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;

        this.toastContainer.appendChild(toast);

        // 3秒后自动移除
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    saveSessionToStorage(info) {
        const sessions = JSON.parse(localStorage.getItem('agentSessions') || '{}');
        sessions[this.sessionId] = {
            agent_type: this.currentAgent,
            updated_at: new Date().toISOString(),
            info: info
        };
        localStorage.setItem('agentSessions', JSON.stringify(sessions));
    }

    loadSessionFromStorage() {
        const sessions = JSON.parse(localStorage.getItem('agentSessions') || '{}');
        const sessionIds = Object.keys(sessions);

        if (sessionIds.length > 0) {
            // 加载最近的会话
            const lastSessionId = sessionIds[sessionIds.length - 1];
            const session = sessions[lastSessionId];

            if (session.agent_type === this.currentAgent) {
                this.sessionId = lastSessionId;
                this.messageCount = session.info?.message_count || 0;
                this.updateSessionInfo();
            }
        }
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    window.agentApp = new AgentApp();
});
