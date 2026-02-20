# Web Server - 编程教学 Agent Web 界面

这是一个基于 FastAPI 的 Web 服务器，提供编程教学 Agent 的交互式 Web 界面。

## 功能特性

- **三种教学 Agent**：
  - 费曼学习法：深入理解编程概念
  - 反向图灵测试：评估编程思维能力
  - 苏格拉底教学法：引导调试代码问题

- **实时流式响应**：模拟打字效果的流式输出
- **会话管理**：支持多会话、会话重置、历史记录
- **学习进度追踪**：显示 Agent 特定的学习进度和能力评估

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置

确保在项目根目录有 `.env` 文件，配置以下内容：

```bash
API_BASE=https://api.openai.com/v1  # 或其他兼容的 API 地址
API_KEY=your-api-key-here
MODEL=gpt-3.5-turbo  # 或其他模型
```

## 运行服务器

```bash
cd web_server
python backend.py
```

服务器启动后：
- **Web 界面**: http://localhost:8020
- **API 文档**: http://localhost:8020/docs

## API 端点

### POST /api/chat
普通聊天接口（非流式）

**请求体**:
```json
{
  "agent_type": "feynman",
  "message": "请解释什么是递归",
  "session_id": "optional-session-id"
}
```

### POST /api/chat/stream
流式聊天接口（推荐使用）

**请求体**: 同上

**响应**: Server-Sent Events (SSE) 格式

### GET /api/session/{session_id}/info
获取会话信息

### POST /api/session/{session_id}/reset
重置会话

### DELETE /api/session/{session_id}
删除会话

## 项目结构

```
web_server/
├── backend.py          # FastAPI 后端服务器
├── requirements.txt    # Python 依赖
├── static/
│   ├── index.html      # 主页面
│   ├── style.css       # 样式文件
│   └── app.js          # 前端逻辑
└── README.md           # 本文件
```

## 技术栈

- **后端**: FastAPI + Uvicorn
- **前端**: 原生 HTML/CSS/JavaScript
- **AI**: OpenAI 兼容 API

## 常见问题

**Q: 启动后无法连接 API？**
A: 检查 `.env` 文件是否在项目根目录，配置是否正确。

**Q: 切换 Agent 后消息丢失？**
A: 这是正常行为，每个 Agent 类型有独立的会话。

**Q: 流式响应卡住？**
A: 可能是网络问题，刷新页面重新开始。
