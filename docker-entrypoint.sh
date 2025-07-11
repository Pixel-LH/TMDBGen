#!/bin/bash

# 设置错误时退出
set -e

# 打印启动信息
echo "🚀 启动 TMDB Gen 服务..."

# 检查必要的环境变量
if [ -z "$ACCESS_TOKEN" ]; then
    echo "❌ 错误: ACCESS_TOKEN 环境变量未设置"
    echo "请设置 TMDB API Access Token"
    exit 1
fi

# 设置默认值
export SERVER_PORT=${SERVER_PORT:-23333}
export HTTP_PROXY=${HTTP_PROXY:-}

# 启动 nginx 服务 (后台运行)
echo "🌐 启动 nginx 服务 (端口 80)..."
nginx -g "daemon on;"
NGINX_PID=$(cat /var/run/nginx.pid)

# 等待 nginx 启动
sleep 2

# 启动后端服务
echo "🔧 启动后端 API 服务 (端口 ${SERVER_PORT})..."
cd /app

# 创建优雅关闭处理函数
cleanup() {
    echo "🛑 收到停止信号，正在关闭服务..."
    nginx -s quit 2>/dev/null || true
    exit 0
}

# 设置信号处理
trap cleanup SIGTERM SIGINT

# 以 app 用户身份启动后端服务
exec su -s /bin/bash app -c "python main.py" 