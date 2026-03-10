#!/usr/bin/env python3
"""
极简靶机URL提交工具
用法: python submit_url.py <靶机URL>
"""

import requests
import sys

if len(sys.argv) < 2:
    print("用法: python submit_url.py <靶机URL>")
    print("示例: python submit_url.py http://example.com/vuln.php")
    sys.exit(1)

url = sys.argv[1]
api = "http://localhost:8000"

data = {
    "title": "靶机挑战",
    "description": f"目标: {url}",
    "target_url": url,
    "category": "web",
    "difficulty": "medium"
}

try:
    r = requests.post(f"{api}/challenge", json=data)
    if r.status_code == 200:
        task = r.json()
        print(f"✅ 已提交")
        print(f"任务ID: {task['task_id']}")
        print(f"状态: {task['status']}")
        print(f"\n检查状态: curl {api}/tasks/{task['task_id']}")
    else:
        print(f"❌ 失败: {r.status_code}")
        print(r.text)
except:
    print("❌ 连接失败，请确保CTF Agent已启动")
    print("启动命令: python start_ctf_agent.py --quick")