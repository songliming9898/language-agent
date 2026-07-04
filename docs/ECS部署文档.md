# 阿里云 ECS 部署文档

## 环境要求

| 组件 | 版本 | 说明 |
|------|------|------|
| 操作系统 | CentOS 7+ / Ubuntu 20.04+ | |
| Python | 3.10+ | 后端运行环境 |
| Node.js | 18+ | 前端构建 |
| MySQL | 8.0 | 数据库 |
| Nginx | 1.20+ | 反向代理 + 静态文件 |
| Git | 2.0+ | 拉取代码 |

---

## 一、基础环境安装

### 1.1 安装 Python 3.10+

```bash
# CentOS
yum install -y python3 python3-pip python3-devel

# Ubuntu
apt update && apt install -y python3 python3-pip python3-venv
```

### 1.2 安装 Node.js 18+

```bash
# 使用 NodeSource
curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -  # CentOS
# 或
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -  # Ubuntu

apt install -y nodejs  # 或 yum install -y nodejs
node -v && npm -v      # 验证
```

### 1.3 安装 MySQL 8.0

```bash
# CentOS
yum install -y mysql-server
systemctl start mysqld
systemctl enable mysqld

# 获取初始密码（CentOS）
grep 'temporary password' /var/log/mysqld.log

# 修改密码
mysql -u root -p
ALTER USER 'root'@'localhost' IDENTIFIED BY 'YourNewPassword123!';
FLUSH PRIVILEGES;
```

```bash
# Ubuntu
apt install -y mysql-server
systemctl start mysql
systemctl enable mysql

# 设置密码
mysql
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'YourNewPassword123!';
FLUSH PRIVILEGES;
```

### 1.4 安装 Nginx

```bash
# CentOS
yum install -y nginx

# Ubuntu
apt install -y nginx

systemctl start nginx
systemctl enable nginx
```

### 1.5 安装 Git + FFmpeg（音频处理依赖）

```bash
yum install -y git ffmpeg    # CentOS
# 或
apt install -y git ffmpeg    # Ubuntu
```

---

## 二、部署步骤

### 2.1 克隆代码

```bash
cd /opt
git clone https://github.com/songliming9898/language-agent.git
mv language-agent kids-english
cd /opt/kids-english
```

### 2.2 初始化数据库

```bash
mysql -u root -p < backend/db/init.sql
```

验证：
```bash
mysql -u root -p -e "USE kids_english; SHOW TABLES;"
# 应看到 6 张表：courses, course_units, sentences, conversations, user_progress, memory_records
```

### 2.3 配置环境变量

```bash
cat > /opt/kids-english/.env << 'EOF'
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

### 2.4 安装 Python 依赖

```bash
cd /opt/kids-english/backend
python3 -m venv /opt/kids-english/venv
source /opt/kids-english/venv/bin/activate

# 使用阿里云镜像加速
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
pip install edge-tts -i https://mirrors.aliyun.com/pypi/simple/
```

### 2.5 构建前端

```bash
cd /opt/kids-english/frontend

# 使用国内镜像加速
npm config set registry https://registry.npmmirror.com
npm install
npm run build
```

构建产物在 `frontend/dist/` 目录。

### 2.6 配置 Nginx

```bash
cp /opt/kids-english/deploy/nginx.conf /etc/nginx/conf.d/kids-english.conf

# 如果有域名，修改 server_name
vi /etc/nginx/conf.d/kids-english.conf

# 检查配置
nginx -t

# 重载
systemctl reload nginx
```

### 2.7 配置 Systemd 服务

```bash
cp /opt/kids-english/deploy/kids-english.service /etc/systemd/system/

systemctl daemon-reload
systemctl enable kids-english
systemctl start kids-english
```

### 2.8 检查服务状态

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

```bash
# 阿里云 ECS 需要在「安全组」中开放 80 端口
# 如果使用 firewalld：
firewall-cmd --zone=public --add-port=80/tcp --permanent
firewall-cmd --reload
```

### 3.2 MySQL 安全加固

```bash
# 仅本地访问
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
cd /opt/kids-english
git pull
source /opt/kids-english/venv/bin/activate
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
# 检查 dist 目录
ls /opt/kids-english/frontend/dist/
# 重新构建
cd /opt/kids-english/frontend && npm run build
```

### Q: API 502 错误？
```bash
# 检查后端是否运行
systemctl status kids-english
journalctl -u kids-english -n 50
# 确认端口
ss -tlnp | grep 8003
```

### Q: LLM 调用失败？
```bash
# 检查 API Key
cat /opt/kids-english/.env | grep LLM
# 测试连通性
curl -H "Authorization: Bearer sk-your-key" https://api.deepseek.com/v1/models
```

### Q: TTS 不发声？
```bash
# Edge-TTS 需要网络连接微软服务
# 测试
python3 -c "import edge_tts; print('ok')"
```
