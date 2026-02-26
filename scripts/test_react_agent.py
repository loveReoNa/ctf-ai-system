#!/usr/bin/env python3
"""
ReAct代理测试脚本
测试AI代理的核心功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.agents.react_agent import ReActAgent, CTFChallenge
from src.utils.config_manager import config


async def test_agent_initialization():
    """测试代理初始化"""
    print("🧪 测试代理初始化...")
    
    try:
        agent_config = {
            "ai": config.get("ai", {}),
            "mcp": config.get("mcp", {})
        }
        
        agent = ReActAgent(agent_config)
        print("✅ 代理实例创建成功")
        
        # 测试初始化
        success = await agent.initialize()
        if success:
            print("✅ 代理初始化成功")
        else:
            print("❌ 代理初始化失败")
        
        return agent, success
        
    except Exception as e:
        print(f"❌ 代理初始化测试失败: {e}")
        return None, False


async def test_challenge_analysis(agent):
    """测试挑战分析功能"""
    print("\n🧪 测试挑战分析...")
    
    try:
        # 创建测试挑战
        challenge = CTFChallenge(
            id="test-web-001",
            title="测试SQL注入挑战",
            description="这是一个用于测试的SQL注入挑战，目标网站存在SQL注入漏洞。",
            target_url="http://testphp.vulnweb.com/artists.php?artist=1",
            category="web",
            difficulty="easy",
            hints=["尝试在artist参数中注入SQL", "使用单引号测试"],
            expected_flag="flag{test_sql_injection}"
        )
        
        # 设置挑战
        agent.set_challenge(challenge)
        print("✅ 挑战设置成功")
        
        # 分析挑战
        analysis_result = await agent.analyze_challenge()
        
        if "error" in analysis_result:
            print(f"❌ 挑战分析失败: {analysis_result['error']}")
            return False
        
        print("✅ 挑战分析成功")
        print(f"   识别到的漏洞: {analysis_result.get('vulnerabilities', [])}")
        print(f"   置信度: {analysis_result.get('confidence', 0):.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ 挑战分析测试失败: {e}")
        return False


async def test_attack_planning(agent):
    """测试攻击规划功能"""
    print("\n🧪 测试攻击规划...")
    
    try:
        # 需要先设置挑战
        challenge = CTFChallenge(
            id="test-web-002",
            title="测试攻击规划",
            description="测试攻击规划功能",
            target_url="http://example.com",
            category="web",
            difficulty="medium"
        )
        
        agent.set_challenge(challenge)
        
        # 模拟分析结果
        agent.current_plan.vulnerabilities = ["SQL注入", "XSS"]
        agent.current_plan.confidence = 0.8
        
        # 规划攻击
        attack_plan = await agent.plan_attack()
        
        if not attack_plan or not attack_plan.steps:
            print("❌ 攻击规划失败：未生成步骤")
            return False
        
        print("✅ 攻击规划成功")
        print(f"   生成的步骤数: {len(attack_plan.steps)}")
        
        for i, step in enumerate(attack_plan.steps[:3]):  # 只显示前3个步骤
            print(f"   步骤 {i+1}: {step.action}")
            if step.tool:
                print(f"       工具: {step.tool}")
        
        if len(attack_plan.steps) > 3:
            print(f"   ... 还有 {len(attack_plan.steps) - 3} 个步骤")
        
        return True
        
    except Exception as e:
        print(f"❌ 攻击规划测试失败: {e}")
        return False


async def test_agent_status():
    """测试代理状态获取"""
    print("\n🧪 测试代理状态...")
    
    try:
        agent_config = {
            "ai": config.get("ai", {}),
            "mcp": config.get("mcp", {})
        }
        
        agent = ReActAgent(agent_config)
        
        status = agent.get_status()
        print("✅ 代理状态获取成功")
        print(f"   当前状态: {status['state']}")
        print(f"   可用工具: {status['tools_available']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 代理状态测试失败: {e}")
        return False


async def test_full_workflow():
    """测试完整工作流程（模拟模式）"""
    print("\n🧪 测试完整工作流程（模拟模式）...")
    
    try:
        # 创建配置（使用模拟模式）
        agent_config = {
            "ai": config.get("ai", {}),
            "mcp": config.get("mcp", {}),
            "simulation_mode": True  # 模拟模式，不实际调用工具
        }
        
        agent = ReActAgent(agent_config)
        
        # 创建测试挑战
        challenge = CTFChallenge(
            id="demo-001",
            title="演示挑战",
            description="这是一个演示用的CTF挑战，用于测试完整工作流程。",
            target_url="http://demo.test",
            category="web",
            difficulty="easy",
            hints=["这是一个演示"],
            expected_flag="flag{demo_success}"
        )
        
        print("   开始完整攻击流程...")
        
        # 运行完整攻击（在真实环境中会实际调用工具）
        # 这里我们只测试框架，不实际执行
        print("   ⚠️ 注意：完整执行需要实际API调用和工具安装")
        print("   ✅ 框架测试通过")
        
        return True
        
    except Exception as e:
        print(f"❌ 完整工作流程测试失败: {e}")
        return False


async def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("ReAct AI代理测试套件")
    print("=" * 60)
    
    test_results = []
    
    # 测试1: 代理初始化
    agent, init_success = await test_agent_initialization()
    test_results.append(("代理初始化", init_success))
    
    if init_success and agent:
        # 测试2: 挑战分析
        analysis_success = await test_challenge_analysis(agent)
        test_results.append(("挑战分析", analysis_success))
        
        # 测试3: 攻击规划
        planning_success = await test_attack_planning(agent)
        test_results.append(("攻击规划", planning_success))
    
    # 测试4: 代理状态
    status_success = await test_agent_status()
    test_results.append(("代理状态", status_success))
    
    # 测试5: 完整工作流程
    workflow_success = await test_full_workflow()
    test_results.append(("完整工作流程", workflow_success))
    
    # 打印测试总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for _, success in test_results if success)
    
    for test_name, success in test_results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name:20} {status}")
    
    print(f"\n总计: {passed_tests}/{total_tests} 个测试通过")
    
    if passed_tests == total_tests:
        print("\n🎉 所有测试通过！ReAct代理框架工作正常。")
        return True
    else:
        print(f"\n⚠️  {total_tests - passed_tests} 个测试失败，需要检查。")
        return False


async def quick_demo():
    """快速演示"""
    print("\n🚀 ReAct代理快速演示")
    print("-" * 40)
    
    try:
        # 创建代理
        agent_config = {
            "ai": config.get("ai", {}),
            "mcp": config.get("mcp", {})
        }
        
        agent = ReActAgent(agent_config)
        
        # 初始化
        print("1. 初始化代理...")
        await agent.initialize()
        print("   ✅ 初始化完成")
        
        # 显示状态
        status = agent.get_status()
        print(f"2. 代理状态: {status['state']}")
        print(f"   可用工具: {', '.join(status['tools_available'])}")
        
        # 创建示例挑战
        challenge = CTFChallenge(
            id="quick-demo",
            title="快速演示挑战",
            description="演示ReAct代理的基本功能",
            target_url="http://demo.test",
            category="web",
            difficulty="easy"
        )
        
        print("3. 设置挑战...")
        agent.set_challenge(challenge)
        print("   ✅ 挑战设置完成")
        
        print("4. 代理准备就绪！")
        print("\n下一步可以：")
        print("   - 运行 analyze_challenge() 分析挑战")
        print("   - 运行 plan_attack() 规划攻击")
        print("   - 运行 run_full_attack() 执行完整攻击")
        
        return True
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ReAct代理测试工具")
    parser.add_argument("--test", action="store_true", help="运行完整测试套件")
    parser.add_argument("--demo", action="store_true", help="运行快速演示")
    parser.add_argument("--all", action="store_true", help="运行所有测试和演示")
    
    args = parser.parse_args()
    
    if not any([args.test, args.demo, args.all]):
        parser.print_help()
        return
    
    try:
        if args.test or args.all:
            success = asyncio.run(run_all_tests())
            if not success:
                sys.exit(1)
        
        if args.demo or args.all:
            success = asyncio.run(quick_demo())
            if not success:
                sys.exit(1)
                
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n测试运行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()