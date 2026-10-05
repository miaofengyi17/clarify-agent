"""
启动入口。
用 `python -m clarify_agent` 即可启动服务。
"""
import uvicorn
from .config import config


def main():
    """启动 FastAPI 服务器。"""
    uvicorn.run(
        "clarify_agent.server:app",     # FastAPI 应用路径
        host=config.host,               # 监听地址
        port=config.port,               # 监听端口
        log_level=config.log_level,     # 日志级别
        reload=False,                   # 生产环境不开热重载
    )


if __name__ == "__main__":
    main()