# AI-for-Education

一个可独立运行的教学辅导系统目录。当前目录已经收拢了知识点题库生成、作业题预生成、学生端辅导与 `/admin` 管理后台所需的主要资产，不再默认依赖外层仓库目录结构。

## 推荐启动方式

### 本地启动

1. 准备本地依赖
   - Python 3.10+
   - Redis
   - MySQL（默认端口 `3307`）

2. 配置环境变量
   - 编辑当前目录下的 `.env`
   - 至少配置模型相关参数与数据库连接信息

3. 启动应用
   ```powershell
   .\start_local.ps1
   ```
   或
   ```powershell
   .\.venv\Scripts\python.exe .\app.py
   ```

4. 访问地址
   - 学生端: [http://localhost:5000](http://localhost:5000)
   - 管理后台: [http://localhost:5000/admin](http://localhost:5000/admin)

### Docker 启动

仍然保留 Docker 方式，但当前更推荐本地模式调试。

```powershell
.\start.ps1
```

## 目录结构

### 核心应用
- `app.py`: Flask 主入口
- `app_xiaohang_enhanced.py`: 学生端增强辅导逻辑
- `config.py`: LLM 配置与提示词
- `models.py`: 数据模型

### 预生成资产
- `app_pregenerator/problem_bank.json`: 知识点题本地题库
- `app_pregenerator/batch_generator.py`: 知识点题生成流水线
- `app_pregenerator/homework_pregenerator.py`: 作业题预生成脚本
- `app_pregenerator/homework_guidance_bank.json`: 作业题预生成资产

### 题库检索
- `retriever.py`: 英文题库检索器
- `leetcode_db.json`: 英文种子题库

### 管理后台
- `admin/admin_panel.py`: `/admin` 后端接口
- `admin/admin_settings.json`: 后台模型配置与密码
- `admin/admin_batch_jobs.json`: 批处理任务历史
- `static/admin/index.html`: 管理后台页面
- `static/admin/admin.js`: 管理后台前端逻辑

## 管理后台说明

`/admin` 支持：

- 配置模型 `base_url / api_key / model`
- 管理知识点题库
- 管理作业题库
- 单题生成
- 知识点批量补生成
- 作业题批量生成
- 查看批处理历史和实时终端日志

默认管理员密码：

```text
zgl666
```

可以在 `/admin` 中修改，或通过环境变量 `ADMIN_PASSWORD` 覆盖默认值。

## 预生成脚本

### 生成一整套作业题教学资产

```powershell
.\.venv\Scripts\python.exe .\app_pregenerator\homework_pregenerator.py --homework-key homework0 --model gpt-5.4 --overwrite
```

### 只生成某一道作业题

```powershell
.\.venv\Scripts\python.exe .\app_pregenerator\homework_pregenerator.py --homework-key homework0 --problem-index 0 --model gpt-5.4 --overwrite
```

### 知识点题批量生成

推荐直接通过 `/admin` 操作；后台已经接到 `app_pregenerator/batch_generator.py` 的流水线。

## 环境变量

常用变量：

- `REDIS_HOST`
- `REDIS_PORT`
- `REDIS_DB`
- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE`
- `AKR_BASE_URL`
- `AKR_API_KEY`
- `ADMIN_MODEL`
- `ADMIN_PASSWORD`

## 说明

- 当前目录内部已经包含知识点题库生成所需的 `problem_bank.json / batch_generator.py / retriever.py / leetcode_db.json`
- 当前目录内部也已经包含作业题预生成所需的脚本与资产
- 仍然可能存在 `.idea`、`.venv`、`__pycache__` 这类开发环境文件，其中的绝对路径不影响运行时逻辑

