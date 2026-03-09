#!/usr/bin/env python3
"""
CTF Agent系统集成测试
测试整个系统的各个组件是否正常工作
"""

import asyncio
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

def print_header(title):
    """打印测试标题"""
    print("\n" + "="*60)
    print(f"测试: {title}")
    print("="*60)

def print_result(success, message):
    """打印测试结果"""
    if success:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")

async def test_config_loading():
    """测试配置加载"""
    print_header("配置加载测试")
    
    try:
        from src.utils.config_manager import config
        
        # 检查配置是否加载成功
        if config:
            print_result(True, f"配置加载成功，版本: {config.get('version', '未知')}")
            
            # 打印关键配置
            print("\n关键配置:")
            print(f"  AI提供商: {config.get('ai', {}).get('provider', '未设置')}")
            print(f"  API主机: {config.get('api', {}).get('server', {}).get('host', '未设置')}")
            print(f"  API端口: {config.get('api', {}).get('server', {}).get('port', '未设置')}")
            
            return True
        else:
            print_result(False, "配置为空")
            return False
            
    except Exception as e:
        print_result(False, f"配置加载失败: {e}")
        return False

async def test_logger():
    """测试日志系统"""
    print_header("日志系统测试")
    
    try:
        from src.utils.logger import setup_logger
        
        # 创建测试日志器
        logger = setup_logger("test_logger", log_level="INFO")
        
        # 测试日志记录
        logger.debug("调试消息（应该不可见）")
        logger.info("信息消息")
        logger.warning("警告消息")
        logger.error("错误消息")
        
        print_result(True, "日志系统工作正常")
        
        # 检查日志文件
        log_file = Path("logs") / "ctf_ai.log"
        if log_file.exists():
            print(f"  日志文件: {log_file} (存在)")
        else:
            print(f"  日志文件: {log_file} (不存在)")
        
        return True
        
    except Exception as e:
        print_result(False, f"日志系统测试失败: {e}")
        return False

async def test_mcp_tools():
    """测试MCP工具"""
    print_header("MCP工具测试")
    
    try:
        from src.mcp_server.tools.sqlmap_wrapper import SQLMapWrapper
        
        # 创建SQLMap包装器
        wrapper = SQLMapWrapper()
        
        # 测试连接
        print("测试SQLMap连接...")
        connected = await wrapper.test_connection()
        
        if connected:
            print_result(True, "SQLMap连接成功")
            
            # 测试简单扫描（使用测试目标）
            print("\n测试SQLMap扫描...")
            test_url = "http://testphp.vulnweb.com/artists.php?artist=1"
            
            result = await wrapper.scan(
                test_url,
                level=1,
                risk=1,
                timeout=30
            )
            
            if result.get("success"):
                vuln_count = len(result.get("vulnerabilities", []))
                print_result(True, f"扫描成功，发现 {vuln_count} 个漏洞")
                return True
            else:
                print_result(False, "扫描失败或未发现漏洞")
                return False
        else:
            print_result(False, "SQLMap连接失败")
            return False
            
    except Exception as e:
        print_result(False, f"MCP工具测试失败: {e}")
        return False

async def test_react_agent():
    """测试ReAct Agent"""
    print_header("ReAct Agent测试")
    
    try:
        from src.agents.react_agent import ReActAgent, CTFChallenge
        from src.utils.config_manager import config
        
        # 创建Agent配置
        agent_config = {
            "ai": config.get("ai", {}),
            "mcp": config.get("mcp", {})
        }
        
        # 创建Agent
        agent = ReActAgent(agent_config)
        
        # 初始化Agent
        print("初始化Agent...")
        initialized = await agent.initialize()
        
        if not initialized:
            print_result(False, "Agent初始化失败")
            return False
        
        print_result(True, "Agent初始化成功")
        
        # 创建测试挑战
        challenge = CTFChallenge(
            id="test-001",
            title="测试SQL注入挑战",
            description="一个用于测试的SQL注入挑战",
            target_url="http://testphp.vulnweb.com/artists.php?artist=1",
            category="web",
            difficulty="easy",
            hints=["尝试SQL注入"],
            expected_flag=None
        )
        
        # 设置挑战
        agent.set_challenge(challenge)
        print_result(True, "挑战设置成功")
        
        # 测试分析功能
        print("\n测试挑战分析...")
        analysis_result = await agent.analyze_challenge()
        
        if "error" not in analysis_result:
            print_result(True, f"挑战分析成功，置信度: {analysis_result.get('confidence', 0):.2f}")
            
            vulnerabilities = analysis_result.get("vulnerabilities", [])
            if vulnerabilities:
                print(f"  识别到漏洞: {', '.join(vulnerabilities)}")
            
            return True
        else:
            print_result(False, f"挑战分析失败: {analysis_result.get('error')}")
            return False
            
    except Exception as e:
        print_result(False, f"ReAct Agent测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_api_server():
    """测试API服务器"""
    print_header("API服务器测试")
    
    try:
        import requests
        
        # 尝试连接API服务器
        base_url = "http://localhost:8000"
        
        print(f"尝试连接API服务器: {base_url}")
        
        try:
            response = requests.get(f"{base_url}/", timeout=5)
            
            if response.status_code == 200:
                print_result(True, "API服务器响应正常")
                
                # 测试状态端点
                status_response = requests.get(f"{base_url}/status", timeout=5)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"  Agent状态: {status_data.get('state')}")
                    print(f"  可用工具: {len(status_data.get('tools_available', []))} 个")
                    return True
                else:
                    print_result(False, "状态端点不可用")
                    return False
            else:
                print_result(False, f"API服务器返回错误状态码: {response.status_code}")
                return False
                
        except requests.ConnectionError:
            print_result(False, "无法连接到API服务器（可能未启动）")
            print("  提示: 请先运行 'python start_ctf_agent.py' 启动服务器")
            return False
            
    except Exception as e:
        print_result(False, f"API服务器测试失败: {e}")
        return False

async def run_all_tests():
    """运行所有测试"""
    print("="*60)
    print("CTF Agent系统集成测试")
    print("="*60)
    
    test_results = []
    
    # 运行各个测试
    tests = [
        ("配置加载", test_config_loading),
        ("日志系统", test_logger),
        ("MCP工具", test_mcp_tools),
        ("ReAct Agent", test_react_agent),
        ("API服务器", test_api_server),
    ]
    
    for test_name, test_func in tests:
        try:
            success = await test_func()
            test_results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            test_results.append((test_name, False))
    
    # 打印测试摘要
    print_header("测试摘要")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for _, success in test_results if success)
    
    print(f"总测试数: {total_tests}")
    print(f"通过测试: {passed_tests}")
    print(f"失败测试: {total_tests - passed_tests}")
    
    print("\n详细结果:")
    for test_name, success in test_results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    # 总体评估
    if passed_tests == total_tests:
        print("\n🎉 所有测试通过！系统工作正常。")
        return True
    elif passed_tests >= total_tests * 0.7:
        print(f"\n⚠️  部分测试通过 ({passed_tests}/{total_tests})，系统基本可用。")
        return True
    else:
        print(f"\n❌ 测试失败较多 ({passed_tests}/{total_tests})，系统可能有问题。")
        return False

def main():
    """主函数"""
    try:
        # 运行所有测试
        success = asyncio.run(run_all_tests())
        
        # 提供下一步建议
        print("\n" + "="*60)
        print("下一步建议:")
        
        if success:
            print("1. 启动系统: python start_ctf_agent.py")
            print("2. 测试API客户端: python api_client_example.py --demo quick")
            print("3. 查看API文档: http://localhost:8000/docs")
        else:
            print("1. 检查依赖: pip install -r requirements.txt")
            print("2. 检查配置: 确保 .env 文件正确配置")
            print("3. 检查工具: 确保 sqlmap, nmap 等工具已安装")
            print("4. 查看日志: logs/ 目录下的日志文件")
        
        print("="*60)
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        return 130
    except Exception as e:
        print(f"\n❌ 测试运行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())