#!/usr/bin/env python3
"""
检查目标服务器状态
"""

import asyncio
import aiohttp
import sys

async def check_target(url):
    """检查目标URL是否可达"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=10) as response:
                print(f"状态码: {response.status}")
                print(f"响应头: {dict(response.headers)}")
                text = await response.text()
                print(f"响应长度: {len(text)}")
                print(f"响应预览: {text[:200]}")
                return True
        except Exception as e:
            print(f"错误: {e}")
            return False

async def main():
    if len(sys.argv) < 2:
        print("用法: python check_target.py <URL>")
        return
    
    url = sys.argv[1]
    print(f"检查目标: {url}")
    
    # 检查主页面
    print("\n1. 检查主页面:")
    await check_target(url)
    
    # 检查check.php
    if not url.endswith('/check.php'):
        check_url = url.rstrip('/') + '/check.php'
        print(f"\n2. 检查check.php: {check_url}")
        await check_target(check_url)
    
    # 检查其他常见端点
    endpoints = ['/', '/index.php', '/login.php', '/admin.php']
    for endpoint in endpoints:
        test_url = url.rstrip('/') + endpoint
        print(f"\n3. 检查{endpoint}: {test_url}")
        await check_target(test_url)

if __name__ == "__main__":
    asyncio.run(main())