#!/bin/bash
# ============================================
# 阿里云 ECS 部署脚本
# 项目路径: /opt/language/language-agent
# 虚拟环境: /opt/language/langvenv
# ============================================
set -e

APP_DIR="/opt/language/language-agent"
VENV_DIR="/opt/language/langvenv"

echo "🚀 开始部署 Kids English Agent..."
echo "   项目目录: $APP_DIR"
echo "   虚拟环境: $VENV_DIR"

# 1. 创建虚拟环境（如已存在则跳过）
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv $VENV_DIR
fi
source $VENV_DIR/bin/activate

# 2. 安装/更新 Python 依赖
echo "📦 安装 Python 依赖..."
cd $APP_DIR/backend
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
pip install edge-tts -i https://mirrors.aliyun.com/pypi/simple/

# 3. 初始化数据库
echo "🗄️ 初始化数据库..."
if [ -f "$APP_DIR/.env" ]; then
    export $(cat $APP_DIR/.env | grep -v '^#' | xargs)
fi
mysql -u${DB_USER:-root} -p${DB_PASSWORD} < $APP_DIR/backend/db/init.sql 2>/dev/null || echo "数据库可能已存在，跳过创建"

# 4. 构建前端
echo "🎨 构建前端..."
cd $APP_DIR/frontend
npm install --registry=https://registry.npmmirror.com
npm run build

# 5. 配置 Systemd 服务
echo "⚙️ 配置 Systemd 服务..."
cat > /etc/systemd/system/kids-english.service << 'SERVICEEOF'
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
SERVICEEOF

systemctl daemon-reload
systemctl enable kids-english
systemctl restart kids-english

# 6. 配置 Nginx
echo "🔧 配置 Nginx..."
cp $APP_DIR/deploy/nginx.conf /etc/nginx/conf.d/kids-english.conf
nginx -t && systemctl reload nginx

echo "✅ 部署完成！"
echo "   访问地址: http://$(curl -s ifconfig.me)"
