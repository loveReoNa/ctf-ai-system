#!/usr/bin/env python3
"""
临时修复脚本 - 直接测试工具执行
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.mcp_server.server import CTFMCPServer
from urllib.parse import urlparse


async def test_tools_directly():
    """直接测试工具执行"""
    print("🔧 直接测试工具执行...")
    
    # 创建MCP服务器
    mcp_server = CTFMCPServer()
    await mcp_server.initialize()
    
    # 测试目标
    test_url = "http://e579ae13-2404-401e-ac7b-17d68115f1a9.node5.buuoj.cn:81"
    
    # 提取主机名
    parsed = urlparse(test_url)
    hostname = parsed.hostname
    port = parsed.port or 80
    
    print(f"原始URL: {test_url}")
    print(f"提取的主机名: {hostname}")
    print(f"端口: {port}")
    
    # 测试Nmap工具
    print("\n1. 测试Nmap工具...")
    nmap_args = {
        "target": hostname,
        "ports": str(port),
        "scan_type": "syn"
    }
    
    try:
        nmap_result = await mcp_server.handle_call_tool("nmap_scan", nmap_args)
        print(f"  Nmap执行结果: {nmap_result.get('success', False)}")
        if nmap_result.get('stdout'):
            print(f"  输出长度: {len(nmap_result['stdout'])} 字符")
            # 显示前200个字符
            stdout_preview = nmap_result['stdout'][:200]
            print(f"  输出预览: {stdout_preview}")
    except Exception as e:
        print(f"  Nmap执行错误: {e}")
    
    # 测试SQLMap工具
    print("\n2. 测试SQLMap工具...")
    sqlmap_args = {
        "url": test_url,
        "method": "GET",
        "level": 1,
        "risk": 1
    }
    
    try:
        sqlmap_result = await mcp_server.handle_call_tool("sqlmap_scan", sqlmap_args)
        print(f"  SQLMap执行结果: {sqlmap_result.get('success', False)}")
        if sqlmap_result.get('stdout'):
            print(f"  输出长度: {len(sqlmap_result['stdout'])} 字符")
            # 显示前200个字符
            stdout_preview = sqlmap_result['stdout'][:200]
            print(f"  输出预览: {stdout_preview}")
    except Exception as e:
        print(f"  SQLMap执行错误: {e}")
    
    print("\n✅ 直接工具测试完成")


if __name__ == "__main__":
    asyncio.run(test_tools_directly())