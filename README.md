# 简历智能分析工具 (Resume Analyzer)

AI 驱动的简历智能分析工具，支持自动解析简历结构、64+ 岗位知识库精准匹配打分、AI 自主推荐覆盖全行业、深度分析与优化建议。

![项目截图](./screenshots/demo.png)

## 项目背景

传统简历筛选存在三个痛点：

1. **HR 筛选效率低**：每天面对几十份简历，人工判断匹配度耗时且主观，优质候选人容易被遗漏
2. **求职者盲目投递**：不清楚自己的简历适合什么岗位，缺乏针对性优化，投递效率低下
3. **行业覆盖不足**：现有简历工具大多只覆盖互联网技术岗，财务/制造/运营/设计/教育/医疗等非技术专业求职者无法使用

本项目通过 AI 驱动的智能分析，实现从「简历解析 → 岗位匹配 → 深度分析 → 优化建议」的全链路覆盖，支持 64+ 岗位知识库匹配 + AI 自主推荐，覆盖全行业。

## 核心功能

| 功能 | 说明 |
|------|------|
| 📄 简历解析 | 支持粘贴文本、拖拽上传 PDF/Word 文件，AI 自动提取姓名/技能/经历/项目/证书等结构化信息 |
| 🎯 岗位匹配 | 64 个岗位知识库精准匹配 + AI 自主推荐未知方向，覆盖 10+ 行业，评分 0-100 |
| 🔍 深度分析 | 核心优势/能力短板/关键词匹配/STAR 法则经历评估，猎头推荐语风格 |
| ✏️ 优化建议 | 简历改写（含原文对比）/补充项/结构建议/面试问题预测/关键词优化 |
| 📋 历史记录 | 自动保存分析记录，支持查看/删除，前端详情缓存二次秒开 |
| 🖨️ 导出报告 | 浏览器打印另存为 PDF，候选人姓名动态命名，含完整分析报告 |

## 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 前端 | React + TypeScript + Vite + CSS | React 19.2 / Vite 8.0 / TypeScript 6.0 |
| 后端 | Python + FastAPI + SQLAlchemy | Python 3.14 / FastAPI 0.136 / SQLAlchemy 2.0 |
| AI 引擎 | DeepSeek API（OpenAI SDK） | deepseek-chat / openai 2.41 |
| 数据库 | SQLite | — |
| 文件解析 | pdfplumber + python-docx | pdfplumber 0.11 / python-docx 1.2 |

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser :5173                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐  │
│  │ HomePage │ │ JobCard  │ │JobDetail │ │ HistoryList   │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └───────┬───────┘  │
│       └─────────────┴────────────┴───────────────┘          │
│                         │ HTTP                               │
└─────────────────────────┼───────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────────┐
│              FastAPI :8010                                   │
│  ┌──────────────────────┴──────────────────────────────┐    │
│  │                   路由层 (resume.py)                  │    │
│  │  POST /submit  POST /analyze-detail  GET /history    │    │
│  └───┬──────────────┬─────────────────┬────────────────┘    │
│      │              │                 │                      │
│  ┌───▼──────┐ ┌─────▼──────┐ ┌───────▼──────────┐          │
│  │ analyzer │ │  matcher   │ │ detail_service   │          │
│  │ 简历解析  │ │  岗位匹配   │ │ 深度分析+优化建议  │          │
│  └────┬─────┘ └─────┬──────┘ └───────┬──────────┘          │
│       │              │                │                      │
│  ┌────▼──────────────▼────────────────▼──────────┐          │
│  │            ai_client.py (公共调用)              │          │
│  │        30s 超时 · 1 次重试 · 统一日志          │          │
│  └──────────────────────┬────────────────────────┘          │
│                         │                                    │
└─────────────────────────┼───────────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          │                               │
     ┌────▼────┐                   ┌─────▼─────┐
     │ DeepSeek │                   │  SQLite   │
     │   API    │                   │  (本地)    │
     └─────────┘                   └───────────┘
```

**核心流程：**
1. 用户提交简历（文本/文件）→ `analyzer.py` 调用 AI 提取结构化信息
2. 结构化简历 → `matcher.py` 分两步匹配：知识库 64 岗位 + AI 自主推荐，合并排序取 Top 8
3. 点击岗位 → `detail_service.py` 并行发起深度分析 + 优化建议，耗时减半
4. 所有 AI 调用统一走 `ai_client.py`，自带超时/重试/日志

## 项目亮点

### 1. 公共 AI 调用模块
三个服务（解析/匹配/详情）复用同一套调用逻辑 —— `ai_client.py` 统一管理 30s 超时、1 次重试、结构化日志标注，避免代码重复和配置分散。

### 2. 三层 JSON 容错机制
AI 输出格式不稳定是最大痛点。自建解析器按优先级尝试：直接 JSON 解析 → 正则提取 markdown 代码块 → 首尾大括号截取。三层兜底，大幅降低解析失败率。

### 3. 并行调用优化
深度分析和优化建议原本串行 10-15s。通过 `ThreadPoolExecutor` 并行发起两次独立 AI 调用，耗时降至 5-8s，用户体验显著提升。

### 4. 两步智能岗位匹配
- **知识库匹配**：64 个岗位覆盖 10+ 行业（技术/财务/制造/运营/设计/人力/销售/教育/法律/医疗），含行业隔离规则和技术岗位硬性评分上限
- **AI 自主推荐**：知识库未覆盖方向（如酒店经理、短视频编导）由 AI 脱离知识库独立推荐，前端标注「AI推荐」标签

### 5. 前端结果缓存
同一次分析中的岗位详情结果缓存在模块级 Map 中，关闭 Modal 后再次点击同一岗位直接读取缓存，不重复调用 API。

### 6. 前后端类型对齐
后端 Pydantic 模型定义数据结构，前端 TypeScript 类型与之对应。编译期即可发现字段不匹配问题，减少运行时错误。

## 本地运行

### 环境要求
- Python 3.14+
- Node.js 22+
- DeepSeek API Key

### 后端

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install --only-binary :all: -r requirements.txt
cp .env.example .env   # 编辑 .env 填入真实 API Key
uvicorn app.main:app --port 8010 --reload
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 `http://localhost:5173`，粘贴简历或上传 PDF/Word 文件即可体验。

API 文档：`http://localhost:8010/docs`

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | 必填 |
| `DEEPSEEK_BASE_URL` | API 地址 | `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | 模型名称 | `deepseek-chat` |
| `APP_PORT` | 服务端口 | `8010` |
| `DATABASE_URL` | 数据库路径 | `sqlite:///./resume_analyzer.db` |

## 项目结构

```
resume-analyzer/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI 入口，CORS 配置
│   │   ├── core/config.py           # 环境变量管理
│   │   ├── models/resume.py         # Pydantic 数据模型
│   │   ├── api/routes/resume.py     # API 路由（提交/匹配/历史）
│   │   ├── services/
│   │   │   ├── ai_client.py         # 公共 AI 调用（超时+重试）
│   │   │   ├── analyzer.py          # 简历解析服务
│   │   │   ├── matcher.py           # 岗位匹配 + 打分
│   │   │   ├── detail_service.py    # 深度分析 + 优化建议（并行）
│   │   │   ├── file_parser.py       # PDF/Word 文本提取
│   │   │   └── history.py           # 历史记录 CRUD
│   │   ├── db/database.py           # SQLAlchemy 模型
│   │   └── data/jobs.json           # 64 个岗位知识库
│   ├── .env.example                 # 环境变量模板
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── pages/HomePage.tsx       # 首页状态机
│       ├── components/
│       │   ├── ResumeInput.tsx      # 文本/文件双模式输入
│       │   ├── FileUpload.tsx       # 拖拽上传
│       │   ├── JobCard.tsx          # 岗位推荐卡片
│       │   ├── JobDetail.tsx        # 岗位详情 Modal（深度分析+优化建议）
│       │   ├── ResultCard.tsx       # 分析结果展示
│       │   └── HistoryList.tsx      # 历史记录列表
│       ├── services/api.ts         # API 请求封装
│       └── types/resume.ts         # TypeScript 类型定义
└── .gitignore
```

## 后续规划

- [ ] 移动端响应式适配
- [ ] 批量简历上传与分析
- [ ] 面试模拟训练（AI 角色扮演）
- [ ] Docker Compose 一键部署
- [ ] 用户系统（多租户 + 权限隔离）
