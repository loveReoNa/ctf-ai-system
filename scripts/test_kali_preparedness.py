#!/usr/bin/env python3
"""
Kali环境准备测试脚本
验证系统是否已准备好进行Kali Linux部署和测试
"""
import os
import sys
import platform
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config_manager import config
from src.mcp_server.server import get_tool_path, CTFMCPServer


def test_platform_detection():
    """测试平台检测和路径选择"""
    print("=" * 60)
    print("平台检测测试")
    print("=" * 60)
    
    current_system = platform.system()
    print(f"当前操作系统: {current_system}")
    
    # 测试工具路径获取
    sqlmap_path = get_tool_path("sqlmap")
    nmap_path = get_tool_path("nmap")
    
    print(f"SQLMap路径: {sqlmap_path}")
    print(f"Nmap路径: {nmap_path}")
    
    # 验证路径配置
    if current_system == "Windows":
        expected_sqlmap = config.get("tools.sqlmap.windows_path", "sqlmap")
        expected_nmap = config.get("tools.nmap.windows_path", "nmap")
    else:
        expected_sqlmap = config.get("tools.sqlmap.path", "sqlmap")
        expected_nmap = config.get("tools.nmap.path", "nmap")
    
    print(f"预期SQLMap路径: {expected_sqlmap}")
    print(f"预期Nmap路径: {expected_nmap}")
    
    success = True
    if sqlmap_path != expected_sqlmap:
        print(f"❌ SQLMap路径不匹配: 获取={sqlmap_path}, 预期={expected_sqlmap}")
        success = False
    else:
        print("✅ SQLMap路径正确")
    
    if nmap_path != expected_nmap:
        print(f"❌ Nmap路径不匹配: 获取={nmap_path}, 预期={expected_nmap}")
        success = False
    else:
        print("✅ Nmap路径正确")
    
    return success


async def test_mcp_server_initialization():
    """测试MCP服务器初始化"""
    print("\n" + "=" * 60)
    print("MCP服务器初始化测试")
    print("=" * 60)
    
    try:
        server = CTFMCPServer()
        await server.initialize()
        
        # 列出工具
        tools = await server.handle_list_tools()
        print(f"可用工具: {[tool['name'] for tool in tools]}")
        
        if len(tools) >= 2:
            print("✅ MCP服务器初始化成功")
            print("✅ 工具注册成功")
            return True
        else:
            print(f"❌ 工具数量不足: {len(tools)}")
            return False
            
    except Exception as e:
        print(f"❌ MCP服务器初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_configuration():
    """测试配置文件"""
    print("\n" + "=" * 60)
    print("配置文件测试")
    print("=" * 60)
    
    required_configs = [
        ("ai.provider", "deepseek"),
        ("ai.model", "deepseek-chat"),
        ("tools.sqlmap.path", "/usr/bin/sqlmap"),
        ("tools.nmap.path", "/usr/bin/nmap"),
    ]
    
    all_passed = True
    for key, expected_value in required_configs:
        value = config.get(key)
        if value == expected_value:
            print(f"✅ {key}: {value}")
        else:
            print(f"❌ {key}: 获取={value}, 预期={expected_value}")
            all_passed = False
    
    return all_passed


def test_kali_specific_checks():
    """测试Kali特定检查"""
    print("\n" + "=" * 60)
    print("Kali环境特定检查")
    print("=" * 60)
    
    current_system = platform.system()
    is_kali = current_system == "Linux" or "kali" in platform.platform().lower()
    
    print(f"当前系统: {platform.platform()}")
    print(f"是否为Kali/Linux: {is_kali}")
    
    if is_kali:
        print("✅ 检测到Kali/Linux环境")
        
        # 检查Kali路径配置
        sqlmap_kali_path = config.get("tools.sqlmap.path")
        nmap_kali_path = config.get("tools.nmap.path")
        
        print(f"Kali SQLMap路径: {sqlmap_kali_path}")
        print(f"Kali Nmap路径: {nmap_kali_path}")
        
        if sqlmap_kali_path == "/usr/bin/sqlmap":
            print("✅ SQLMap路径配置正确（Kali默认路径）")
        else:
            print(f"⚠️ SQLMap路径可能不是Kali默认: {sqlmap_kali_path}")
            
        if nmap_kali_path == "/usr/bin/nmap":
            print("✅ Nmap路径配置正确（Kali默认路径）")
        else:
            print(f"⚠️ Nmap路径可能不是Kali默认: {nmap_kali_path}")
            
        return True
    else:
        print(f"⚠️ 当前不是Kali环境，但系统已配置为支持Kali部署")
        print(f"⚠️ 在Kali上运行时，工具将使用路径: /usr/bin/sqlmap, /usr/bin/nmap")
        return True


async def main():
    """主测试函数"""
    print("CTF AI攻击模拟系统 - Kali环境准备测试")
    print("=" * 60)
    
    tests = [
        ("平台检测", test_platform_detection),
        ("配置文件", test_configuration),
        ("Kali特定检查", test_kali_specific_checks),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ 测试 '{test_name}' 失败: {e}")
            results.append((test_name, False))
    
    # 单独处理异步测试
    try:
        mcp_result = await test_mcp_server_initialization()
        results.append(("MCP服务器初始化", mcp_result))
    except Exception as e:
        print(f"❌ 测试 'MCP服务器初始化' 失败: {e}")
        results.append(("MCP服务器初始化", False))
    
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\n通过测试: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 所有测试通过！系统已准备好进行Kali部署。")
        print("\n下一步建议:")
        print("1. 将项目传输到Kali Linux")
        print("2. 运行环境验证: python3 scripts/verify_kali_environment.py")
        print("3. 安装Python依赖: pip3 install -r requirements.txt")
        print("4. 配置环境变量: cp .env.example .env")
        print("5. 运行完整测试: python3 scripts/test_react_agent.py")
        print("6. 启动MCP服务器: python3 scripts/start_mcp_server.py")
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查上述问题。")
    
    return passed == total


if __name__ == "__main__":
    # 设置日志级别避免干扰
    import logging
    logging.getLogger().setLevel(logging.ERROR)
    
    # 运行测试
    success = asyncio.run(main())
    sys.exit(0 if success else 1)