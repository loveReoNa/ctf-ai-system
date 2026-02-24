#!/usr/bin/env python3
"""
启动CTF AI MCP服务器
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.mcp_server import CTFMCPServer
from src.utils.logger import setup_global_logging


async def start_server():
    """启动MCP服务器"""
    print("=" * 60)
    print("CTF AI MCP服务器启动")
    print("=" * 60)
    
    # 设置日志
    setup_global_logging(level="INFO")
    
    # 创建服务器实例
    server = CTFMCPServer()
    
    try:
        # 初始化服务器
        print("\n初始化服务器...")
        await server.initialize()
        print("✅ 服务器初始化完成")
        
        # 显示服务器信息
        print("\n服务器信息:")
        print(f"  主机: {config.get('server.host', '127.0.0.1')}")
        print(f"  端口: {config.get('server.port', 8000)}")
        print(f"  工具数量: {len(server.tool_manager.tools)}")
        
        # 列出可用工具
        print("\n可用工具:")
        tools = await server.handle_list_tools()
        for i, tool in enumerate(tools, 1):
            print(f"  {i}. {tool['name']} - {tool['description']}")
        
        print("\n" + "=" * 60)
        print("MCP服务器正在运行...")
        print("按 Ctrl+C 停止服务器")
        print("=" * 60)
        
        # 运行服务器
        await server.run_stdio_server()
        
    except KeyboardInterrupt:
        print("\n\n收到中断信号，关闭服务器...")
    except Exception as e:
        print(f"\n❌ 服务器启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("服务器已关闭")
    return 0


if __name__ == "__main__":
    from src.utils.config_manager import config
    
    # 检查配置
    if not config.validate():
        print("❌ 配置验证失败，请检查配置文件")
        sys.exit(1)
    
    # 运行服务器
    exit_code = asyncio.run(start_server())
    sys.exit(exit_code)