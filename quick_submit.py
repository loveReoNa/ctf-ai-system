#!/usr/bin/env python3
"""
CTF Agent 快速提交脚本
只需提供靶机URL即可快速提交题目
"""

import requests
import sys
import json

def quick_submit(target_url, title=None, category="web", difficulty="medium"):
    """
    快速提交靶机URL题目
    
    Args:
        target_url: 靶机URL
        title: 挑战标题（可选，自动生成）
        category: 挑战类别（web, crypto等）
        difficulty: 难度（easy, medium, hard）
    """
    
    API_URL = "http://localhost:8000"
    
    # 自动生成标题
    if not title:
        from urllib.parse import urlparse
        parsed = urlparse(target_url)
        title = f"靶机挑战 - {parsed.netloc}"
    
    # 构建挑战数据
    challenge_data = {
        "title": title,
        "description": f"靶机URL挑战: {target_url}",
        "target_url": target_url,
        "category": category,
        "difficulty": difficulty,
        "hints": ["系统自动分析中..."]
    }
    
    try:
        # 提交挑战
        response = requests.post(
            f"{API_URL}/challenge",
            json=challenge_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            task_id = result["task_id"]
            
            print("✅ 挑战提交成功！")
            print(f"📋 任务ID: {task_id}")
            print(f"🎯 目标URL: {target_url}")
            print(f"📊 状态: {result['status']}")
            print(f"📝 消息: {result['message']}")
            print(f"\n🔍 监控任务进度:")
            print(f"   curl {API_URL}/tasks/{task_id}")
            print(f"   或访问: {API_URL}/docs")
            
            return task_id
        else:
            print(f"❌ 提交失败 (HTTP {response.status_code}):")
            print(response.text)
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到CTF Agent API服务器")
        print("请确保已启动系统: python start_ctf_agent.py --quick")
        return None
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        return None

def monitor_task(task_id, timeout=300):
    """监控任务进度"""
    import time
    
    API_URL = "http://localhost:8000"
    
    print(f"\n⏳ 监控任务 {task_id}...")
    print("按Ctrl+C停止监控")
    
    try:
        for i in range(timeout // 5):  # 每5秒检查一次
            try:
                response = requests.get(f"{API_URL}/tasks/{task_id}", timeout=5)
                status = response.json()
                
                print(f"检查 {i+1}: 状态={status['status']}, 进度={status['progress']:.0%}")
                
                if status['status'] == 'completed':
                    result = status.get('result', {})
                    if result.get('success'):
                        print(f"\n✅ 攻击成功！")
                        execution = result.get('execution', {})
                        if execution.get('flag_found'):
                            print(f"🎉 Flag: {execution.get('final_flag')}")
                        else:
                            print("⚠️  攻击完成但未找到flag")
                        
                        # 显示攻击摘要
                        print(f"\n📊 攻击摘要:")
                        print(f"  总步骤: {execution.get('total_steps', 0)}")
                        print(f"  成功步骤: {execution.get('successful_steps', 0)}")
                        print(f"  失败步骤: {execution.get('failed_steps', 0)}")
                    else:
                        print(f"\n❌ 攻击失败: {result.get('error', '未知错误')}")
                    break
                    
                elif status['status'] == 'failed':
                    print(f"\n❌ 任务失败: {status.get('error', '未知错误')}")
                    break
                    
            except requests.exceptions.RequestException:
                print(f"检查 {i+1}: 连接失败，重试...")
            
            time.sleep(5)  # 等待5秒
            
    except KeyboardInterrupt:
        print("\n🛑 监控已停止")
        print(f"任务仍在后台运行，可使用以下命令检查:")
        print(f"curl {API_URL}/tasks/{task_id}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="CTF Agent 快速提交工具")
    parser.add_argument("url", help="靶机URL")
    parser.add_argument("--title", "-t", help="挑战标题（可选）")
    parser.add_argument("--category", "-c", default="web", 
                       choices=["web", "crypto", "pwn", "reverse", "misc", "forensics"],
                       help="挑战类别")
    parser.add_argument("--difficulty", "-d", default="medium",
                       choices=["easy", "medium", "hard"],
                       help="难度级别")
    parser.add_argument("--monitor", "-m", action="store_true",
                       help="提交后自动监控任务进度")
    parser.add_argument("--timeout", default=300, type=int,
                       help="监控超时时间（秒）")
    
    args = parser.parse_args()
    
    # 提交挑战
    task_id = quick_submit(
        target_url=args.url,
        title=args.title,
        category=args.category,
        difficulty=args.difficulty
    )
    
    # 如果需要监控
    if task_id and args.monitor:
        monitor_task(task_id, args.timeout)

if __name__ == "__main__":
    main()