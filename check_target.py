#!/usr/bin/env python3
"""
检查目标网站结构
"""

import requests
import re
import sys

def check_target(url):
    """检查目标网站"""
    print(f"检查目标: {url}")
    print("="*60)
    
    try:
        # 获取主页
        r = requests.get(url, timeout=10)
        print(f"状态码: {r.status_code}")
        print(f"响应长度: {len(r.text)} 字节")
        
        # 检查标题
        title_match = re.search(r'<title>(.*?)</title>', r.text, re.IGNORECASE)
        if title_match:
            print(f"标题: {title_match.group(1)}")
        else:
            print("标题: 未找到")
        
        # 检查表单
        forms = re.findall(r'<form[^>]*>', r.text, re.IGNORECASE)
        print(f"\n表单数量: {len(forms)}")
        
        for i, form_tag in enumerate(forms):
            print(f"\n表单 {i+1}:")
            print(f"  HTML: {form_tag}")
            
            # 提取action属性
            action_match = re.search(r'action=["\']([^"\']+)["\']', form_tag, re.IGNORECASE)
            if action_match:
                action = action_match.group(1)
                print(f"  Action: {action}")
                
                # 构建完整URL
                if action.startswith('http'):
                    form_url = action
                elif action.startswith('/'):
                    from urllib.parse import urlparse
                    parsed = urlparse(url)
                    form_url = f"{parsed.scheme}://{parsed.netloc}{action}"
                else:
                    form_url = f"{url.rstrip('/')}/{action}"
                
                print(f"  完整URL: {form_url}")
        
        # 检查可能的端点
        print(f"\n检查常见端点...")
        common_endpoints = [
            '/check.php', '/login.php', '/admin.php', '/index.php',
            '/search.php', '/query.php', '/api.php', '/user.php'
        ]
        
        for endpoint in common_endpoints:
            test_url = f"{url.rstrip('/')}{endpoint}"
            try:
                r_test = requests.get(test_url, timeout=3)
                if r_test.status_code < 400:
                    print(f"  {endpoint}: 存在 (状态码: {r_test.status_code})")
                else:
                    print(f"  {endpoint}: 不存在或错误 (状态码: {r_test.status_code})")
            except:
                print(f"  {endpoint}: 请求失败")
        
        # 检查robots.txt
        robots_url = f"{url.rstrip('/')}/robots.txt"
        try:
            r_robots = requests.get(robots_url, timeout=3)
            if r_robots.status_code == 200:
                print(f"\nrobots.txt 内容:")
                print(r_robots.text[:500])
        except:
            pass
        
        print("\n" + "="*60)
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    target = "http://600ac8e9-f9ec-49c6-b102-89b50c62b2be.node5.buuoj.cn:81"
    check_target(target)