#!/usr/bin/env python3
"""
测试MCP服务器框架
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.mcp_server import CTFMCPServer
from src.utils.logger import setup_global_logging


async def test_mcp_server():
    """测试MCP服务器"""
    print("=" * 50)
    print("测试MCP服务器框架")
    print("=" * 50)
    
    # 设置日志
    setup_global_logging(level="INFO")
    
    # 创建服务器实例
    server = CTFMCPServer()
    
    try:
        # 初始化服务器
        print("\n1. 初始化MCP服务器...")
        await server.initialize()
        print("   ✅ 服务器初始化成功")
        
        # 测试列出工具
        print("\n2. 测试列出工具...")
        tools = await server.handle_list_tools()
        print(f"   可用工具数量: {len(tools)}")
        for tool in tools:
            print(f"   - {tool['name']}: {tool['description']}")
        
        # 测试工具管理器
        print("\n3. 测试工具管理器...")
        tool_names = list(server.tool_manager.tools.keys())
        print(f"   已注册工具: {tool_names}")
        
        if tool_names:
            # 测试获取工具信息
            first_tool = tool_names[0]
            tool = server.tool_manager.get_tool(first_tool)
            if tool:
                print(f"   工具 '{first_tool}' 描述: {tool.description}")
                print(f"   工具模式: {tool.get_schema()}")
        
        # 测试SQLMap包装器连接
        print("\n4. 测试SQLMap包装器连接...")
        from src.mcp_server.tools import sqlmap_wrapper
        connected = await sqlmap_wrapper.test_connection()
        if connected:
            print("   ✅ SQLMap连接测试成功")
        else:
            print("   ⚠ SQLMap连接测试失败（可能未安装或路径不正确）")
        
        print("\n" + "=" * 50)
        print("MCP服务器框架测试完成！")
        print("\n下一步:")
        print("1. 确保sqlmap和nmap已正确安装")
        print("2. 运行MCP服务器: python src/mcp_server/server.py --server")
        print("3. 开发前端界面集成")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    success = await test_mcp_server()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)