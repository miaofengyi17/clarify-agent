# 使用轻量 Python 镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 先装依赖（利用缓存加速）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制源码
COPY src/ ./src/
COPY pyproject.toml .

# 安装项目本身
RUN pip install -e .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "-m", "clarify_agent"]