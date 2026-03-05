#!/usr/bin/env python3
"""
项目状态检查脚本
验证所有核心组件是否正常工作
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_file_structure():
    """检查项目文件结构"""
    print("📁 检查项目文件结构...")
    
    required_dirs = [
        "config",
        "src",
        "src/agents",
        "src/core", 
        "src/mcp_server",
        "src/mcp_server/tools",
        "src/utils",
        "src/web_ui",
        "docs",
        "logs",
        "reports",
        "scripts",
        "tests"
    ]
    
    required_files = [
        "config/development.yaml",
        ".env.example",
        "requirements.txt",
        "README.md",
        "solve_ctf.py",
        "src/__init__.py",
        "src/agents/react_agent.py",
        "src/core/attack_engine.py",
        "src/utils/config_manager.py",
        "src/utils/deepseek_client.py",
        "src/utils/logger.py",
        "src/utils/tool_coordinator.py",
        "src/utils/tool_parser.py",
        "src/mcp_server/server.py",
        "src/mcp_server/tools/sqlmap_wrapper.py",
        "src/mcp_server/tools/nmap_wrapper.py"
    ]
    
    all_good = True
    
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"  ✅ 目录存在: {dir_path}")
        else:
            print(f"  ❌ 目录缺失: {dir_path}")
            all_good = False
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✅ 文件存在: {file_path}")
        else:
            print(f"  ❌ 文件缺失: {file_path}")
            all_good = False
    
    return all_good

def check_config_files():
    """检查配置文件"""
    print("\n⚙️ 检查配置文件...")
    
    config_files = [
        "config/development.yaml",
        ".env"
    ]
    
    all_good = True
    
    for config_file in config_files:
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():
                        print(f"  ✅ 配置文件有效: {config_file}")
                    else:
                        print(f"  ⚠️ 配置文件为空: {config_file}")
            except Exception as e:
                print(f"  ❌ 配置文件读取错误 {config_file}: {e}")
                all_good = False
        else:
            if config_file == ".env":
                print(f"  ⚠️ 环境文件不存在: {config_file} (请复制 .env.example)")
            else:
                print(f"  ❌ 配置文件缺失: {config_file}")
                all_good = False
    
    return all_good

async def check_module_imports():
    """检查模块导入"""
    print("\n🔧 检查模块导入...")
    
    modules_to_check = [
        ("src.utils.logger", "setup_logger"),
        ("src.utils.config_manager", "ConfigManager"),
        ("src.utils.deepseek_client", "DeepSeekClient"),
        ("src.utils.tool_coordinator", "ToolChainCoordinator"),
        ("src.utils.tool_parser", "ToolParserFactory"),
        ("src.agents.react_agent", "ReActAgent"),
        ("src.core.attack_engine", "AttackExecutionEngine"),
        ("src.mcp_server.server", "CTFMCPServer"),
    ]
    
    all_good = True
    
    for module_path, class_name in modules_to_check:
        try:
            module = __import__(module_path, fromlist=[class_name])
            if hasattr(module, class_name):
                print(f"  ✅ 可导入: {module_path}.{class_name}")
            else:
                print(f"  ❌ 类/函数不存在: {module_path}.{class_name}")
                all_good = False
        except ImportError as e:
            print(f"  ❌ 导入失败 {module_path}: {e}")
            all_good = False
        except Exception as e:
            print(f"  ⚠️ 导入错误 {module_path}: {e}")
            all_good = False
    
    return all_good

async def check_core_functionality():
    """检查核心功能"""
    print("\n🚀 检查核心功能...")
    
    try:
        # 测试配置管理器
        from src.utils.config_manager import ConfigManager
        config = ConfigManager()
        # 验证配置是否已加载
        if config.get("project.name") is not None:
            print("  ✅ 配置管理器: 正常")
        else:
            print("  ❌ 配置管理器: 配置未正确加载")
            return False
    except Exception as e:
        print(f"  ❌ 配置管理器错误: {e}")
        return False
    
    try:
        # 测试日志系统
        from src.utils.logger import setup_logger
        logger = setup_logger("test_logger")
        logger.info("测试日志消息")
        print("  ✅ 日志系统: 正常")
    except Exception as e:
        print(f"  ❌ 日志系统错误: {e}")
        return False
    
    try:
        # 测试工具链协调器初始化
        from src.utils.tool_coordinator import ToolChainCoordinator
        coordinator = ToolChainCoordinator()
        await coordinator.initialize()
        print("  ✅ 工具链协调器: 正常")
    except Exception as e:
        print(f"  ❌ 工具链协调器错误: {e}")
        return False
    
    return True

def check_documentation():
    """检查文档"""
    print("\n📚 检查文档...")
    
    docs_files = [
        "docs/kali_deployment.md",
        "docs/kali_testing_guide.md",
        "docs/project_progress_summary.md",
        "docs/project_progress_report.md",
        "README.md"
    ]
    
    all_good = True
    
    for doc_file in docs_files:
        if os.path.exists(doc_file):
            try:
                with open(doc_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if len(content) > 100:  # 基本内容检查
                        print(f"  ✅ 文档完整: {doc_file}")
                    else:
                        print(f"  ⚠️ 文档过短: {doc_file}")
            except Exception as e:
                print(f"  ❌ 文档读取错误 {doc_file}: {e}")
                all_good = False
        else:
            print(f"  ⚠️ 文档缺失: {doc_file}")
            all_good = False
    
    return all_good

def check_recent_progress():
    """检查最近进展"""
    print("\n📈 检查最近进展...")
    
    # 检查solve_ctf.py脚本
    if os.path.exists("solve_ctf.py"):
        with open("solve_ctf.py", 'r', encoding='utf-8') as f:
            content = f.read()
            if "CTFSolver" in content and "solve_challenge" in content:
                print("  ✅ CTF解题脚本: 已实现")
            else:
                print("  ⚠️ CTF解题脚本: 不完整")
    else:
        print("  ❌ CTF解题脚本: 缺失")
    
    # 检查工具链协调器
    if os.path.exists("src/utils/tool_coordinator.py"):
        with open("src/utils/tool_coordinator.py", 'r', encoding='utf-8') as f:
            content = f.read()
            if "ToolChainCoordinator" in content and "execute_chain" in content:
                print("  ✅ 工具链协调器: 已实现")
            else:
                print("  ⚠️ 工具链协调器: 不完整")
    
    # 检查攻击执行引擎
    if os.path.exists("src/core/attack_engine.py"):
        with open("src/core/attack_engine.py", 'r', encoding='utf-8') as f:
            content = f.read()
            if "AttackExecutionEngine" in content and "execute_attack" in content:
                print("  ✅ 攻击执行引擎: 已实现")
            else:
                print("  ⚠️ 攻击执行引擎: 不完整")
    
    # 检查工具输出解析器
    if os.path.exists("src/utils/tool_parser.py"):
        with open("src/utils/tool_parser.py", 'r', encoding='utf-8') as f:
            content = f.read()
            if "ToolParserFactory" in content and "parse_tool_output" in content:
                print("  ✅ 工具输出解析器: 已实现")
            else:
                print("  ⚠️ 工具输出解析器: 不完整")
    
    return True

async def main():
    """主函数"""
    print("=" * 70)
    print("CTF AI攻击模拟系统 - 项目状态检查")
    print("=" * 70)
    
    results = []
    
    # 执行各项检查
    results.append(("文件结构", check_file_structure()))
    results.append(("配置文件", check_config_files()))
    results.append(("模块导入", await check_module_imports()))
    results.append(("核心功能", await check_core_functionality()))
    results.append(("文档", check_documentation()))
    results.append(("最近进展", check_recent_progress()))
    
    # 汇总结果
    print("\n" + "=" * 70)
    print("检查结果汇总")
    print("=" * 70)
    
    total_checks = len(results)
    passed_checks = sum(1 for _, passed in results if passed)
    
    for check_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{check_name}: {status}")
    
    print(f"\n总计: {passed_checks}/{total_checks} 项检查通过")
    
    if passed_checks == total_checks:
        print("\n🎉 所有检查通过！项目状态良好。")
        return 0
    else:
        print(f"\n⚠️  {total_checks - passed_checks} 项检查失败，需要修复。")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)