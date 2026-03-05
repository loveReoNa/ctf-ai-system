#!/usr/bin/env python3
"""
集成测试脚本
测试安全工具深度集成、工具链协调机制和攻击执行引擎
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.tool_parser import ToolParserFactory
from src.utils.tool_coordinator import ToolChainCoordinator
from src.core.attack_engine import AttackExecutionEngine
from src.utils.logger import setup_logger


class IntegrationTester:
    """集成测试器"""
    
    def __init__(self):
        self.logger = setup_logger("integration_tester")
        self.test_results = []
    
    async def test_tool_parser(self):
        """测试工具解析器"""
        self.logger.info("开始测试工具解析器...")
        
        parser_factory = ToolParserFactory()
        test_cases = [
            {
                "name": "SQLMap解析器",
                "tool": "sqlmap",
                "output": """
sqlmap identified the following injection point(s):
---
Parameter: id (GET)
    Type: boolean-based blind
    Title: MySQL >= 5.0 AND boolean-based blind - WHERE or HAVING clause
    Payload: id=1' AND 1234=1234 AND 'abcd'='abcd
---
back-end DBMS: MySQL >= 5.0
                """,
                "expected_fields": ["success", "vulnerabilities", "summary"]
            },
            {
                "name": "Nmap解析器",
                "tool": "nmap",
                "output": """
Nmap scan report for 127.0.0.1
Host is up (0.00010s latency).
Not shown: 998 closed ports
PORT     STATE SERVICE
80/tcp   open  http
443/tcp  open  https
3306/tcp open  mysql
                """,
                "expected_fields": ["success", "hosts", "summary"]
            },
            {
                "name": "Nikto解析器",
                "tool": "nikto",
                "output": """
+ Server: Apache/2.4.41 (Ubuntu)
+ /: The anti-clickjacking X-Frame-Options header is not present.
+ /config/: Directory indexing found.
+ /backup/: Directory indexing found.
                """,
                "expected_fields": ["success", "vulnerabilities", "summary"]
            }
        ]
        
        results = []
        for test_case in test_cases:
            try:
                result = parser_factory.parse_tool_output(
                    test_case["tool"], 
                    test_case["output"]
                )
                
                # 检查必需字段
                missing_fields = []
                for field in test_case["expected_fields"]:
                    if field not in result:
                        missing_fields.append(field)
                
                if missing_fields:
                    test_passed = False
                    message = f"缺少字段: {missing_fields}"
                else:
                    test_passed = True
                    message = f"解析成功，发现 {len(result.get('vulnerabilities', []))} 个漏洞"
                
                results.append({
                    "test": test_case["name"],
                    "passed": test_passed,
                    "message": message,
                    "result": result
                })
                
                self.logger.info(f"{test_case['name']}: {message}")
                
            except Exception as e:
                results.append({
                    "test": test_case["name"],
                    "passed": False,
                    "message": f"解析异常: {e}",
                    "error": str(e)
                })
                self.logger.error(f"{test_case['name']} 测试失败: {e}")
        
        self.test_results.append({
            "component": "工具解析器",
            "results": results,
            "passed": all(r["passed"] for r in results)
        })
        
        return results
    
    async def test_tool_coordinator(self):
        """测试工具链协调器"""
        self.logger.info("开始测试工具链协调器...")
        
        try:
            coordinator = ToolChainCoordinator()
            
            # 测试初始化
            init_success = await coordinator.initialize()
            
            if not init_success:
                self.logger.warning("工具链协调器初始化失败（可能缺少MCP服务器），继续测试...")
            
            # 测试工具链创建
            test_chains = ["web_recon", "quick_scan", "full_scan"]
            
            results = []
            for chain_name in test_chains:
                try:
                    # 创建工具链上下文（不实际执行）
                    context = await coordinator.execute_chain(
                        chain_name=chain_name,
                        target="test.example.com",
                        strategy="sequential"
                    )
                    
                    test_passed = True
                    message = f"工具链 '{chain_name}' 创建成功"
                    
                    results.append({
                        "test": f"工具链创建 - {chain_name}",
                        "passed": test_passed,
                        "message": message,
                        "context": {
                            "chain_id": context.chain_id,
                            "target": context.target,
                            "tools_executed": len(context.tools_executed)
                        }
                    })
                    
                    self.logger.info(f"工具链 '{chain_name}': {message}")
                    
                except Exception as e:
                    results.append({
                        "test": f"工具链创建 - {chain_name}",
                        "passed": False,
                        "message": f"创建失败: {e}",
                        "error": str(e)
                    })
                    self.logger.error(f"工具链 '{chain_name}' 测试失败: {e}")
            
            # 测试报告生成
            try:
                # 创建模拟上下文，包含一个工具执行结果
                mock_tool_result = type('MockToolResult', (), {
                    'tool_name': 'nmap_scan',
                    'success': True,
                    'execution_time': 1.5,
                    'dependencies': [],
                    'next_tools': ['sqlmap_scan'],
                    'output': {
                        'parsed': {
                            'success': True,
                            'message': '扫描完成',
                            'summary': {'open_ports': 3}
                        }
                    }
                })()
                
                mock_context = type('MockContext', (), {
                    'chain_id': 'test_chain_123',
                    'target': 'test.example.com',
                    'tools_executed': [mock_tool_result],
                    'flags_found': ['flag{test_flag}'],
                    'start_time': 0,
                    'end_time': 100,
                    'current_state': {'chain_summary': {'total_tools': 1, 'successful_tools': 1}}
                })()
                
                report = coordinator.generate_chain_report(mock_context)
                
                test_passed = "chain_id" in report and "target" in report and "success" in report
                message = "报告生成成功" if test_passed else "报告生成失败"
                
                results.append({
                    "test": "报告生成",
                    "passed": test_passed,
                    "message": message,
                    "report_keys": list(report.keys())
                })
                
                self.logger.info(f"报告生成: {message}")
                
            except Exception as e:
                results.append({
                    "test": "报告生成",
                    "passed": False,
                    "message": f"报告生成失败: {e}",
                    "error": str(e)
                })
                self.logger.error(f"报告生成测试失败: {e}")
            
            self.test_results.append({
                "component": "工具链协调器",
                "results": results,
                "passed": all(r["passed"] for r in results)
            })
            
            return results
            
        except Exception as e:
            self.logger.error(f"工具链协调器测试失败: {e}")
            
            self.test_results.append({
                "component": "工具链协调器",
                "results": [{
                    "test": "整体测试",
                    "passed": False,
                    "message": f"测试失败: {e}",
                    "error": str(e)
                }],
                "passed": False
            })
            
            return []
    
    async def test_attack_engine(self):
        """测试攻击执行引擎"""
        self.logger.info("开始测试攻击执行引擎...")
        
        try:
            engine = AttackExecutionEngine()
            
            # 测试初始化
            init_success = await engine.initialize()
            
            if not init_success:
                self.logger.warning("攻击执行引擎初始化失败（可能缺少AI客户端），继续测试...")
            
            results = []
            
            # 测试攻击计划创建
            try:
                plan = await engine.create_attack_plan(
                    target="testphp.vulnweb.com",
                    description="CTF测试攻击"
                )
                
                test_passed = hasattr(plan, 'plan_id') and hasattr(plan, 'steps')
                message = f"攻击计划创建成功，包含 {len(plan.steps)} 个步骤"
                
                results.append({
                    "test": "攻击计划创建",
                    "passed": test_passed,
                    "message": message,
                    "plan_id": plan.plan_id,
                    "steps_count": len(plan.steps)
                })
                
                self.logger.info(f"攻击计划创建: {message}")
                
                # 测试攻击状态获取
                try:
                    # 创建模拟攻击上下文
                    mock_context = type('MockContext', (), {
                        'attack_id': 'test_attack_123',
                        'target': 'test.example.com',
                        'plan': plan,
                        'start_time': 0,
                        'end_time': None,
                        'success': False,
                        'current_phase': 'reconnaissance',
                        'execution_history': []
                    })()
                    
                    engine.active_attacks['test_attack_123'] = mock_context
                    
                    status = engine.get_attack_status('test_attack_123')
                    
                    test_passed = status is not None and 'attack_id' in status
                    message = "攻击状态获取成功" if test_passed else "攻击状态获取失败"
                    
                    results.append({
                        "test": "攻击状态获取",
                        "passed": test_passed,
                        "message": message,
                        "status_keys": list(status.keys()) if status else []
                    })
                    
                    self.logger.info(f"攻击状态获取: {message}")
                    
                    # 清理
                    del engine.active_attacks['test_attack_123']
                    
                except Exception as e:
                    results.append({
                        "test": "攻击状态获取",
                        "passed": False,
                        "message": f"状态获取失败: {e}",
                        "error": str(e)
                    })
                    self.logger.error(f"攻击状态获取测试失败: {e}")
                
                # 测试引擎指标
                try:
                    metrics = engine.get_engine_metrics()
                    
                    test_passed = 'total_attacks' in metrics and 'active_attacks' in metrics
                    message = "引擎指标获取成功" if test_passed else "引擎指标获取失败"
                    
                    results.append({
                        "test": "引擎指标获取",
                        "passed": test_passed,
                        "message": message,
                        "metrics_keys": list(metrics.keys())
                    })
                    
                    self.logger.info(f"引擎指标获取: {message}")
                    
                except Exception as e:
                    results.append({
                        "test": "引擎指标获取",
                        "passed": False,
                        "message": f"指标获取失败: {e}",
                        "error": str(e)
                    })
                    self.logger.error(f"引擎指标获取测试失败: {e}")
                
            except Exception as e:
                results.append({
                    "test": "攻击计划创建",
                    "passed": False,
                    "message": f"计划创建失败: {e}",
                    "error": str(e)
                })
                self.logger.error(f"攻击计划创建测试失败: {e}")
            
            self.test_results.append({
                "component": "攻击执行引擎",
                "results": results,
                "passed": all(r["passed"] for r in results)
            })
            
            return results
            
        except Exception as e:
            self.logger.error(f"攻击执行引擎测试失败: {e}")
            
            self.test_results.append({
                "component": "攻击执行引擎",
                "results": [{
                    "test": "整体测试",
                    "passed": False,
                    "message": f"测试失败: {e}",
                    "error": str(e)
                }],
                "passed": False
            })
            
            return []
    
    async def test_integration(self):
        """运行所有集成测试"""
        self.logger.info("=" * 60)
        self.logger.info("开始集成测试")
        self.logger.info("=" * 60)
        
        # 运行所有测试
        await self.test_tool_parser()
        await self.test_tool_coordinator()
        await self.test_attack_engine()
        
        # 生成测试报告
        report = self.generate_test_report()
        
        self.logger.info("=" * 60)
        self.logger.info("集成测试完成")
        self.logger.info("=" * 60)
        
        return report
    
    def generate_test_report(self):
        """生成测试报告"""
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        
        report = {
            "timestamp": time.time(),
            "components": [],
            "summary": {}
        }
        
        for component_result in self.test_results:
            component_tests = len(component_result["results"])
            component_passed = sum(1 for r in component_result["results"] if r["passed"])
            component_failed = component_tests - component_passed
            
            total_tests += component_tests
            passed_tests += component_passed
            failed_tests += component_failed
            
            component_report = {
                "name": component_result["component"],
                "passed": component_result["passed"],
                "tests": component_tests,
                "passed_tests": component_passed,
                "failed_tests": component_failed,
                "success_rate": component_passed / component_tests if component_tests > 0 else 0,
                "test_details": component_result["results"]
            }
            
            report["components"].append(component_report)
        
        report["summary"] = {
            "total_components": len(self.test_results),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "overall_success_rate": passed_tests / total_tests if total_tests > 0 else 0,
            "all_passed": failed_tests == 0
        }
        
        # 保存报告到文件
        report_file = "logs/integration_test_report.json"
        os.makedirs("logs", exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"测试报告已保存: {report_file}")
        
        # 打印摘要
        self.print_test_summary(report)
        
        return report
    
    def print_test_summary(self, report):
        """打印测试摘要"""
        summary = report["summary"]
        
        print("\n" + "=" * 60)
        print("集成测试摘要")
        print("=" * 60)
        print(f"测试组件: {summary['total_components']}")
        print(f"总测试数: {summary['total_tests']}")
        print(f"通过测试: {summary['passed_tests']}")
        print(f"失败测试: {summary['failed_tests']}")
        print(f"成功率: {summary['overall_success_rate']:.2%}")
        print(f"整体状态: {'通过' if summary['all_passed'] else '失败'}")
        print("=" * 60)
        
        for component in report["components"]:
            status = "✓" if component["passed"] else "✗"
            print(f"{status} {component['name']}: "
                  f"{component['passed_tests']}/{component['tests']} 通过 "
                  f"({component['success_rate']:.2%})")
        
        print("=" * 60)
        
        if not summary["all_passed"]:
            print("\n失败测试详情:")
            for component in report["components"]:
                for test in component["test_details"]:
                    if not test["passed"]:
                        print(f"  - {component['name']}: {test['test']}")
                        print(f"    原因: {test['message']}")
        
        print()


# 导入time模块
import time

async def main():
    """主函数"""
    tester = IntegrationTester()
    report = await tester.test_integration()
    
    # 返回测试结果
    return report["summary"]["all_passed"]


if __name__ == "__main__":
    # 运行集成测试
    success = asyncio.run(main())
    
    # 根据测试结果退出
    sys.exit(0 if success else 1)