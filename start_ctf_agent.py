#!/usr/bin/env python3
"""
CTF Agent系统启动脚本
一键启动CTF Agent API服务器和必要组件
"""

import os
import sys
import subprocess
import time
import signal
import threading
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent


class CTFAgentLauncher:
    """CTF Agent启动器"""
    
    def __init__(self):
        self.processes = []
        self.log_files = []
        
    def check_dependencies(self):
        """检查依赖"""
        print("🔍 检查系统依赖...")
        
        # 检查Python版本
        python_version = sys.version_info
        if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
            print(f"❌ 需要Python 3.8+，当前版本: {sys.version}")
            return False
        
        print(f"✅ Python版本: {sys.version}")
        
        # 检查必要工具
        required_tools = ["sqlmap", "nmap"]
        for tool in required_tools:
            try:
                subprocess.run([tool, "--version"], capture_output=True, check=False)
                print(f"✅ {tool} 已安装")
            except FileNotFoundError:
                print(f"⚠️  {tool} 未安装，部分功能可能受限")
        
        return True
    
    def install_python_dependencies(self):
        """安装Python依赖"""
        print("\n📦 安装Python依赖...")
        
        requirements_file = PROJECT_ROOT / "requirements.txt"
        if not requirements_file.exists():
            print("❌ 未找到requirements.txt文件")
            return False
        
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
                check=True
            )
            print("✅ Python依赖安装完成")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 依赖安装失败: {e}")
            return False
    
    def setup_environment(self):
        """设置环境"""
        print("\n⚙️  设置环境...")
        
        # 创建必要目录
        directories = ["logs", "reports", "data"]
        for dir_name in directories:
            dir_path = PROJECT_ROOT / dir_name
            dir_path.mkdir(exist_ok=True)
            print(f"✅ 创建目录: {dir_name}")
        
        # 检查配置文件
        config_file = PROJECT_ROOT / "config" / "development.yaml"
        if not config_file.exists():
            print("⚠️  配置文件不存在，将使用默认配置")
            # 可以在这里创建默认配置文件
        
        # 检查环境变量文件
        env_example = PROJECT_ROOT / ".env.example"
        env_file = PROJECT_ROOT / ".env"
        
        if not env_file.exists() and env_example.exists():
            print("⚠️  .env文件不存在，从.example复制")
            import shutil
            shutil.copy(env_example, env_file)
            print("✅ 已创建.env文件，请编辑它设置API密钥等")
        
        return True
    
    def start_api_server(self, host="0.0.0.0", port=8000):
        """启动API服务器"""
        print(f"\n🚀 启动CTF Agent API服务器 (http://{host}:{port})...")
        
        # 创建日志文件
        log_file = PROJECT_ROOT / "logs" / "api_server.log"
        self.log_files.append(log_file)
        
        with open(log_file, "w") as f:
            f.write(f"CTF Agent API服务器启动于 {time.ctime()}\n")
        
        # 启动服务器进程
        server_script = PROJECT_ROOT / "src" / "api" / "server.py"
        
        if not server_script.exists():
            print(f"❌ 服务器脚本不存在: {server_script}")
            return False
        
        try:
            # 使用uvicorn启动FastAPI服务器
            cmd = [
                sys.executable, "-m", "uvicorn",
                "src.api.server:app",
                "--host", host,
                "--port", str(port),
                "--reload",
                "--log-level", "info"
            ]
            
            process = subprocess.Popen(
                cmd,
                cwd=PROJECT_ROOT,
                stdout=open(log_file, "a"),
                stderr=subprocess.STDOUT,
                text=True
            )
            
            self.processes.append(("API服务器", process))
            
            # 等待服务器启动
            print("⏳ 等待服务器启动...")
            time.sleep(3)
            
            # 检查服务器是否运行
            try:
                import requests
                response = requests.get(f"http://{host}:{port}/", timeout=5)
                if response.status_code == 200:
                    print(f"✅ API服务器启动成功: http://{host}:{port}")
                    print(f"📚 API文档: http://{host}:{port}/docs")
                    return True
            except:
                pass
            
            print("⚠️  服务器启动中，可能需要更多时间...")
            return True
            
        except Exception as e:
            print(f"❌ 启动API服务器失败: {e}")
            return False
    
    def start_mcp_server(self):
        """启动MCP服务器（如果需要）"""
        print("\n🔧 启动MCP服务器...")
        
        # 检查MCP服务器实现
        mcp_server_script = PROJECT_ROOT / "src" / "mcp_server" / "server.py"
        
        if not mcp_server_script.exists():
            print("⚠️  MCP服务器脚本不存在，跳过")
            return True
        
        # 创建日志文件
        log_file = PROJECT_ROOT / "logs" / "mcp_server.log"
        self.log_files.append(log_file)
        
        try:
            # 在后台线程中启动MCP服务器
            def run_mcp_server():
                try:
                    import asyncio
                    from src.mcp_server.server import CTFMCPServer
                    
                    server = CTFMCPServer()
                    asyncio.run(server.run())
                except Exception as e:
                    print(f"MCP服务器错误: {e}")
            
            thread = threading.Thread(target=run_mcp_server, daemon=True)
            thread.start()
            
            print("✅ MCP服务器已启动（后台线程）")
            return True
            
        except Exception as e:
            print(f"❌ 启动MCP服务器失败: {e}")
            return False
    
    def monitor_processes(self):
        """监控进程"""
        print("\n👁️  监控进程状态...")
        print("按Ctrl+C停止所有进程")
        
        try:
            while True:
                alive_processes = []
                for name, process in self.processes:
                    if process.poll() is None:
                        alive_processes.append((name, process))
                    else:
                        print(f"⚠️  {name} 已停止 (退出码: {process.returncode})")
                
                self.processes = alive_processes
                
                if not self.processes:
                    print("所有进程已停止")
                    break
                
                time.sleep(5)
                
        except KeyboardInterrupt:
            print("\n🛑 收到停止信号，正在停止所有进程...")
            self.stop_all_processes()
    
    def stop_all_processes(self):
        """停止所有进程"""
        print("\n🛑 停止所有进程...")
        
        for name, process in self.processes:
            print(f"停止 {name}...")
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass
        
        self.processes.clear()
        print("✅ 所有进程已停止")
    
    def show_usage(self):
        """显示使用说明"""
        print("\n" + "="*60)
        print("CTF Agent系统使用说明")
        print("="*60)
        print("\n📌 系统已启动，您现在可以:")
        print("\n1. 使用API客户端:")
        print("   python api_client_example.py --demo full")
        print("\n2. 直接调用API:")
        print("   curl http://localhost:8000/status")
        print("   curl http://localhost:8000/docs")
        print("\n3. 提交CTF挑战:")
        print("   curl -X POST http://localhost:8000/challenge \\")
        print("     -H 'Content-Type: application/json' \\")
        print("     -d '{\"title\":\"测试挑战\",\"target_url\":\"http://example.com\",...}'")
        print("\n4. 查看日志:")
        print("   tail -f logs/api_server.log")
        print("\n5. 停止系统:")
        print("   按Ctrl+C")
        print("="*60)
    
    def run(self):
        """运行启动器"""
        print("="*60)
        print("CTF Agent系统启动器")
        print("="*60)
        
        # 检查依赖
        if not self.check_dependencies():
            return False
        
        # 安装依赖（可选）
        install = input("\n是否安装Python依赖？(y/n): ").lower().strip()
        if install == 'y':
            if not self.install_python_dependencies():
                return False
        
        # 设置环境
        if not self.setup_environment():
            return False
        
        # 获取服务器配置
        host = input(f"\nAPI服务器主机 (默认: 0.0.0.0): ").strip() or "0.0.0.0"
        port_input = input(f"API服务器端口 (默认: 8000): ").strip()
        port = int(port_input) if port_input else 8000
        
        # 启动MCP服务器
        self.start_mcp_server()
        
        # 启动API服务器
        if not self.start_api_server(host, port):
            return False
        
        # 显示使用说明
        self.show_usage()
        
        # 监控进程
        try:
            self.monitor_processes()
        except KeyboardInterrupt:
            print("\n👋 再见！")
        
        return True


def quick_start():
    """快速启动（无交互）"""
    launcher = CTFAgentLauncher()
    
    # 基本检查
    if not launcher.check_dependencies():
        return False
    
    # 设置环境
    launcher.setup_environment()
    
    # 启动服务器
    launcher.start_mcp_server()
    launcher.start_api_server()
    
    # 显示信息
    print("\n✅ CTF Agent系统已启动！")
    print("📚 API文档: http://localhost:8000/docs")
    print("🛑 按Ctrl+C停止系统")
    
    try:
        launcher.monitor_processes()
    except KeyboardInterrupt:
        launcher.stop_all_processes()
    
    return True


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="CTF Agent系统启动器")
    parser.add_argument("--quick", action="store_true", help="快速启动模式")
    
    args = parser.parse_args()
    
    if args.quick:
        quick_start()
    else:
        launcher = CTFAgentLauncher()
        launcher.run()


if __name__ == "__main__":
    main()