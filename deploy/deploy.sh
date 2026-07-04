#!/bin/bash
# ============================================
# 阿里云 ECS 部署脚本
# ============================================
set -e

APP_DIR="/opt/kids-english"
PYTHON_BIN="python3"
VENV_DIR="$APP_DIR/venv"

echo "🚀 开始部署 Kids English Agent..."

# 1. 创建目录
mkdir -p $APP_DIR

# 2. 复制后端
echo "📦 部署后端..."
cp -r backend $APP_DIR/
cd $APP_DIR/backend

# 3. 创建虚拟环境
if [ ! -d "$VENV_DIR" ]; then
    $PYTHON_BIN -m venv $VENV_DIR
fi
source $VENV_DIR/bin/activate

# 4. 安装依赖
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
pip install edge-tts -i https://mirrors.aliyun.com/pypi/simple/

# 5. 配置环境变量（从 .env 文件加载）
if [ -f "$APP_DIR/.env" ]; then
    export $(cat $APP_DIR/.env | grep -v '^#' | xargs)
fi

# 6. 初始化数据库
echo "🗄️ 初始化数据库..."
mysql -u${DB_USER:-root} -p${DB_PASSWORD} < db/init.sql 2>/dev/null || echo "数据库可能已存在，跳过创建"

# 7. 启动后端 (使用 systemd 或 supervisor)
echo "▶️ 启动后端服务..."

# 复制 systemd 服务文件
cp ../deploy/kids-english.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable kids-english
systemctl restart kids-english

# 8. 部署前端
echo "🎨 部署前端..."
cd $APP_DIR
cp -r frontend $APP_DIR/
cd $APP_DIR/frontend

# 安装 Node 依赖并构建
npm install --registry=https://registry.npmmirror.com
npm run build

# 9. 配置 Nginx
echo "🔧 配置 Nginx..."
cp ../deploy/nginx.conf /etc/nginx/sites-available/kids-english 2>/dev/null || \
cp ../deploy/nginx.conf /etc/nginx/conf.d/kids-english.conf
nginx -t && systemctl reload nginx

echo "✅ 部署完成！"
echo "访问地址: http://$(curl -s ifconfig.me)"
