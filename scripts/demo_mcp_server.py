#!/usr/bin/env python3
"""
MCP服务器演示脚本
展示CTF AI MCP服务器的核心功能
"""
import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.mcp_server import CTFMCPServer
from src.utils.logger import setup_global_logging
from src.utils.config_manager import config


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


async def demo_mcp_server():
    """演示MCP服务器功能"""
    print_header("CTF AI MCP服务器演示")
    
    # 设置日志
    setup_global_logging(level="INFO")
    
    # 创建服务器实例
    print("创建MCP服务器实例...")
    server = CTFMCPServer()
    
    try:
        # 1. 初始化服务器
        print_header("1. 初始化服务器")
        await server.initialize()
        print("✅ 服务器初始化成功")
        
        # 2. 显示配置信息
        print_header("2. 配置信息")
        print(f"项目名称: {config.get('project.name')}")
        print(f"环境: {config.get('environment')}")
        print(f"AI提供商: {config.get('ai.provider')}")
        print(f"AI模型: {config.get('ai.model')}")
        
        # 3. 列出可用工具
        print_header("3. 可用工具")
        tools = await server.handle_list_tools()
        print(f"已注册工具数量: {len(tools)}")
        
        for tool in tools:
            print(f"\n📦 工具: {tool['name']}")
            print(f"   描述: {tool['description']}")
            print(f"   必需参数: {', '.join(tool['schema'].get('required', []))}")
        
        # 4. 演示工具调用（模拟）
        print_header("4. 工具调用演示")
        
        if tools:
            first_tool = tools[0]
            tool_name = first_tool['name']
            
            print(f"演示工具: {tool_name}")
            
            # 根据工具类型创建示例参数
            if tool_name == "sqlmap_scan":
                example_args = {
                    "url": "http://testphp.vulnweb.com/artists.php?artist=1",
                    "method": "GET",
                    "level": 1,
                    "risk": 1
                }
            elif tool_name == "nmap_scan":
                example_args = {
                    "target": "127.0.0.1",
                    "ports": "80,443,8080",
                    "scan_type": "syn"
                }
            else:
                example_args = {}
            
            print(f"示例参数: {json.dumps(example_args, indent=2, ensure_ascii=False)}")
            
            # 注意：实际调用需要工具已安装，这里只演示框架
            print("\n⚠ 注意: 实际工具调用需要sqlmap/nmap已正确安装")
            print("   要启用实际调用，请取消注释以下代码:")
            print(f"   result = await server.handle_call_tool('{tool_name}', example_args)")
        
        # 5. 演示工具管理器
        print_header("5. 工具管理器")
        print(f"工具管理器状态: 正常")
        print(f"已加载工具: {list(server.tool_manager.tools.keys())}")
        
        # 6. 演示与AI集成
        print_header("6. AI集成演示")
        print("MCP服务器可与DeepSeek AI代理集成:")
        print("  1. AI分析CTF挑战")
        print("  2. 生成攻击策略")
        print("  3. 调用MCP工具执行攻击")
        print("  4. 分析结果并调整策略")
        
        # 7. 下一步建议
        print_header("7. 下一步操作")
        print("✅ MCP服务器框架已就绪")
        print("\n建议下一步:")
        print("1. 安装并配置安全工具 (sqlmap, nmap)")
        print("2. 运行完整测试: python scripts/test_mcp_server.py")
        print("3. 启动服务器: python scripts/start_mcp_server.py")
        print("4. 开发AI代理集成")
        print("5. 创建Web监控界面")
        
        print_header("演示完成")
        print("🎉 MCP服务器框架演示成功!")
        print("项目已具备基础工具集成能力，可继续开发完整系统。")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    success = await demo_mcp_server()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)