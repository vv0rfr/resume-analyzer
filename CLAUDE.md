# Resume Analyzer — 简历智能分析工具

FastAPI + React/TypeScript 全栈项目，AI 驱动的简历智能分析与岗位匹配。

## 架构速览

```
resume-analyzer/
├── backend/   (Python 3.14 + FastAPI + uvicorn, port 8010)
└── frontend/  (React 19 + TypeScript + Vite, port 5173)
```

- **AI 引擎**：DeepSeek API（deepseek-chat 模型，通过 OpenAI 兼容 SDK 调用）
- **数据库**：SQLite（`backend/resume_analyzer.db`）
- **文件解析**：pdfplumber + python-docx
- **前端状态**：无全局状态管理，通过 props 和 API response 驱动

## 命令速查

```bash
# 后端
cd backend && venv/Scripts/activate
uvicorn app.main:app --port 8010 --reload      # 启动（--reload 自动检测文件变更）

# 前端
cd frontend
npm run dev              # Vite 开发服务器
npm run build            # 生产构建

# API 文档
open http://localhost:8010/docs    # Swagger UI
```

## 关键规则

1. **两步匹配**：`matcher.py` 先做知识库匹配（64 个岗位），再做自主推荐（不依赖知识库），两者合并按分数排序
2. **行业隔离**：prompt 中必须显式禁止将非技术简历匹配到技术岗位
3. **is_custom 字段**：自主推荐的岗位 `is_custom=true`，知识库匹配的 `is_custom=false`，前端据此显示「AI推荐」标签
4. **AI 调用**：所有 DeepSeek 请求统一走 `app/services/ai_client.py` 的 `call_deepseek()`，自带 30s 超时 + 1 次重试
5. **前端端口**：Vite 默认 5173，知识库匹配允许的 CORS origin 在 `config.py` 中配置

## API 路由

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/resume/submit` | 提交简历（文本或文件），返回解析 + 岗位匹配 |
| POST | `/api/resume/analyze-detail` | 针对指定岗位做深度分析 + 优化建议 |
| GET | `/api/resume/history` | 历史记录列表 |
| GET | `/api/resume/history/{id}` | 历史记录详情 |
| DELETE | `/api/resume/history/{id}` | 删除历史记录 |
| GET | `/api/health` | 健康检查 |

## 数据文件

- `backend/app/data/jobs.json` — 64 个岗位知识库，覆盖技术/财务/制造/运营/设计/人力/销售/教育/法律/医疗等行业，每个岗位含 `job_id`、`core_skills`、`nice_to_have`、`levels` 等字段
- `backend/.env` — DeepSeek API Key + 服务端口配置（不入 git）
- `backend/resume_analyzer.db` — SQLite 数据库（不入 git）

## 深入文档

| 文档 | 说明 |
|------|------|
| `README.md` | 功能概览 + 快速开始 |
| `backend/app/services/matcher.py` | 岗位匹配核心逻辑（知识库 + 自主推荐） |
| `backend/app/services/analyzer.py` | 简历解析服务（AI 提取结构化信息） |
| `backend/app/services/ai_client.py` | 公共 AI 调用模块（超时 + 重试） |
| `backend/app/core/config.py` | 配置（环境变量 + CORS origins） |
| `frontend/src/components/JobCard.tsx` | 岗位卡片（含 AI推荐 标签） |
