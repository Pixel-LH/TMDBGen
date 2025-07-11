# 使用 Python 3.11 作为基础镜像
FROM python:3.11-slim as base

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    nginx \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY main.py gen.py ./
COPY frontend/ ./frontend/
COPY nginx.conf /etc/nginx/nginx.conf

RUN mkdir -p /var/log/nginx /var/cache/nginx /var/run && \
    touch /var/run/nginx.pid && \
    chown -R www-data:www-data /var/log/nginx /var/cache/nginx /var/run/nginx.pid

RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app

EXPOSE 80

# 启动脚本
COPY --chown=app:app docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

# 默认启动命令
CMD ["/app/docker-entrypoint.sh"] 