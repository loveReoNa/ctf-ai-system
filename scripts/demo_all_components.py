#!/usr/bin/env python3
"""
演示脚本 - 展示安全工具深度集成、工具链协调和攻击执行引擎
"""

import asyncio
import json
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.tool_parser import ToolParserFactory
from src.utils.tool_coordinator import ToolChainCoordinator, demo_tool_chain
from src.core.attack_engine import AttackExecutionEngine, demo_attack_engine
from src.utils.logger import setup_logger


class ComponentDemo:
    """组件演示器"""
    
    def __init__(self):
        self.logger = setup_logger("component_demo")
        self.demo_results = {}
    
    def print_header(self, title):
        """打印标题"""
        print("\n" + "=" * 70)
        print(f" {title}")
        print("=" * 70)
    
    def print_section(self, title):
        """打印章节"""
        print(f"\n{'-' * 40}")
        print(f" {title}")
        print(f"{'-' * 40}")
    
    async def demo_tool_parsers(self):
        """演示工具解析器"""
        self.print_header("演示 1: 安全工具输出解析器")
        
        parser_factory = ToolParserFactory()
        
        # 演示SQLMap解析
        self.print_section("SQLMap输出解析")
        
        sqlmap_output = """
sqlmap identified the following injection point(s):
---
Parameter: id (GET)
    Type: boolean-based blind
    Title: MySQL >= 5.0 AND boolean-based blind - WHERE or HAVING clause
    Payload: id=1' AND 1234=1234 AND 'abcd'='abcd
    Risk: HIGH
---
back-end DBMS: MySQL >= 5.0
technique: boolean-based blind
        """
        
        result = parser_factory.parse_tool_output("sqlmap", sqlmap_output)
        
        print("原始SQLMap输出:")
        print(sqlmap_output[:200] + "...")
        
        print("\n解析结果:")
        print(f"  成功: {result.get('success', False)}")
        print(f"  漏洞数量: {len(result.get('vulnerabilities', []))}")
        
        if result.get('vulnerabilities'):
            for i, vuln in enumerate(result['vulnerabilities'], 1):
                print(f"  漏洞 {i}: {vuln.get('type')} - {vuln.get('severity')}")
                print(f"    位置: {vuln.get('location')}")
                print(f"    描述: {vuln.get('description')}")
        
        summary = result.get('summary', {})
        print(f"  数据库: {summary.get('dbms_detected', '未知')}")
        print(f"  风险等级: {summary.get('risk_level', '未知')}")
        
        # 演示Nmap解析
        self.print_section("Nmap输出解析")
        
        nmap_output = """
Nmap scan report for 192.168.1.100
Host is up (0.0023s latency).
Not shown: 997 closed ports
PORT     STATE SERVICE    VERSION
80/tcp   open  http       Apache httpd 2.4.41
443/tcp  open  ssl/https  Apache httpd 2.4.41
3306/tcp open  mysql      MySQL 5.7.33
        """
        
        result = parser_factory.parse_tool_output("nmap", nmap_output)
        
        print("原始Nmap输出:")
        print(nmap_output[:200] + "...")
        
        print("\n解析结果:")
        print(f"  成功: {result.get('success', False)}")
        print(f"  主机数量: {len(result.get('hosts', []))}")
        
        if result.get('hosts'):
            for host in result['hosts']:
                print(f"  主机: {host.get('ip')}")
                print(f"    开放端口: {host.get('open_ports_count')}")
                
                for port in host.get('ports', []):
                    if port.get('state') == 'open':
                        print(f"    端口 {port.get('port')}/{port.get('protocol')}: "
                              f"{port.get('service')} {port.get('version', '')}")
        
        summary = result.get('summary', {})
        print(f"  总开放端口: {summary.get('open_ports', 0)}")
        print(f"  发现服务: {', '.join(summary.get('services_found', []))}")
        
        self.demo_results['tool_parsers'] = {
            'sqlmap': parser_factory.parse_tool_output("sqlmap", sqlmap_output),
            'nmap': parser_factory.parse_tool_output("nmap", nmap_output)
        }
        
        return True
    
    async def demo_tool_coordination(self):
        """演示工具链协调"""
        self.print_header("演示 2: 工具链协调机制")
        
        print("工具链协调器功能:")
        print("  1. 多工具依赖管理")
        print("  2. 并行/顺序执行策略")
        print("  3. 结果整合与分析")
        print("  4. 智能工具链推荐")
        
        self.print_section("预定义工具链")
        
        coordinator = ToolChainCoordinator()
        
        # 显示预定义工具链
        print("可用工具链:")
        for chain_name, tools in coordinator.predefined_chains.items():
            print(f"  {chain_name}: {', '.join(tools)}")
        
        self.print_section("工具依赖关系")
        
        print("工具依赖图:")
        for source, deps in coordinator.tool_dependencies.items():
            for dep in deps:
                print(f"  {source} -> {dep.target_tool} ({dep.dependency_type.value})")
        
        self.print_section("模拟工具链执行")
        
        # 创建模拟工具链上下文
        mock_context = type('MockContext', (), {
            'chain_id': 'demo_chain_123',
            'target': 'demo.example.com',
            'tools_executed': [
                type('MockResult', (), {
                    'tool_name': 'nmap_scan',
                    'success': True,
                    'output': {
                        'parsed': {
                            'success': True,
                            'hosts': [{
                                'ip': 'demo.example.com',
                                'ports': [
                                    {'port': 80, 'state': 'open', 'service': 'http'},
                                    {'port': 443, 'state': 'open', 'service': 'https'}
                                ]
                            }]
                        }
                    },
                    'execution_time': 5.2,
                    'dependencies': [],
                    'next_tools': ['sqlmap_scan', 'dirb_scan']
                })(),
                type('MockResult', (), {
                    'tool_name': 'sqlmap_scan',
                    'success': True,
                    'output': {
                        'parsed': {
                            'success': True,
                            'vulnerabilities': [{
                                'type': 'SQL Injection',
                                'severity': 'high',
                                'description': 'Boolean-based blind SQL injection'
                            }]
                        }
                    },
                    'execution_time': 12.8,
                    'dependencies': ['nmap_scan'],
                    'next_tools': ['sqlmap_data_dump']
                })()
            ],
            'flags_found': ['flag{demo_flag_123}'],
            'start_time': time.time() - 30,
            'end_time': time.time(),
            'current_state': {}
        })()
        
        # 生成报告
        report = coordinator.generate_chain_report(mock_context)
        
        print("工具链执行报告:")
        print(f"  工具链ID: {report.get('chain_id')}")
        print(f"  目标: {report.get('target')}")
        print(f"  执行工具: {report.get('execution_summary', {}).get('tools_executed', 0)}")
        print(f"  成功工具: {report.get('execution_summary', {}).get('tools_successful', 0)}")
        print(f"  找到Flag: {len(report.get('flags_found', []))}")
        
        security_assessment = report.get('security_assessment', {})
        print(f"  安全风险等级: {security_assessment.get('risk_level', 'unknown')}")
        print(f"  发现漏洞: {len(security_assessment.get('vulnerabilities', []))}")
        
        self.demo_results['tool_coordination'] = report
        
        return True
    
    async def demo_attack_engine(self):
        """演示攻击执行引擎"""
        self.print_header("演示 3: 攻击执行引擎")
        
        print("攻击执行引擎功能:")
        print("  1. AI驱动的攻击计划生成")
        print("  2. 多阶段攻击执行")
        print("  3. 实时状态监控")
        print("  4. 自动化报告生成")
        
        self.print_section("攻击阶段")
        
        from src.core.attack_engine import AttackPhase, AttackStatus
        
        print("攻击阶段:")
        for phase in AttackPhase:
            print(f"  {phase.value}: {phase.name.replace('_', ' ').title()}")
        
        print("\n攻击状态:")
        for status in AttackStatus:
            print(f"  {status.value}: {status.name.title()}")
        
        self.print_section("模拟攻击执行")
        
        # 创建模拟攻击计划
        mock_plan = type('MockPlan', (), {
            'plan_id': 'demo_plan_456',
            'target': 'ctf.example.com',
            'description': 'CTF挑战攻击演示',
            'steps': [
                type('MockStep', (), {
                    'step_id': 'step_1',
                    'phase': AttackPhase.RECONNAISSANCE,
                    'description': 'Nmap端口扫描',
                    'tool_name': 'nmap_scan',
                    'status': AttackStatus.COMPLETED,
                    'result': {'success': True, 'message': '发现开放端口 80, 443'}
                })(),
                type('MockStep', (), {
                    'step_id': 'step_2',
                    'phase': AttackPhase.VULNERABILITY_ANALYSIS,
                    'description': 'Nikto漏洞扫描',
                    'tool_name': 'nikto_scan',
                    'status': AttackStatus.COMPLETED,
                    'result': {'success': True, 'message': '发现3个安全问题'}
                })(),
                type('MockStep', (), {
                    'step_id': 'step_3',
                    'phase': AttackPhase.EXPLOITATION,
                    'description': 'SQLMap注入检测',
                    'tool_name': 'sqlmap_scan',
                    'status': AttackStatus.RUNNING,
                    'result': None
                })()
            ],
            'status': AttackStatus.RUNNING,
            'current_step_index': 2,
            'flags_found': ['flag{ctf_demo_2024}'],
            'vulnerabilities_found': [
                {'type': 'SQL Injection', 'severity': 'high', 'description': 'Boolean-based blind'},
                {'type': 'XSS', 'severity': 'medium', 'description': 'Reflected XSS in search parameter'}
            ]
        })()
        
        # 创建模拟攻击上下文
        mock_context = type('MockContext', (), {
            'attack_id': 'demo_attack_789',
            'target': 'ctf.example.com',
            'plan': mock_plan,
            'current_phase': AttackPhase.EXPLOITATION,
            'start_time': time.time() - 120,
            'end_time': None,
            'success': False,
            'execution_history': [
                {
                    'step_id': 'step_1',
                    'description': 'Nmap端口扫描',
                    'status': 'completed',
                    'execution_time': 8.5,
                    'result': {'success': True}
                },
                {
                    'step_id': 'step_2',
                    'description': 'Nikto漏洞扫描',
                    'status': 'completed',
                    'execution_time': 15.2,
                    'result': {'success': True}
                }
            ]
        })()
        
        print("攻击计划:")
        print(f"  计划ID: {mock_plan.plan_id}")
        print(f"  目标: {mock_plan.target}")
        print(f"  描述: {mock_plan.description}")
        print(f"  步骤数: {len(mock_plan.steps)}")
        print(f"  当前步骤: {mock_plan.current_step_index + 1}/{len(mock_plan.steps)}")
        print(f"  状态: {mock_plan.status.value}")
        
        print("\n攻击步骤:")
        for i, step in enumerate(mock_plan.steps, 1):
            status_icon = '✓' if step.status == AttackStatus.COMPLETED else '▶' if step.status == AttackStatus.RUNNING else '○'
            print(f"  {status_icon} 步骤{i}: {step.description}")
            if step.result:
                print(f"      结果: {step.result.get('message', '')}")
        
        print(f"\n攻击成果:")
        print(f"  找到Flag: {len(mock_plan.flags_found)} 个")
        for flag in mock_plan.flags_found:
            print(f"    - {flag}")
        
        print(f"  发现漏洞: {len(mock_plan.vulnerabilities_found)} 个")
        for vuln in mock_plan.vulnerabilities_found:
            print(f"    - {vuln['type']} ({vuln['severity']}): {vuln['description']}")
        
        self.print_section("攻击引擎指标")
        
        # 模拟引擎指标
        mock_metrics = {
            'total_attacks': 5,
            'successful_attacks': 3,
            'failed_attacks': 2,
            'average_execution_time': 186.5,
            'flags_found_total': 8,
            'active_attacks': 1,
            'total_history': 4
        }
        
        print("引擎性能指标:")
        for key, value in mock_metrics.items():
            if 'time' in key:
                print(f"  {key}: {value:.2f} 秒")
            else:
                print(f"  {key}: {value}")
        
        self.demo_results['attack_engine'] = {
            'plan': mock_plan.__dict__ if hasattr(mock_plan, '__dict__') else {},
            'context': mock_context.__dict__ if hasattr(mock_context, '__dict__') else {},
            'metrics': mock_metrics
        }
        
        return True
    
    async def demo_integration_workflow(self):
        """演示集成工作流"""
        self.print_header("演示 4: 完整集成工作流")
        
        print("完整攻击模拟工作流:")
        print("  1. AI分析目标并生成攻击计划")
        print("  2. 工具链协调器执行侦察阶段")
        print("  3. 解析器分析工具输出")
        print("  4. AI根据结果调整攻击策略")
        print("  5. 工具链协调器执行漏洞利用")
        print("  6. 攻击引擎监控执行状态")
        print("  7. 生成详细攻击报告")
        
        self.print_section("工作流示例")
        
        workflow_steps = [
            ("目标分析", "AI分析CTF挑战描述，识别潜在攻击向量"),
            ("侦察阶段", "Nmap扫描开放端口，Dirb爆破目录，Nikto扫描漏洞"),
            ("漏洞分析", "解析工具输出，识别SQL注入、XSS等漏洞"),
            ("攻击规划", "AI生成针对性的漏洞利用方案"),
            ("漏洞利用", "SQLMap执行注入攻击，尝试获取数据库访问"),
            ("权限提升", "尝试获取系统权限，访问敏感文件"),
            ("数据提取", "提取flag和敏感信息"),
            ("清理痕迹", "清除攻击痕迹（模拟）"),
            ("报告生成", "生成详细攻击报告和教育分析")
        ]
        
        for i, (step, description) in enumerate(workflow_steps, 1):
            print(f"  {i}. {step}: {description}")
            await asyncio.sleep(0.1)  # 轻微延迟，使演示更自然
        
        self.print_section("预期输出")
        
        expected_output = {
            "attack_id": "workflow_demo_001",
            "target": "ctf-challenge.example.com",
            "duration": "3分45秒",
            "phases_completed": ["reconnaissance", "vulnerability_analysis", "exploitation"],
            "flags_found": [
                "flag{sql_injection_success}",
                "flag{admin_panel_access}",
                "flag{root_shell_obtained}"
            ],
            "vulnerabilities": [
                {"type": "SQL Injection", "severity": "high", "cvss": 8.5},
                {"type": "XSS", "severity": "medium", "cvss": 6.1},
                {"type": "Directory Traversal", "severity": "medium", "cvss": 5.8}
            ],
            "educational_insights": [
                "SQL注入漏洞源于未过滤的用户输入",
                "XSS漏洞可通过输出编码修复",
                "目录遍历漏洞需要路径验证"
            ]
        }
        
        print("完整攻击工作流预期结果:")
        print(json.dumps(expected_output, indent=2, ensure_ascii=False))
        
        self.demo_results['integration_workflow'] = expected_output
        
        return True
    
    async def run_all_demos(self):
        """运行所有演示"""
        self.print_header("CTF AI攻击模拟系统 - 组件演示")
        print("演示所有三个核心组件:")
        print("  1. 安全工具深度集成 - 工具输出解析器")
        print("  2. 工具链协调机制 - 多工具协同执行")
        print("  3. 攻击执行引擎优化 - 完整攻击工作流")
        
        try:
            # 运行各个演示
            await self.demo_tool_parsers()
            await asyncio.sleep(1)
            
            await self.demo_tool_coordination()
            await asyncio.sleep(1)
            
            await self.demo_attack_engine()
            await asyncio.sleep(1)
            
            await self.demo_integration_workflow()
            
            # 保存演示结果
            self.save_demo_results()
            
            self.print_header("演示完成")
            print("所有组件演示成功完成！")
            print("\n系统已具备以下能力:")
            print("  ✓ 智能解析安全工具输出")
            print("  ✓ 协调多工具协同攻击")
            print("  ✓ AI驱动的攻击计划生成")
            print("  ✓ 完整的攻击执行工作流")
            print("  ✓ 详细的结果分析和报告")
            
            return True
            
        except Exception as e:
            self.logger.error(f"演示失败: {e}")
            print(f"\n演示过程中出现错误: {e}")
            return False
    
    def save_demo_results(self):
        """保存演示结果"""
        try:
            os.makedirs("logs", exist_ok=True)
            
            demo_file = "logs/component_demo_results.json"
            with open(demo_file, 'w', encoding='utf-8') as f:
                json.dump(self.demo_results, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"演示结果已保存: {demo_file}")
            
        except Exception as e:
            self.logger.error(f"保存演示结果失败: {e}")


# 导入os模块
import os

async def main():
    """主函数"""
    demo = ComponentDemo()
    success = await demo.run_all_demos()
    
    return success


if __name__ == "__main__":
    # 运行演示
    print("CTF AI攻击模拟系统 - 组件演示")
    print("版本: 1.0.0")
    print("作者: 毕业设计项目组")
    print()
    
    try:
        success = asyncio.run(main())
        
        if success:
            print("\n" + "=" * 70)
            print(" 演示成功！系统组件功能完整，可以用于CTF攻击模拟。")
            print("=" * 70)
            sys.exit(0)
        else:
            print("\n" + "=" * 70)
            print(" 演示失败，请检查错误日志。")
            print("=" * 70)
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n演示被用户中断。")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n演示发生错误: {e}")
        sys.exit(1)