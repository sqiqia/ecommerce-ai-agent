"""适合在 PyCharm 中直接运行的本地服务启动器。"""

import argparse
import socket
from collections.abc import Sequence

import uvicorn


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
PORT_SEARCH_COUNT = 20


def is_port_available(host: str, port: int) -> bool:
    """通过尝试绑定判断端口是否真的可用，包括 Windows 幽灵占用。"""

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_socket:
        try:
            test_socket.bind((host, port))
        except OSError:
            return False
    return True


def find_available_port(
    host: str = DEFAULT_HOST,
    start_port: int = DEFAULT_PORT,
    search_count: int = PORT_SEARCH_COUNT,
) -> int:
    """从指定端口开始，返回第一个可以正常绑定的端口。"""

    for port in range(start_port, start_port + search_count):
        if is_port_available(host, port):
            return port
    end_port = start_port + search_count - 1
    raise RuntimeError(f"端口 {start_port} 到 {end_port} 都已被占用")


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="启动电商运营自动化 Agent")
    parser.add_argument("--host", default=DEFAULT_HOST, help="监听地址")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="优先使用的端口")
    parser.add_argument(
        "--reload",
        action="store_true",
        help="开发时自动重载代码；日常运行不建议开启",
    )
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    args = build_argument_parser().parse_args(arguments)
    try:
        selected_port = find_available_port(args.host, args.port)
    except RuntimeError as exc:
        print(f"\n启动失败：{exc}")
        print("请关闭旧服务，或使用 --port 指定其他起始端口。\n")
        return 1

    if selected_port != args.port:
        print(f"\n端口 {args.port} 已被占用，已自动切换到 {selected_port}。")
    print("\n电商运营自动化 Agent 即将启动：")
    print(f"  中文工作台：http://{args.host}:{selected_port}")
    print(f"  健康检查：http://{args.host}:{selected_port}/health")
    print(f"  接口文档：http://{args.host}:{selected_port}/docs")
    print("  停止服务：在运行窗口按 Ctrl+C，或点击 PyCharm 红色方块。\n")

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=selected_port,
        reload=args.reload,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
