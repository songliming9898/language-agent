# 小学生英语口语对练 Agent

面向小学三年级学生的 AI 英语口语对练系统，支持课程跟读和自由对话。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + Vite + 原生 CSS (移动端 H5) |
| 后端 | Python FastAPI |
| 数据库 | MySQL 8.0 |
| LLM | DeepSeek (兼容 OpenAI API) |
| TTS | Microsoft Edge TTS (免费) |
| ASR | OpenAI Whisper (本地) |

## 项目结构

```
language_agent/
├── backend/                # Python 后端
│   ├── main.py            # FastAPI 入口
│   ├── config.py          # 配置管理
│   ├── requirements.txt   # Python 依赖
│   ├── db/                # 数据库
│   │   ├── connection.py  # 连接管理
│   │   └── init.sql       # 建表 + 初始数据
│   ├── models/            # SQLAlchemy 模型
│   ├── routers/           # API 路由
│   └── services/          # 业务服务 (LLM/TTS/ASR/Memory)
├── frontend/              # React 前端
│   └── src/
│       ├── pages/         # 6 个页面
│       ├── hooks/         # 录音/播放 Hook
│       └── services/      # API 封装
├── deploy/                # 部署配置
│   ├── deploy.sh          # 一键部署脚本
│   ├── nginx.conf         # Nginx 配置
│   └── kids-english.service  # Systemd 服务
└── docs/
    └── 概要设计文档.md
```

## 本地开发

### 1. 后端

```bash
cd backend
pip install -r requirements.txt
pip install edge-tts  # TTS 依赖

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入数据库密码和 LLM API Key

# 初始化数据库
mysql -u root -p < db/init.sql

# 启动后端
python main.py
# 访问 http://localhost:8003/docs 查看 API 文档
```

### 2. 前端

```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:5173
```

## 部署到阿里云 ECS

```bash
# 1. 上传代码到服务器
scp -r language_agent/ root@your-ecs-ip:/opt/

# 2. 创建 .env 配置
cat > /opt/kids-english/.env << EOF
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=kids_english
LLM_API_KEY=sk-your-deepseek-key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
EOF

# 3. 执行部署脚本
chmod +x /opt/kids-english/deploy/deploy.sh
/opt/kids-english/deploy/deploy.sh
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/courses | 课程列表 |
| GET | /api/courses/{id}/units | 单元列表 |
| GET | /api/courses/units/{id}/sentences | 句子列表 |
| POST | /api/practice/evaluate | 跟读评分 |
| POST | /api/practice/chat | 自由对话 |
| POST | /api/practice/session/start | 开始会话 |
| GET | /api/practice/session/{id}/history | 对话历史 |
| GET | /api/progress | 学习进度 |
| GET | /api/memory/summary | AI 记忆 |
