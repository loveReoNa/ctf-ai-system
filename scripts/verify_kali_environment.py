#!/usr/bin/env python3
"""
Kali Linux环境验证脚本
验证所有必要的工具和配置是否就绪
"""
import os
import sys
import subprocess
import platform
from pathlib import Path


def run_command(cmd, check=True):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, check=check
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stdout.strip(), e.stderr.strip()


def print_check(name, success, message=""):
    """打印检查结果"""
    icon = "✅" if success else "❌"
    color = "\033[92m" if success else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{icon} {name}: {message}{reset}")
    return success


def main():
    print("=" * 60)
    print("Kali Linux环境验证")
    print("=" * 60)
    
    checks_passed = 0
    checks_total = 0
    
    # 1. 检查操作系统
    print("\n1. 操作系统检查")
    system = platform.system()
    release = platform.release()
    success = "Linux" in system or "kali" in platform.platform().lower()
    if print_check("操作系统", success, f"{system} {release}"):
        checks_passed += 1
    checks_total += 1
    
    # 2. 检查Python版本
    print("\n2. Python环境检查")
    python_version = sys.version.split()[0]
    success = sys.version_info >= (3, 8)
    if print_check("Python版本", success, f"版本: {python_version}"):
        checks_passed += 1
    checks_total += 1
    
    # 3. 检查安全工具
    print("\n3. 安全工具检查")
    
    tools_to_check = [
        ("sqlmap", "sqlmap --version", "SQL注入工具"),
        ("nmap", "nmap --version", "端口扫描工具"),
        ("python3", "python3 --version", "Python 3"),
        ("git", "git --version", "版本控制"),
    ]
    
    for tool_name, cmd, description in tools_to_check:
        success, stdout, stderr = run_command(f"which {tool_name}", check=False)
        if success:
            success, version_out, _ = run_command(cmd, check=False)
            version = version_out.split('\n')[0] if version_out else "已安装"
            if print_check(f"{tool_name} ({description})", True, version):
                checks_passed += 1
        else:
            print_check(f"{tool_name} ({description})", False, "未安装")
        checks_total += 1
    
    # 3.1 检查虚拟环境
    print("\n3.1 Python虚拟环境检查")
    venv_path = Path.cwd() / "venv"
    venv_exists = venv_path.exists()
    
    if venv_exists:
        python_path = venv_path / "bin" / "python"
        if python_path.exists():
            success, version_out, _ = run_command(f"{python_path} --version", check=False)
            version = version_out if version_out else "虚拟环境Python"
            if print_check("Python虚拟环境", True, f"已创建 ({version})"):
                checks_passed += 1
        else:
            print_check("Python虚拟环境", False, "存在但Python不可用")
    else:
        print_check("Python虚拟环境", False, "未创建 (Kali需要虚拟环境)")
    checks_total += 1
    
    # 3.2 检查pip在虚拟环境中
    if venv_exists:
        pip_path = venv_path / "bin" / "pip"
        if pip_path.exists():
            print_check("虚拟环境pip", True, "可用")
            checks_passed += 1
        else:
            print_check("虚拟环境pip", False, "不可用")
    else:
        print_check("虚拟环境pip", False, "虚拟环境不存在")
    checks_total += 1
    
    # 4. 检查项目结构
    print("\n4. 项目结构检查")
    required_dirs = ["src", "config", "scripts", "docs"]
    current_dir = Path.cwd()
    
    dir_checks = []
    for dir_name in required_dirs:
        dir_path = current_dir / dir_name
        exists = dir_path.exists()
        dir_checks.append((dir_name, exists))
        if print_check(f"目录: {dir_name}", exists):
            checks_passed += 1
        checks_total += 1
    
    # 5. 检查配置文件
    print("\n5. 配置文件检查")
    config_files = [
        ("config/development.yaml", "主配置文件"),
        (".env.example", "环境变量示例"),
        ("requirements.txt", "Python依赖"),
    ]
    
    for file_path, description in config_files:
        file = current_dir / file_path
        exists = file.exists()
        if print_check(f"文件: {description}", exists, str(file)):
            checks_passed += 1
        checks_total += 1
    
    # 6. 总结
    print("\n" + "=" * 60)
    print("验证结果总结")
    print("=" * 60)
    
    percentage = (checks_passed / checks_total) * 100
    print(f"通过检查: {checks_passed}/{checks_total} ({percentage:.1f}%)")
    
    if percentage >= 80:
        print("\n🎉 环境验证通过！可以开始项目部署。")
        print("\n下一步建议:")
        
        if venv_exists:
            print("1. 激活虚拟环境: source venv/bin/activate")
            print("2. 安装Python依赖: pip install -r requirements.txt")
        else:
            print("1. 创建虚拟环境: python3 -m venv venv")
            print("2. 激活虚拟环境: source venv/bin/activate")
            print("3. 安装Python依赖: pip install -r requirements.txt")
        
        print("4. 配置环境变量: cp .env.example .env")
        print("5. 运行配置验证: python scripts/validate_config.py")
        print("6. 测试MCP服务器: python scripts/test_mcp_server.py")
        
        # 提供快速设置脚本建议
        setup_script = Path.cwd() / "scripts" / "setup_kali_venv.sh"
        if setup_script.exists():
            print(f"\n💡 快速设置: chmod +x scripts/setup_kali_venv.sh && ./scripts/setup_kali_venv.sh")
            
    elif percentage >= 50:
        print("\n⚠️ 环境基本就绪，但需要安装一些工具。")
        print("\n需要安装的工具:")
        for tool_name, cmd, description in tools_to_check:
            success, _, _ = run_command(f"which {tool_name}", check=False)
            if not success:
                print(f"  - {tool_name}: {description}")
        
        # 虚拟环境建议
        if not venv_exists:
            print(f"  - python3-venv: 虚拟环境支持 (sudo apt install python3-venv)")
            
    else:
        print("\n❌ 环境不满足要求，请先安装必要工具。")
        print("\n建议运行设置脚本:")
        print("  chmod +x scripts/setup_kali_venv.sh")
        print("  ./scripts/setup_kali_venv.sh")
    
    print("\n" + "=" * 60)
    
    return 0 if percentage >= 80 else 1


if __name__ == "__main__":
    sys.exit(main())