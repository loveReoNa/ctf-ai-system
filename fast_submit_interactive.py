#!/usr/bin/env python3
"""
CTF Agent 交互式快速提交工具
最简单的方式提交靶机题目
"""

import requests
import sys

def check_server():
    """检查API服务器是否运行"""
    try:
        response = requests.get("http://localhost:8000/", timeout=3)
        return response.status_code == 200
    except:
        return False

def main():
    print("🚀 CTF Agent 快速提交工具")
    print("=" * 40)
    
    # 检查服务器
    print("检查CTF Agent系统状态...")
    if not check_server():
        print("❌ CTF Agent API服务器未运行！")
        print("请先启动系统:")
        print("  1. python start_ctf_agent.py --quick")
        print("  2. 或手动启动: python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000")
        input("\n按Enter键退出...")
        return
    
    print("✅ CTF Agent系统正在运行")
    print()
    
    # 获取靶机URL
    print("请输入靶机URL（例如: http://example.com/vuln.php?id=1）")
    print("或输入 'demo' 使用演示URL")
    
    url_input = input("靶机URL: ").strip()
    
    if url_input.lower() == 'demo':
        target_url = "http://testphp.vulnweb.com/artists.php?artist=1"
        print(f"使用演示URL: {target_url}")
    elif url_input:
        target_url = url_input
    else:
        print("❌ 未提供URL")
        return
    
    # 选择挑战类型
    print("\n选择挑战类型:")
    print("  1. Web安全 (SQL注入、XSS等)")
    print("  2. 网络扫描 (端口扫描、服务识别)")
    print("  3. 其他 (默认)")
    
    type_choice = input("选择 [1-3, 默认1]: ").strip()
    
    if type_choice == "2":
        category = "network"
        title = "网络扫描挑战"
    elif type_choice == "3":
        category = "misc"
        title = "综合挑战"
    else:
        category = "web"
        title = "Web安全挑战"
    
    # 选择难度
    print("\n选择难度:")
    print("  1. 简单 (easy)")
    print("  2. 中等 (medium)")
    print("  3. 困难 (hard)")
    
    diff_choice = input("选择 [1-3, 默认2]: ").strip()
    
    if diff_choice == "1":
        difficulty = "easy"
    elif diff_choice == "3":
        difficulty = "hard"
    else:
        difficulty = "medium"
    
    # 构建挑战数据
    challenge_data = {
        "title": title,
        "description": f"快速提交的靶机挑战: {target_url}",
        "target_url": target_url,
        "category": category,
        "difficulty": difficulty,
        "hints": ["系统自动分析中..."]
    }
    
    print("\n" + "=" * 40)
    print("提交挑战信息:")
    print(f"  标题: {title}")
    print(f"  URL: {target_url}")
    print(f"  类型: {category}")
    print(f"  难度: {difficulty}")
    print("=" * 40)
    
    confirm = input("\n确认提交？(y/n): ").strip().lower()
    if confirm != 'y':
        print("取消提交")
        return
    
    # 提交挑战
    print("\n⏳ 正在提交挑战...")
    try:
        response = requests.post(
            "http://localhost:8000/challenge",
            json=challenge_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            task_id = result["task_id"]
            
            print("✅ 挑战提交成功！")
            print(f"📋 任务ID: {task_id}")
            print(f"📊 状态: {result['status']}")
            
            # 询问是否监控
            print("\n是否要监控任务进度？")
            monitor = input("监控任务进度？(y/n, 默认n): ").strip().lower()
            
            if monitor == 'y':
                print(f"\n⏳ 开始监控任务 {task_id}...")
                print("按Ctrl+C停止监控")
                print()
                
                import time
                try:
                    for i in range(60):  # 最多监控5分钟
                        try:
                            status_resp = requests.get(f"http://localhost:8000/tasks/{task_id}", timeout=5)
                            status = status_resp.json()
                            
                            # 创建进度条
                            progress = int(status['progress'] * 50)
                            progress_bar = "[" + "=" * progress + " " * (50 - progress) + "]"
                            
                            print(f"状态: {status['status']:12} {progress_bar} {status['progress']:.1%}")
                            
                            if status['status'] in ['completed', 'failed']:
                                if status['status'] == 'completed':
                                    result = status.get('result', {})
                                    if result.get('success'):
                                        print(f"\n🎉 攻击成功！")
                                        flag = result.get('execution', {}).get('final_flag')
                                        if flag:
                                            print(f"Flag: {flag}")
                                    else:
                                        print(f"\n❌ 攻击失败")
                                else:
                                    print(f"\n❌ 任务失败: {status.get('error')}")
                                break
                                
                        except requests.exceptions.RequestException:
                            print("连接失败，重试...")
                        
                        time.sleep(5)  # 每5秒检查一次
                        
                except KeyboardInterrupt:
                    print("\n🛑 监控已停止")
                
                print(f"\n💡 提示: 可随时使用以下命令检查任务状态:")
                print(f"curl http://localhost:8000/tasks/{task_id}")
            
            else:
                print(f"\n💡 提示:")
                print(f"1. 手动检查任务: curl http://localhost:8000/tasks/{task_id}")
                print(f"2. 查看API文档: http://localhost:8000/docs")
                print(f"3. 查看日志: tail -f logs/api_server.log")
                
        else:
            print(f"❌ 提交失败 (HTTP {response.status_code}):")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务器")
    except Exception as e:
        print(f"❌ 发生错误: {e}")
    
    input("\n按Enter键退出...")

if __name__ == "__main__":
    main()