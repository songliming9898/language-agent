# 阿里云 ECS 部署文档

> **项目路径**: `/opt/language/language-agent`
> **Python 虚拟环境**: `/opt/language/langvenv`
> **操作系统**: Alibaba Cloud Linux 3 (OpenAnolis Edition)

## 环境要求

| 组件 | 版本 | 说明 |
|------|------|------|
| 操作系统 | Alibaba Cloud Linux 3 / CentOS 8+ | |
| Python | 3.10+ | 后端运行环境 |
| Node.js | 18+ | 前端构建 |
| MySQL | 8.0 | 数据库 |
| Nginx | 1.20+ | 反向代理 + 静态文件 |
| Git | 2.0+ | 拉取代码 |

---

## 一、基础环境安装

### 1.1 安装 Python 3.10+

```bash
# Alibaba Cloud Linux 3
yum install -y python3 python3-pip python3-devel
```

### 1.2 安装 Node.js 18+

```bash
# 使用 NodeSource
curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -
yum install -y nodejs
node -v && npm -v      # 验证
```

### 1.3 安装 MySQL 8.0

```bash
yum install -y mysql-server
systemctl start mysqld
systemctl enable mysqld

# 获取初始密码
grep 'temporary password' /var/log/mysqld.log

# 修改密码
mysql -u root -p
ALTER USER 'root'@'localhost' IDENTIFIED BY 'YourNewPassword123!';
FLUSH PRIVILEGES;
```

### 1.4 安装 Nginx

```bash
yum install -y nginx
systemctl start nginx
systemctl enable nginx
```

### 1.5 安装 FFmpeg（音频处理依赖）

```bash
# 先装 EPEL 源
yum install -y epel-release
yum install -y ffmpeg

# 如果 EPEL 没有，用 RPM Fusion
yum install -y --nogpgcheck https://mirrors.rpmfusion.org/free/el/rpmfusion-free-release-8.noarch.rpm
yum install -y ffmpeg
```

---

## 二、部署步骤

### 2.1 克隆代码

```bash
mkdir -p /opt/language
cd /opt/language
git clone https://github.com/songliming9898/language-agent.git
cd /opt/language/language-agent
```

### 2.2 创建 Python 虚拟环境

```bash
python3 -m venv /opt/language/langvenv
source /opt/language/langvenv/bin/activate
```

### 2.3 安装 Python 依赖

```bash
cd /opt/language/language-agent/backend
source /opt/language/langvenv/bin/activate

# 使用阿里云镜像加速
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
pip install edge-tts -i https://mirrors.aliyun.com/pypi/simple/
```

### 2.4 初始化数据库

```bash
mysql -u root -p < /opt/language/language-agent/backend/db/init.sql
```

验证：
```bash
mysql -u root -p -e "USE kids_english; SHOW TABLES;"
# 应看到 6 张表：courses, course_units, sentences, conversations, user_progress, memory_records
```

### 2.5 配置环境变量

```bash
cat > /opt/language/language-agent/.env << 'EOF'
# 数据库
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=YourNewPassword123!
DB_NAME=kids_english

# LLM (DeepSeek)
LLM_API_KEY=sk-your-deepseek-api-key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat

# TTS
TTS_PROVIDER=edge
EOF
```

> 替换 `YourNewPassword123!` 和 `sk-your-deepseek-api-key` 为实际值。

### 2.6 构建前端

```bash
cd /opt/language/language-agent/frontend

# 使用国内镜像加速
npm config set registry https://registry.npmmirror.com
npm install
npm run build
```

构建产物在 `frontend/dist/` 目录。

### 2.7 配置 Nginx

```bash
cp /opt/language/language-agent/deploy/nginx.conf /etc/nginx/conf.d/kids-english.conf

# 如果有域名，修改 server_name
vi /etc/nginx/conf.d/kids-english.conf

# 检查配置
nginx -t

# 重载
systemctl reload nginx
```

### 2.8 配置 Systemd 服务

先修改服务文件中的路径：

```bash
cat > /etc/systemd/system/kids-english.service << 'EOF'
[Unit]
Description=Kids English Speaking Agent
After=network.target mysql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/language/language-agent/backend
EnvironmentFile=/opt/language/language-agent/.env
ExecStart=/opt/language/langvenv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8003
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable kids-english
systemctl start kids-english
```

### 2.9 检查服务状态

```bash
# 后端
systemctl status kids-english

# 查看日志
journalctl -u kids-english -f

# 测试 API
curl http://127.0.0.1:8003/api/health
# 返回 {"status":"ok","service":"kids-english-agent"}
```

---

## 三、安全配置

### 3.1 开放防火墙端口

阿里云 ECS 需要在「安全组」中开放 80 端口。

```bash
# 如果使用 firewalld：
firewall-cmd --zone=public --add-port=80/tcp --permanent
firewall-cmd --reload
```

### 3.2 MySQL 安全加固

```bash
mysql -u root -p -e "
  DELETE FROM mysql.user WHERE User='';
  DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1');
  FLUSH PRIVILEGES;
"
```

---

## 四、常用运维命令

```bash
# 重启后端
systemctl restart kids-english

# 查看后端日志
journalctl -u kids-english -f --no-pager

# 重新部署（拉代码 → 装依赖 → 构建前端 → 重启）
cd /opt/language/language-agent
git pull
source /opt/language/langvenv/bin/activate
pip install -r backend/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
cd frontend && npm install && npm run build && cd ..
systemctl restart kids-english
systemctl reload nginx
```

---

## 五、验证

浏览器访问 `http://你的ECS公网IP`，应看到：

1. 首页 — 学习进度卡片 + 三个功能入口
2. 课程对练 — 选择课程 → 单元 → 录音跟读 → 评分
3. 自由对练 — 文字/语音对话
4. 学习报告 — 进度 + AI 记忆

---

## 六、常见问题

### Q: 前端页面空白？
```bash
ls /opt/language/language-agent/frontend/dist/
cd /opt/language/language-agent/frontend && npm run build
```

### Q: API 502 错误？
```bash
systemctl status kids-english
journalctl -u kids-english -n 50
ss -tlnp | grep 8003
```

### Q: LLM 调用失败？
```bash
cat /opt/language/language-agent/.env | grep LLM
curl -H "Authorization: Bearer sk-your-key" https://api.deepseek.com/v1/models
```

### Q: TTS 不发声？
```bash
source /opt/language/langvenv/bin/activate
python3 -c "import edge_tts; print('ok')"
```
