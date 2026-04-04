/**
 * 代码框架 (Code Framework Studio) - 框架分解工作室
 * 核心理念：将每个拆解步骤视为一张"逻辑卡片"，递归展开
 */

const FrameworkStudio = {
    // 状态管理
    state: {
        sessionId: null,
        problemTitle: '',
        problemContent: '',
        cards: [],           // 所有卡片数据
        completedCount: 0,
        totalCount: 0,
        currentDepth: 0,
        maxDepth: 5
    },

    // 控制结构配置
    controlTypes: {
        sequence: { icon: '📋', name: '顺序结构', color: '#3498db' },
        selection: { icon: '🔀', name: '选择结构', color: '#e74c3c' },
        loop: { icon: '🔄', name: '循环结构', color: '#27ae60' }
    },

    // 初始化
    init() {
        console.log('FrameworkStudio 初始化...');
        this.loadSessionData();
        this.bindEvents();
    },

    // 加载会话数据
    async loadSessionData() {
        try {
            // 尝试从 sessionStorage 获取题目信息
            const problemData = sessionStorage.getItem('current_problem');
            if (problemData) {
                const data = JSON.parse(problemData);
                this.state.problemTitle = data.title || '编程题目';
                this.state.problemContent = data.content || '';
                document.getElementById('problem-title').textContent = this.state.problemTitle;
            }
            
            // 获取 session_id
            const response = await fetch('/api/xiaohang/get_session_status', {
                method: 'GET',
                credentials: 'include'
            });
            
            if (response.ok) {
                const data = await response.json();
                this.state.sessionId = data.session_id;
                if (data.problem) {
                    this.state.problemContent = data.problem;
                    // 提取题目标题（第一行或前50字符）
                    const firstLine = data.problem.split('\n')[0];
                    this.state.problemTitle = firstLine.substring(0, 50) + (firstLine.length > 50 ? '...' : '');
                    document.getElementById('problem-title').textContent = this.state.problemTitle;
                }
            }
        } catch (error) {
            console.error('加载会话数据失败:', error);
        }
    },

    // 绑定事件
    bindEvents() {
        // 键盘快捷键
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.collapseAll();
            }
        });
    },

    // 更新进度显示
    updateProgress() {
        document.getElementById('done-count').textContent = this.state.completedCount;
        document.getElementById('total-count').textContent = this.state.totalCount;
        document.getElementById('current-depth').textContent = `L${this.state.currentDepth}`;
    },

    // ==================== 核心：开始分解 ====================
    async startDecomposition() {
        document.getElementById('empty-state').style.display = 'none';
        this.showDecomposing(true);

        try {
            const response = await fetch('/api/xiaohang/decompose_problem', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                    level: 0,
                    parentProblem: this.state.problemContent
                })
            });

            if (!response.ok) throw new Error('分解请求失败');

            // 流式读取响应
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let fullText = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                fullText += decoder.decode(value);
            }

            // 解析 JSON 数据
            const data = this.parseDecompositionResponse(fullText);
            if (data) {
                this.renderRootCard(data);
            } else {
                this.showError('无法解析分解结果');
            }

        } catch (error) {
            console.error('分解失败:', error);
            this.showError('分解失败，请重试');
        } finally {
            this.showDecomposing(false);
        }
    },

    // 解析分解响应
    parseDecompositionResponse(text) {
        try {
            // 尝试提取 JSON
            const jsonMatch = text.match(/```json\s*([\s\S]*?)\s*```/);
            let jsonStr = null;
            
            if (jsonMatch) {
                jsonStr = jsonMatch[1].trim();
            } else {
                const firstBrace = text.indexOf('{');
                const lastBrace = text.lastIndexOf('}');
                if (firstBrace !== -1 && lastBrace > firstBrace) {
                    jsonStr = text.substring(firstBrace, lastBrace + 1);
                }
            }

            if (jsonStr) {
                return JSON.parse(jsonStr);
            }
        } catch (error) {
            console.error('JSON 解析失败:', error);
        }
        return null;
    },

    // ==================== 渲染根卡片 ====================
    renderRootCard(data) {
        const container = document.getElementById('cards-container');
        container.innerHTML = '';

        const cardId = this.generateCardId();
        const cardData = {
            id: cardId,
            layer: data.level || 0,
            name: data.parentProblem || '主问题',
            controlType: 'sequence',
            ipo: data.overallIPO || {},
            subProblems: data.subProblems || [],
            completed: false,
            expanded: true,
            isLeaf: true  // 初始为叶子节点，分解后变为非叶子
        };

        this.state.cards.push(cardData);
        this.state.currentDepth = cardData.layer;
        this.recalculateCounts();  // 重新计算

        const cardHtml = this.createCardHtml(cardData);
        container.innerHTML = cardHtml;

        // 渲染 Mermaid 图
        this.renderMermaidForCard(cardId, cardData);
    },

    // ==================== 创建卡片 HTML ====================
    createCardHtml(cardData) {
        const ctrl = this.controlTypes[cardData.controlType] || this.controlTypes.sequence;
        const layerLabel = `Layer ${cardData.layer}`;
        
        return `
        <div class="logic-card slide-in" 
             id="card-${cardData.id}" 
             data-layer="${cardData.layer}"
             data-card-id="${cardData.id}">
            
            <!-- 区域①：状态栏 -->
            <div class="card-header" onclick="FrameworkStudio.toggleCard('${cardData.id}')">
                <div class="header-left">
                    <span class="layer-tag">${layerLabel}</span>
                    <span class="module-name">${this.escapeHtml(cardData.name)}</span>
                    <span class="control-type-badge">
                        <span>${ctrl.icon}</span>
                        <span>${ctrl.name}</span>
                    </span>
                </div>
                <div class="header-right">
                    <span class="status-badge pending" id="status-${cardData.id}">待处理</span>
                    <span class="toggle-icon">▼</span>
                </div>
            </div>
            
            <!-- 区域②：可视化逻辑区 -->
            <div class="card-body">
                <div class="mermaid-container" id="mermaid-${cardData.id}">
                    <div class="mermaid-loading">生成逻辑图中...</div>
                </div>
                
                <!-- IPO 信息 -->
                ${this.renderIPOSection(cardData.ipo)}
                
                <!-- 区域③：交互决策区 -->
                <div class="confidence-gate" id="gate-${cardData.id}">
                    <div class="gate-question">
                        你要继续分解 <em>${this.escapeHtml(cardData.name)}</em> 的代码吗？
                    </div>
                    <div class="gate-buttons">
                        <!-- ORIGINAL: 基于上述逻辑结构，你现在能写出...的代码吗？ -->
                        <!-- COMMENTED OUT:
                        <button class="gate-btn can-write" onclick="FrameworkStudio.markAsCanWrite('${cardData.id}')">
                            ✅ 能，我可以写出来
                        </button>
                        -->
                        <button class="gate-btn cannot-write" onclick="FrameworkStudio.continueDecompose('${cardData.id}')">
                            🔍 不能，继续分解
                        </button>
                    </div>
                </div>
                
                <!-- 代码输入区 -->
                <div class="code-input-area" id="code-area-${cardData.id}">
                    <textarea class="code-textarea" 
                              id="code-${cardData.id}"
                              placeholder="// 在这里写出该模块的代码实现..."></textarea>
                    <div class="code-actions">
                        <button class="code-action-btn" onclick="FrameworkStudio.cancelCode('${cardData.id}')">取消</button>
                        <button class="code-action-btn confirm" onclick="FrameworkStudio.confirmCode('${cardData.id}')">✓ 确认完成</button>
                    </div>
                </div>
                
                <!-- 子卡片容器 -->
                <div class="sub-cards-container" id="sub-cards-${cardData.id}"></div>
            </div>
            
            <!-- 完成摘要 -->
            <div class="completed-summary">
                ✅ 模块已就绪 - 代码已编写
            </div>
        </div>
        `;
    },

    // 渲染 IPO 区域
    renderIPOSection(ipo) {
        if (!ipo || (!ipo.input && !ipo.process && !ipo.output)) {
            return '';
        }
        
        return `
        <div class="ipo-section">
            <div class="ipo-box input">
                <div class="ipo-label">📥 输入</div>
                <div class="ipo-content">${this.escapeHtml(ipo.input || '-')}</div>
            </div>
            <div class="ipo-box process">
                <div class="ipo-label">⚙️ 处理</div>
                <div class="ipo-content">${this.escapeHtml(ipo.process || '-')}</div>
            </div>
            <div class="ipo-box output">
                <div class="ipo-label">📤 输出</div>
                <div class="ipo-content">${this.escapeHtml(ipo.output || '-')}</div>
            </div>
        </div>
        `;
    },

    // ==================== Mermaid 图表生成 ====================
    async renderMermaidForCard(cardId, cardData) {
        const container = document.getElementById(`mermaid-${cardId}`);
        if (!container) return;

        // 根据子问题生成 Mermaid 代码
        const mermaidCode = this.generateMermaidCode(cardData);
        
        try {
            const id = `mermaid-render-${cardId}-${Date.now()}`;
            const { svg } = await mermaid.render(id, mermaidCode);
            container.innerHTML = svg;
            
            // 为子问题节点添加高亮样式
            this.highlightSubProblemNodes(container, cardData.subProblems);
        } catch (error) {
            console.error('Mermaid 渲染失败:', error);
            container.innerHTML = `
                <div style="color: #64748b; font-size: 13px;">
                    <p>📊 逻辑结构预览</p>
                    <pre style="background: #f1f5f9; padding: 12px; border-radius: 8px; text-align: left; font-size: 12px; overflow-x: auto;">${this.escapeHtml(mermaidCode)}</pre>
                </div>
            `;
        }
    },

    // 生成 Mermaid 代码
    generateMermaidCode(cardData) {
        const subProblems = cardData.subProblems || [];
        
        if (subProblems.length === 0) {
            // 没有子问题，显示简单的单节点
            return `graph LR
    A[${this.sanitizeMermaidText(cardData.name)}]
    style A fill:#e0f2fe,stroke:#3b82f6,stroke-width:2px`;
        }

        // 分析主要控制结构
        const hasLoop = subProblems.some(s => s.controlType === 'loop');
        const hasSelection = subProblems.some(s => s.controlType === 'selection');

        let code = '';

        if (hasSelection && subProblems.length <= 3) {
            // 选择结构 - 菱形判定
            code = this.generateSelectionDiagram(cardData, subProblems);
        } else if (hasLoop) {
            // 循环结构 - 环形流程
            code = this.generateLoopDiagram(cardData, subProblems);
        } else {
            // 顺序结构 - 线性流程
            code = this.generateSequenceDiagram(cardData, subProblems);
        }

        return code;
    },

    // 顺序结构图
    generateSequenceDiagram(cardData, subProblems) {
        let nodes = ['graph LR'];
        
        subProblems.forEach((sub, index) => {
            const nodeId = String.fromCharCode(65 + index); // A, B, C...
            const nextId = String.fromCharCode(65 + index + 1);
            const icon = this.controlTypes[sub.controlType]?.icon || '📋';
            const name = this.sanitizeMermaidText(sub.name || `步骤${index + 1}`);
            
            nodes.push(`    ${nodeId}["${icon} ${name}"]`);
            
            if (index < subProblems.length - 1) {
                nodes.push(`    ${nodeId} --> ${nextId}`);
            }
            
            // 根据控制类型添加样式
            const styleColor = this.getControlTypeColor(sub.controlType);
            nodes.push(`    style ${nodeId} fill:${styleColor.bg},stroke:${styleColor.border},stroke-width:2px`);
        });

        return nodes.join('\n');
    },

    // 选择结构图
    generateSelectionDiagram(cardData, subProblems) {
        let nodes = ['graph TD'];
        
        // 找到选择节点
        const selectionNode = subProblems.find(s => s.controlType === 'selection');
        const otherNodes = subProblems.filter(s => s.controlType !== 'selection');
        
        if (selectionNode) {
            const conditionText = this.sanitizeMermaidText(selectionNode.name || '条件判断');
            nodes.push(`    A{{"${conditionText}?"}}`);
            nodes.push(`    style A fill:#fef3c7,stroke:#f59e0b,stroke-width:2px`);
            
            // 分支
            if (otherNodes.length >= 2) {
                nodes.push(`    A -- Yes --> B["✅ ${this.sanitizeMermaidText(otherNodes[0]?.name || '分支1')}"]`);
                nodes.push(`    A -- No --> C["❌ ${this.sanitizeMermaidText(otherNodes[1]?.name || '分支2')}"]`);
                nodes.push(`    style B fill:#dcfce7,stroke:#22c55e,stroke-width:2px`);
                nodes.push(`    style C fill:#fee2e2,stroke:#ef4444,stroke-width:2px`);
            } else {
                nodes.push(`    A -- Yes --> B["执行操作"]`);
                nodes.push(`    A -- No --> C["跳过"]`);
            }
        } else {
            // 降级为顺序结构
            return this.generateSequenceDiagram(cardData, subProblems);
        }

        return nodes.join('\n');
    },

    // 循环结构图
    generateLoopDiagram(cardData, subProblems) {
        let nodes = ['graph TD'];
        
        // 找到循环节点
        const loopNode = subProblems.find(s => s.controlType === 'loop');
        const beforeLoop = subProblems.filter(s => s.controlType !== 'loop').slice(0, 1);
        const afterLoop = subProblems.filter(s => s.controlType !== 'loop').slice(1);
        
        let currentId = 'A';
        
        // 循环前的初始化
        if (beforeLoop.length > 0) {
            const initName = this.sanitizeMermaidText(beforeLoop[0].name || '初始化');
            nodes.push(`    A["📋 ${initName}"]`);
            nodes.push(`    A --> B`);
            nodes.push(`    style A fill:#e0f2fe,stroke:#3b82f6,stroke-width:2px`);
            currentId = 'B';
        }
        
        // 循环条件判断
        const loopCondition = this.sanitizeMermaidText(loopNode?.name || '循环条件');
        nodes.push(`    ${currentId}{{"🔄 ${loopCondition}?"}}`);
        nodes.push(`    style ${currentId} fill:#dcfce7,stroke:#22c55e,stroke-width:2px`);
        
        // 循环体
        const nextId = String.fromCharCode(currentId.charCodeAt(0) + 1);
        nodes.push(`    ${currentId} -- Yes --> ${nextId}["执行循环体"]`);
        nodes.push(`    ${nextId} --> ${currentId}`);
        nodes.push(`    style ${nextId} fill:#e0f2fe,stroke:#3b82f6,stroke-width:2px,stroke-dasharray: 5 5`);
        
        // 循环结束
        const endId = String.fromCharCode(nextId.charCodeAt(0) + 1);
        nodes.push(`    ${currentId} -- No --> ${endId}["循环结束"]`);
        nodes.push(`    style ${endId} fill:#f1f5f9,stroke:#64748b,stroke-width:2px`);

        return nodes.join('\n');
    },

    // 获取控制类型颜色
    getControlTypeColor(controlType) {
        const colors = {
            sequence: { bg: '#e0f2fe', border: '#3b82f6' },
            selection: { bg: '#fef3c7', border: '#f59e0b' },
            loop: { bg: '#dcfce7', border: '#22c55e' }
        };
        return colors[controlType] || colors.sequence;
    },

    // 高亮子问题节点
    highlightSubProblemNodes(container, subProblems) {
        // 可以在这里添加点击事件等交互
    },

    // 清理 Mermaid 文本
    sanitizeMermaidText(text) {
        if (!text) return '';
        return text
            .replace(/["\[\]{}()<>]/g, '')
            .replace(/\n/g, ' ')
            .substring(0, 30);
    },

    // ==================== 交互操作 ====================
    
    // 折叠/展开卡片
    toggleCard(cardId) {
        const card = document.getElementById(`card-${cardId}`);
        if (card) {
            card.classList.toggle('collapsed');
        }
    },

    // 标记为"能写出代码"
    markAsCanWrite(cardId) {
        const card = document.getElementById(`card-${cardId}`);
        const gate = document.getElementById(`gate-${cardId}`);
        const codeArea = document.getElementById(`code-area-${cardId}`);
        
        if (card && gate && codeArea) {
            gate.style.display = 'none';
            card.classList.add('show-code');
            
            // 聚焦到代码输入框
            const textarea = document.getElementById(`code-${cardId}`);
            if (textarea) {
                textarea.focus();
            }
        }
    },

    // 取消代码输入
    cancelCode(cardId) {
        const card = document.getElementById(`card-${cardId}`);
        const gate = document.getElementById(`gate-${cardId}`);
        
        if (card && gate) {
            card.classList.remove('show-code');
            gate.style.display = 'block';
        }
    },

    // 确认代码完成
    confirmCode(cardId) {
        const card = document.getElementById(`card-${cardId}`);
        const statusBadge = document.getElementById(`status-${cardId}`);
        const cardData = this.state.cards.find(c => c.id === cardId);
        
        if (card && cardData) {
            card.classList.add('completed');
            card.classList.remove('show-code');
            cardData.completed = true;
            
            if (statusBadge) {
                statusBadge.textContent = '✅ 已完成';
                statusBadge.classList.remove('pending');
                statusBadge.classList.add('completed');
            }
            
            // 重新计算完成数
            this.recalculateCounts();
            
            // 检查是否所有模块都完成
            this.checkAllCompleted();
        }
    },

    // 重新计算总数和完成数（只计算叶子节点）
    recalculateCounts() {
        let total = 0;
        let completed = 0;
        
        this.state.cards.forEach(card => {
            // 只有叶子节点（isLeaf=true）才计入统计
            if (card.isLeaf) {
                total++;
                if (card.completed) {
                    completed++;
                }
            }
        });
        
        this.state.totalCount = total;
        this.state.completedCount = completed;
        this.updateProgress();
    },

    // ==================== 继续分解（核心递归逻辑） ====================
    async continueDecompose(cardId) {
        const cardData = this.state.cards.find(c => c.id === cardId);
        if (!cardData) return;

        const subCardsContainer = document.getElementById(`sub-cards-${cardId}`);
        const gate = document.getElementById(`gate-${cardId}`);
        const card = document.getElementById(`card-${cardId}`);
        const statusBadge = document.getElementById(`status-${cardId}`);
        
        if (!subCardsContainer) return;

        // 隐藏决策区
        if (gate) {
            gate.style.display = 'none';
        }
        
        // 将父卡片标记为非叶子节点（已分解），不再计入统计
        cardData.isLeaf = false;
        
        // 更新父卡片状态显示为"已分解"
        if (statusBadge) {
            statusBadge.textContent = '📂 已分解';
            statusBadge.classList.remove('pending');
            statusBadge.style.background = '#e0f2fe';
            statusBadge.style.color = '#0369a1';
        }

        // 显示加载状态
        subCardsContainer.innerHTML = `
            <div class="decomposing-indicator active">
                <div class="decomposing-spinner"></div>
                <div>正在分解子模块...</div>
            </div>
        `;

        try {
            // 如果已有子问题数据，直接渲染
            if (cardData.subProblems && cardData.subProblems.length > 0) {
                this.renderSubCards(cardId, cardData.subProblems, cardData.layer + 1);
                return;
            }

            // 否则请求 API 进行分解
            const response = await fetch('/api/xiaohang/decompose_problem', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                    level: cardData.layer + 1,
                    parentProblem: cardData.name
                })
            });

            if (!response.ok) throw new Error('分解请求失败');

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let fullText = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                fullText += decoder.decode(value);
            }

            const data = this.parseDecompositionResponse(fullText);
            if (data && data.subProblems) {
                cardData.subProblems = data.subProblems;
                this.renderSubCards(cardId, data.subProblems, cardData.layer + 1);
            } else {
                subCardsContainer.innerHTML = `
                    <div style="padding: 20px; text-align: center; color: #64748b;">
                        该模块已足够简单，无需继续分解
                    </div>
                `;
            }

        } catch (error) {
            console.error('分解失败:', error);
            subCardsContainer.innerHTML = `
                <div style="padding: 20px; text-align: center; color: #ef4444;">
                    分解失败，请重试
                    <button onclick="FrameworkStudio.continueDecompose('${cardId}')" 
                            style="margin-left: 10px; padding: 6px 12px; cursor: pointer;">
                        重试
                    </button>
                </div>
            `;
        }
    },

    // 渲染子卡片
    renderSubCards(parentCardId, subProblems, layer) {
        const container = document.getElementById(`sub-cards-${parentCardId}`);
        if (!container) return;

        container.innerHTML = '';

        // 更新深度
        if (layer > this.state.currentDepth) {
            this.state.currentDepth = layer;
        }

        subProblems.forEach((sub, index) => {
            const cardId = this.generateCardId();
            const cardData = {
                id: cardId,
                parentId: parentCardId,
                layer: layer,
                name: sub.name || `子模块 ${index + 1}`,
                description: sub.description || '',
                controlType: sub.controlType || 'sequence',
                ipo: sub.ipo || {},
                subProblems: [],
                needsFurtherDecomposition: sub.needsFurtherDecomposition !== false,
                codeHint: sub.codeHint || '',
                completed: false,
                expanded: true,
                isLeaf: true  // 新创建的子卡片默认为叶子节点
            };

            this.state.cards.push(cardData);

            // 延迟渲染，产生滑入效果
            setTimeout(() => {
                const cardHtml = this.createSubCardHtml(cardData);
                container.insertAdjacentHTML('beforeend', cardHtml);
                
                // 渲染 Mermaid
                this.renderMermaidForSubCard(cardId, cardData);
            }, index * 150);
        });

        // 重新计算计数
        this.recalculateCounts();
    },

    // 创建子卡片 HTML（简化版）
    createSubCardHtml(cardData) {
        const ctrl = this.controlTypes[cardData.controlType] || this.controlTypes.sequence;
        const layerLabel = `Layer ${cardData.layer}`;
        
        // 如果不需要继续分解，显示代码提示
        const codeHintHtml = cardData.codeHint ? `
            <div style="margin-top: 12px; background: #1e293b; padding: 12px; border-radius: 8px;">
                <div style="font-size: 11px; color: #94a3b8; margin-bottom: 6px;">💡 代码提示</div>
                <pre style="margin: 0; font-size: 12px; color: #e2e8f0; overflow-x: auto;"><code>${this.escapeHtml(cardData.codeHint)}</code></pre>
            </div>
        ` : '';

        // 如果足够简单，不显示继续分解按钮
        const gateHtml = cardData.needsFurtherDecomposition ? `
            <div class="confidence-gate" id="gate-${cardData.id}">
                <div class="gate-question">
                    你要继续分解 <em>${this.escapeHtml(cardData.name)}</em> 的代码吗？
                </div>
                <div class="gate-buttons">
                    <!-- ORIGINAL: 你能写出...的代码吗？ -->
                    <!-- COMMENTED OUT:
                    <button class="gate-btn can-write" onclick="FrameworkStudio.markAsCanWrite('${cardData.id}')">
                        ✅ 能
                    </button>
                    -->
                    <button class="gate-btn cannot-write" onclick="FrameworkStudio.continueDecompose('${cardData.id}')">
                        🔍 继续分解
                    </button>
                </div>
            </div>
        ` : `
            <div class="confidence-gate" id="gate-${cardData.id}" style="background: #f0fdf4; border-color: #22c55e;">
                <div class="gate-question" style="color: #166534;">
                    <!-- ORIGINAL: ✨ 该模块已足够简单，可以直接编写代码 -->
                    该模块已足够简单，无需分解
                </div>
                <div class="gate-buttons">
                    <!-- COMMENTED OUT:
                    <button class="gate-btn can-write" onclick="FrameworkStudio.markAsCanWrite('${cardData.id}')">
                        ✅ 开始编写
                    </button>
                    -->
                </div>
                ${codeHintHtml}
            </div>
        `;

        return `
        <div class="logic-card slide-in" 
             id="card-${cardData.id}" 
             data-layer="${cardData.layer}"
             data-card-id="${cardData.id}">
            
            <div class="card-header" onclick="FrameworkStudio.toggleCard('${cardData.id}')">
                <div class="header-left">
                    <span class="layer-tag">${layerLabel}</span>
                    <span class="module-name">${this.escapeHtml(cardData.name)}</span>
                    <span class="control-type-badge">
                        <span>${ctrl.icon}</span>
                        <span>${ctrl.name}</span>
                    </span>
                </div>
                <div class="header-right">
                    <span class="status-badge pending" id="status-${cardData.id}">待处理</span>
                    <span class="toggle-icon">▼</span>
                </div>
            </div>
            
            <div class="card-body">
                ${cardData.description ? `<p style="color: #64748b; margin-bottom: 16px; font-size: 14px;">${this.escapeHtml(cardData.description)}</p>` : ''}
                
                <div class="mermaid-container" id="mermaid-${cardData.id}" style="min-height: 80px;">
                    <div class="mermaid-loading">生成逻辑图...</div>
                </div>
                
                ${this.renderIPOSection(cardData.ipo)}
                
                ${gateHtml}
                
                <div class="code-input-area" id="code-area-${cardData.id}">
                    <textarea class="code-textarea" 
                              id="code-${cardData.id}"
                              placeholder="// ${cardData.codeHint || '在这里写出该模块的代码...'}">${cardData.codeHint || ''}</textarea>
                    <div class="code-actions">
                        <button class="code-action-btn" onclick="FrameworkStudio.cancelCode('${cardData.id}')">取消</button>
                        <button class="code-action-btn confirm" onclick="FrameworkStudio.confirmCode('${cardData.id}')">✓ 确认完成</button>
                    </div>
                </div>
                
                <div class="sub-cards-container" id="sub-cards-${cardData.id}"></div>
            </div>
            
            <div class="completed-summary">
                ✅ 模块已就绪
            </div>
        </div>
        `;
    },

    // 为子卡片渲染简化的 Mermaid 图
    async renderMermaidForSubCard(cardId, cardData) {
        const container = document.getElementById(`mermaid-${cardId}`);
        if (!container) return;

        // 生成简化的单节点图
        const ctrl = this.controlTypes[cardData.controlType] || this.controlTypes.sequence;
        const color = this.getControlTypeColor(cardData.controlType);
        
        let mermaidCode = '';
        
        if (cardData.controlType === 'selection') {
            mermaidCode = `graph TD
    A{{"${ctrl.icon} ${this.sanitizeMermaidText(cardData.name)}?"}}
    A -- Yes --> B["执行"]
    A -- No --> C["跳过"]
    style A fill:${color.bg},stroke:${color.border},stroke-width:2px`;
        } else if (cardData.controlType === 'loop') {
            mermaidCode = `graph TD
    A{{"${ctrl.icon} ${this.sanitizeMermaidText(cardData.name)}"}}
    A -- 继续 --> B["循环体"]
    B --> A
    A -- 结束 --> C["退出"]
    style A fill:${color.bg},stroke:${color.border},stroke-width:2px
    style B fill:#e0f2fe,stroke:#3b82f6,stroke-width:2px,stroke-dasharray: 5 5`;
        } else {
            mermaidCode = `graph LR
    A["${ctrl.icon} ${this.sanitizeMermaidText(cardData.name)}"]
    style A fill:${color.bg},stroke:${color.border},stroke-width:2px`;
        }

        try {
            const id = `mermaid-sub-${cardId}-${Date.now()}`;
            const { svg } = await mermaid.render(id, mermaidCode);
            container.innerHTML = svg;
        } catch (error) {
            container.innerHTML = `<div style="color: #64748b; font-size: 13px;">${ctrl.icon} ${cardData.name}</div>`;
        }
    },

    // ==================== 工具函数 ====================
    
    // 生成唯一卡片 ID
    generateCardId() {
        return 'card_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    },

    // HTML 转义
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    // 显示/隐藏分解中指示器
    showDecomposing(show) {
        const indicator = document.getElementById('decomposing-indicator');
        if (indicator) {
            indicator.classList.toggle('active', show);
        }
    },

    // 显示错误
    showError(message) {
        const container = document.getElementById('cards-container');
        container.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #ef4444;">
                <div style="font-size: 32px; margin-bottom: 12px;">⚠️</div>
                <div style="margin-bottom: 16px;">${message}</div>
                <button onclick="FrameworkStudio.startDecomposition()" 
                        style="padding: 10px 20px; background: #3b82f6; color: white; border: none; border-radius: 8px; cursor: pointer;">
                    重试
                </button>
            </div>
        `;
    },

    // 检查是否全部完成
    checkAllCompleted() {
        if (this.state.completedCount >= this.state.totalCount && this.state.totalCount > 0) {
            this.showCompletionCelebration();
        }
    },

    // 完成庆祝
    showCompletionCelebration() {
        const container = document.getElementById('cards-container');
        container.insertAdjacentHTML('beforeend', `
            <div style="text-align: center; padding: 40px; background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%); border-radius: 16px; margin-top: 24px;">
                <div style="font-size: 48px; margin-bottom: 12px;">🎉</div>
                <div style="font-size: 20px; font-weight: 600; color: #166534; margin-bottom: 8px;">太棒了！所有模块已完成</div>
                <div style="color: #15803d; margin-bottom: 20px;">你已经成功分解并实现了整个问题</div>
                <button onclick="FrameworkStudio.exportCode()" 
                        style="padding: 12px 24px; background: #22c55e; color: white; border: none; border-radius: 10px; font-size: 15px; font-weight: 600; cursor: pointer;">
                    📤 导出完整代码
                </button>
            </div>
        `);
    },

    // ==================== 全局操作 ====================
    
    // 全部折叠
    collapseAll() {
        document.querySelectorAll('.logic-card').forEach(card => {
            card.classList.add('collapsed');
        });
    },

    // 全部展开
    expandAll() {
        document.querySelectorAll('.logic-card').forEach(card => {
            card.classList.remove('collapsed');
        });
    },

    // 重新分解
    resetDecomposition() {
        if (confirm('确定要重新开始分解吗？当前进度将丢失。')) {
            this.state.cards = [];
            this.state.completedCount = 0;
            this.state.totalCount = 0;
            this.state.currentDepth = 0;
            
            document.getElementById('cards-container').innerHTML = '';
            document.getElementById('empty-state').style.display = 'block';
            this.updateProgress();
        }
    },

    // 导出代码
    exportCode() {
        let code = '// ==================== 自动生成的代码框架 ====================\n\n';
        
        this.state.cards.forEach(card => {
            if (card.completed) {
                const textarea = document.getElementById(`code-${card.id}`);
                if (textarea && textarea.value.trim()) {
                    code += `// --- ${card.name} ---\n`;
                    code += textarea.value.trim() + '\n\n';
                }
            }
        });

        if (code.includes('---')) {
            // 创建下载
            const blob = new Blob([code], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'framework_code.c';
            a.click();
            URL.revokeObjectURL(url);
        } else {
            alert('还没有完成任何模块的代码编写');
        }
    }
};

// ==================== 全局函数（供 HTML 调用） ====================

function startDecomposition() {
    FrameworkStudio.startDecomposition();
}

function collapseAll() {
    FrameworkStudio.collapseAll();
}

function expandAll() {
    FrameworkStudio.expandAll();
}

function resetDecomposition() {
    FrameworkStudio.resetDecomposition();
}

function exportCode() {
    FrameworkStudio.exportCode();
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    FrameworkStudio.init();
});
