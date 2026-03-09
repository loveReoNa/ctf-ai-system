#!/usr/bin/env python3
"""
CTF Agent API客户端示例
演示如何通过API调用CTF Agent进行自动解题
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional


class CTFAgentClient:
    """CTF Agent API客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        初始化客户端
        
        Args:
            base_url: API服务器基础URL
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
    def check_server_status(self) -> bool:
        """检查服务器状态"""
        try:
            response = self.session.get(f"{self.base_url}/", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_agent_status(self) -> Dict[str, Any]:
        """获取Agent状态"""
        response = self.session.get(f"{self.base_url}/status")
        response.raise_for_status()
        return response.json()
    
    def submit_challenge(self, challenge_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        提交CTF挑战
        
        Args:
            challenge_data: 挑战数据
            
        Returns:
            任务创建响应
        """
        response = self.session.post(
            f"{self.base_url}/challenge",
            json=challenge_data,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        response = self.session.get(f"{self.base_url}/tasks/{task_id}")
        response.raise_for_status()
        return response.json()
    
    def wait_for_task_completion(self, task_id: str, timeout: int = 300, poll_interval: int = 2) -> Dict[str, Any]:
        """
        等待任务完成
        
        Args:
            task_id: 任务ID
            timeout: 超时时间（秒）
            poll_interval: 轮询间隔（秒）
            
        Returns:
            最终任务状态
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_task_status(task_id)
            
            print(f"任务状态: {status['status']}, 进度: {status['progress']:.1%}")
            
            if status['status'] in ['completed', 'failed']:
                return status
            
            time.sleep(poll_interval)
        
        raise TimeoutError(f"任务 {task_id} 在 {timeout} 秒后仍未完成")
    
    def list_tools(self) -> Dict[str, Any]:
        """获取可用工具列表"""
        response = self.session.get(f"{self.base_url}/tools")
        response.raise_for_status()
        return response.json()
    
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """直接执行工具"""
        response = self.session.post(
            f"{self.base_url}/tools/execute",
            json={"tool_name": tool_name, "parameters": parameters},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()
    
    def initialize_agent(self) -> Dict[str, Any]:
        """初始化Agent"""
        response = self.session.post(f"{self.base_url}/agent/initialize")
        response.raise_for_status()
        return response.json()
    
    def reset_agent(self) -> Dict[str, Any]:
        """重置Agent"""
        response = self.session.post(f"{self.base_url}/agent/reset")
        response.raise_for_status()
        return response.json()


def example_web_sqli_challenge() -> Dict[str, Any]:
    """创建Web SQL注入挑战示例"""
    return {
        "title": "BUUOJ SQL注入挑战",
        "description": "一个存在SQL注入漏洞的Web应用，需要获取flag",
        "target_url": "http://600ac8e9-f9ec-49c6-b102-89b50c62b2be.node5.buuoj.cn:81/check.php",
        "category": "web",
        "difficulty": "medium",
        "hints": [
            "尝试SQL注入",
            "查看URL参数",
            "使用报错注入技术"
        ],
        "expected_flag": None  # 未知flag
    }


def example_xss_challenge() -> Dict[str, Any]:
    """创建XSS挑战示例"""
    return {
        "title": "XSS跨站脚本挑战",
        "description": "一个存在XSS漏洞的Web应用，需要执行JavaScript获取flag",
        "target_url": "http://testphp.vulnweb.com/search.php?test=query",
        "category": "web",
        "difficulty": "easy",
        "hints": [
            "尝试反射型XSS",
            "查看搜索参数",
            "使用alert()测试"
        ]
    }


def demo_full_workflow(client: CTFAgentClient):
    """演示完整工作流程"""
    print("="*60)
    print("CTF Agent API 完整工作流程演示")
    print("="*60)
    
    # 1. 检查服务器状态
    print("\n1. 检查服务器状态...")
    if not client.check_server_status():
        print("❌ 服务器未运行，请先启动API服务器")
        return
    
    print("✅ 服务器运行正常")
    
    # 2. 获取Agent状态
    print("\n2. 获取Agent状态...")
    status = client.get_agent_status()
    print(f"   Agent状态: {status['state']}")
    print(f"   可用工具: {', '.join(status['tools_available'])}")
    
    # 3. 初始化Agent（如果需要）
    if not status['initialized']:
        print("\n3. 初始化Agent...")
        init_result = client.initialize_agent()
        print(f"   初始化结果: {init_result['message']}")
    
    # 4. 提交挑战
    print("\n4. 提交CTF挑战...")
    challenge = example_web_sqli_challenge()
    print(f"   挑战标题: {challenge['title']}")
    print(f"   目标URL: {challenge['target_url']}")
    
    task_response = client.submit_challenge(challenge)
    task_id = task_response['task_id']
    print(f"   任务ID: {task_id}")
    print(f"   任务状态: {task_response['status']}")
    
    # 5. 等待任务完成
    print("\n5. 等待任务执行...")
    print("   (这可能需要几分钟，请耐心等待)")
    
    try:
        final_status = client.wait_for_task_completion(task_id, timeout=600)
        
        print(f"\n   最终状态: {final_status['status']}")
        print(f"   进度: {final_status['progress']:.1%}")
        
        if final_status['status'] == 'completed':
            result = final_status.get('result', {})
            
            if result.get('success'):
                print("   ✅ 攻击成功!")
                
                # 检查是否找到flag
                execution = result.get('execution', {})
                if execution.get('flag_found'):
                    flag = execution.get('final_flag')
                    print(f"   🎉 找到Flag: {flag}")
                else:
                    print("   ⚠️  攻击完成但未找到flag")
                
                # 显示攻击摘要
                print(f"\n   攻击摘要:")
                print(f"     总步骤: {execution.get('total_steps', 0)}")
                print(f"     成功步骤: {execution.get('successful_steps', 0)}")
                print(f"     失败步骤: {execution.get('failed_steps', 0)}")
                
            else:
                print("   ❌ 攻击失败")
                if 'error' in result:
                    print(f"   错误: {result['error']}")
        
        elif final_status['status'] == 'failed':
            print("   ❌ 任务失败")
            if final_status.get('error'):
                print(f"   错误: {final_status['error']}")
    
    except TimeoutError as e:
        print(f"   ⏰ {e}")
        print("   任务仍在运行，您可以使用以下命令检查状态:")
        print(f"   curl {client.base_url}/tasks/{task_id}")
    
    except Exception as e:
        print(f"   ❌ 等待过程中发生错误: {e}")


def demo_tool_execution(client: CTFAgentClient):
    """演示直接工具执行"""
    print("\n" + "="*60)
    print("直接工具执行演示")
    print("="*60)
    
    # 1. 获取可用工具
    print("\n1. 获取可用工具列表...")
    tools_response = client.list_tools()
    tools = tools_response.get('tools', [])
    
    if not tools:
        print("   ⚠️  没有可用工具")
        return
    
    print(f"   发现 {len(tools)} 个工具:")
    for tool in tools[:5]:  # 显示前5个工具
        print(f"     - {tool.get('name')}: {tool.get('description', '无描述')}")
    
    # 2. 执行SQLMap扫描
    print("\n2. 执行SQLMap扫描工具...")
    
    # 查找sqlmap工具
    sqlmap_tools = [t for t in tools if 'sqlmap' in t.get('name', '').lower()]
    
    if sqlmap_tools:
        tool_name = sqlmap_tools[0]['name']
        print(f"   使用工具: {tool_name}")
        
        # 执行扫描
        try:
            result = client.execute_tool(
                tool_name,
                {
                    "url": "http://testphp.vulnweb.com/artists.php?artist=1",
                    "level": 1,
                    "risk": 1,
                    "timeout": 30
                }
            )
            
            print(f"   执行结果: {'成功' if result['success'] else '失败'}")
            print(f"   执行时间: {result['execution_time']:.2f}秒")
            
            if result['success']:
                print("   ✅ 工具执行成功")
                # 可以进一步解析结果
            else:
                print(f"   ❌ 工具执行失败: {result.get('error', '未知错误')}")
                
        except Exception as e:
            print(f"   ❌ 工具执行异常: {e}")
    else:
        print("   ⚠️  未找到SQLMap工具")


def demo_quick_test(client: CTFAgentClient):
    """快速测试演示"""
    print("\n" + "="*60)
    print("快速测试演示")
    print("="*60)
    
    # 创建简单挑战
    challenge = {
        "title": "快速测试挑战",
        "description": "这是一个快速测试挑战",
        "target_url": "http://testphp.vulnweb.com/",
        "category": "web",
        "difficulty": "easy",
        "hints": ["这是一个测试"]
    }
    
    print(f"\n提交测试挑战: {challenge['title']}")
    
    try:
        response = client.submit_challenge(challenge)
        task_id = response['task_id']
        print(f"任务创建成功，ID: {task_id}")
        print(f"您可以使用以下命令检查状态:")
        print(f"curl {client.base_url}/tasks/{task_id}")
        
    except Exception as e:
        print(f"提交失败: {e}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="CTF Agent API客户端")
    parser.add_argument("--url", default="http://localhost:8000", help="API服务器URL")
    parser.add_argument("--demo", choices=["full", "tools", "quick", "all"], default="quick",
                       help="演示模式: full(完整流程), tools(工具执行), quick(快速测试), all(全部)")
    
    args = parser.parse_args()
    
    # 创建客户端
    client = CTFAgentClient(args.url)
    
    print(f"连接到CTF Agent API: {args.url}")
    
    # 检查连接
    if not client.check_server_status():
        print(f"❌ 无法连接到API服务器: {args.url}")
        print("请确保API服务器正在运行:")
        print("  python src/api/server.py")
        sys.exit(1)
    
    print("✅ 成功连接到API服务器")
    
    # 根据参数运行演示
    if args.demo == "full" or args.demo == "all":
        demo_full_workflow(client)
    
    if args.demo == "tools" or args.demo == "all":
        demo_tool_execution(client)
    
    if args.demo == "quick" or args.demo == "all":
        demo_quick_test(client)
    
    print("\n" + "="*60)
    print("演示完成")
    print("="*60)
    print("\n更多API端点:")
    print(f"  {args.url}/docs - API文档")
    print(f"  {args.url}/status - 系统状态")
    print(f"  {args.url}/tasks - 任务列表")
    print(f"  {args.url}/tools - 工具列表")


if __name__ == "__main__":
    main()