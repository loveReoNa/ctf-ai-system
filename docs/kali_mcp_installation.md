# Kali Linux MCP安装指南

## 📋 概述

本指南说明如何在Kali Linux上检查和安装Model Context Protocol (MCP)依赖，以运行CTF攻击模拟系统。

## 🔍 检查MCP是否已安装

### 方法1：使用Python检查

在Kali终端中运行以下命令：

```bash
# 检查Python中是否安装了mcp模块
python3 -c "import mcp; print('✅ MCP已安装，版本:', mcp.__version__ if hasattr(mcp, '__version__') else '未知')"
```

如果看到错误 `ModuleNotFoundError: No module named 'mcp'`，说明MCP未安装。

### 方法2：使用pip检查

```bash
# 检查pip是否安装了mcp包
pip3 list | grep mcp
```

或者：

```bash
pip3 show mcp
```

### 方法3：检查所有项目依赖

```bash
# 检查requirements.txt中的所有依赖
cd ~/ctf-ai-system
pip3 freeze | grep -E "(mcp|flask|openai|langchain)"
```

## 🚀 安装MCP依赖

### 步骤1：更新系统包

```bash
# 更新包列表
sudo apt update

# 升级已安装的包
sudo apt upgrade -y
```

### 步骤2：安装Python和pip（如果需要）

```bash
# 检查Python版本
python3 --version

# 如果Python未安装
sudo apt install python3 python3-pip python3-venv -y
```

### 步骤3：创建虚拟环境（推荐）

```bash
cd ~/ctf-ai-system

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 验证虚拟环境
which python3
which pip3
```

### 步骤4：安装项目依赖

```bash
# 确保在项目目录中
cd ~/ctf-ai-system

# 激活虚拟环境（如果尚未激活）
source venv/bin/activate

# 安装requirements.txt中的所有依赖
pip3 install -r requirements.txt
```

如果遇到权限问题，可以添加 `--user` 标志：

```bash
pip3 install --user -r requirements.txt
```

### 步骤5：验证安装

```bash
# 验证MCP安装
python3 -c "
try:
    import mcp
    print('✅ MCP安装成功')
    
    # 检查其他关键依赖
    import flask
    import openai
    import langchain
    import aiohttp
    
    print('✅ Flask安装成功')
    print('✅ OpenAI安装成功')
    print('✅ LangChain安装成功')
    print('✅ aiohttp安装成功')
    
    print('\n🎉 所有关键依赖安装成功！')
    
except ImportError as e:
    print(f'❌ 导入错误: {e}')
    print('请重新运行: pip3 install -r requirements.txt')
"
```

## 🔧 故障排除

### 问题1：pip安装失败

**症状**：
```
ERROR: Could not find a version that satisfies the requirement mcp>=0.1.0
ERROR: No matching distribution found for mcp>=0.1.0
```

**解决方案**：
MCP包可能不在PyPI上，或者名称不同。尝试：

```bash
# 尝试从GitHub安装
pip3 install git+https://github.com/modelcontextprotocol/python-sdk.git

# 或者安装特定版本
pip3 install mcp==0.1.0
```

如果仍然失败，检查requirements.txt中的MCP行：

```bash
# 临时注释掉mcp行，先安装其他依赖
sed -i 's/^mcp/# mcp/' requirements.txt
pip3 install -r requirements.txt

# 然后尝试从源码安装MCP
git clone https://github.com/modelcontextprotocol/python-sdk.git
cd python-sdk
pip3 install -e .
cd ..
```

### 问题2：权限被拒绝

**症状**：
```
PermissionError: [Errno 13] Permission denied
```

**解决方案**：
使用虚拟环境或添加 `--user` 标志：

```bash
# 方法1：使用虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt

# 方法2：使用--user标志
pip3 install --user -r requirements.txt

# 方法3：使用sudo（不推荐）
sudo pip3 install -r requirements.txt
```

### 问题3：依赖冲突

**症状**：
```
ERROR: Cannot install package due to conflicting dependencies
```

**解决方案**：
尝试安装特定版本：

```bash
# 创建新的requirements文件
cat > requirements_kali.txt << 'EOF'
# 核心依赖
flask>=2.3.0
flask-cors>=4.0.0

# AI/LLM
openai>=1.0.0
langchain>=0.0.300
langchain-openai>=0.0.2

# MCP（从GitHub安装）
git+https://github.com/modelcontextprotocol/python-sdk.git

# 网络请求
requests>=2.31.0
aiohttp>=3.8.0

# 配置管理
pyyaml>=6.0
python-dotenv>=1.0.0

# 其他
colorama>=0.4.0
rich>=13.0.0
EOF

# 安装
pip3 install -r requirements_kali.txt
```

## 📊 完整安装脚本

创建一个完整的安装脚本：

```bash
cat > install_kali_deps.sh << 'EOF'
#!/bin/bash
# Kali Linux依赖安装脚本

set -e

echo "🚀 Kali Linux CTF系统依赖安装"
echo "================================"

# 检查Python
echo "🔍 检查Python环境..."
python3 --version || {
    echo "❌ Python3未安装，正在安装..."
    sudo apt update
    sudo apt install python3 python3-pip python3-venv -y
}

# 创建虚拟环境
echo "🔧 创建虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ 虚拟环境创建成功"
else
    echo "✅ 虚拟环境已存在"
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 升级pip
echo "📦 升级pip..."
pip3 install --upgrade pip

# 安装依赖
echo "📦 安装项目依赖..."
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
else
    echo "❌ requirements.txt未找到"
    exit 1
fi

# 验证安装
echo "✅ 验证安装..."
python3 -c "
import sys
try:
    import mcp
    print('✅ MCP安装成功')
    
    import flask
    print('✅ Flask安装成功')
    
    import openai
    print('✅ OpenAI安装成功')
    
    import langchain
    print('✅ LangChain安装成功')
    
    print('\n🎉 所有依赖安装成功！')
    
except ImportError as e:
    print(f'❌ 导入错误: {e}')
    sys.exit(1)
"

echo ""
echo "📋 安装完成！"
echo "================================"
echo "下一步操作:"
echo "1. 激活虚拟环境: source venv/bin/activate"
echo "2. 运行修复脚本: python3 scripts/kali_fix_tool_chain.py"
echo "3. 测试系统: python3 solve_ctf.py --demo"
echo "================================"
EOF

# 设置执行权限
chmod +x install_kali_deps.sh

# 运行脚本
./install_kali_deps.sh
```

## 🧪 测试MCP功能

安装完成后，测试MCP功能：

```bash
# 激活虚拟环境
source venv/bin/activate

# 测试MCP导入
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from src.mcp_server.server import CTFMCPServer
    print('✅ MCP服务器导入成功')
    
    # 测试工具包装器
    from src.mcp_server.tools.sqlmap_wrapper import SQLMapWrapper
    from src.mcp_server.tools.nmap_wrapper import NmapWrapper
    print('✅ 工具包装器导入成功')
    
    print('\n🎉 MCP功能测试通过！')
    
except Exception as e:
    print(f'❌ 测试失败: {e}')
    import traceback
    traceback.print_exc()
"
```

## 📈 性能优化

### 使用清华PyPI镜像（中国用户）

```bash
# 临时使用镜像
pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 永久配置镜像
pip3 config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

### 缓存依赖

```bash
# 使用缓存目录
pip3 install -r requirements.txt --cache-dir ~/.cache/pip

# 预下载所有依赖
pip3 download -r requirements.txt -d ./deps_cache
pip3 install --no-index --find-links=./deps_cache -r requirements.txt
```

## 🔍 高级检查

### 检查系统工具

```bash
# 检查安全工具
echo "🔧 检查安全工具..."
which sqlmap || echo "❌ sqlmap未安装，运行: sudo apt install sqlmap"
which nmap || echo "❌ nmap未安装，运行: sudo apt install nmap"
which nikto || echo "❌ nikto未安装，运行: sudo apt install nikto"
which dirb || echo "❌ dirb未安装，运行: sudo apt install dirb"
```

### 检查配置文件

```bash
# 检查环境变量
if [ -f ".env" ]; then
    echo "✅ .env文件存在"
    grep -E "DEEPSEEK_API_KEY|SECRET_KEY" .env || echo "⚠️  缺少API密钥配置"
else
    echo "❌ .env文件不存在，复制示例文件: cp .env.example .env"
fi

# 检查配置文件
if [ -f "config/development.yaml" ]; then
    echo "✅ 配置文件存在"
else
    echo "❌ 配置文件不存在"
fi
```

## 📞 支持与帮助

如果遇到问题：

1. **检查日志**：查看 `logs/` 目录中的日志文件
2. **验证Python路径**：确保虚拟环境已激活
3. **检查依赖版本**：运行 `pip3 list` 查看已安装的包
4. **查看错误信息**：仔细阅读错误信息，搜索解决方案
5. **联系团队**：分享错误信息和系统信息

### 常见错误解决方案

**错误**: `ModuleNotFoundError: No module named 'mcp'`
**解决**: 从GitHub安装MCP SDK：`pip3 install git+https://github.com/modelcontextprotocol/python-sdk.git`

**错误**: `ImportError: cannot import name 'StdioServerParameters' from 'mcp'`
**解决**: MCP版本不兼容，尝试：`pip3 install mcp==0.1.0`

**错误**: `Permission denied when installing packages`
**解决**: 使用虚拟环境或添加 `--user` 标志

---

**最后更新**: 2026年3月5日  
**文档版本**: 1.0.0  
**适用环境**: Kali Linux 2024.x  
**验证状态**: ✅ 已验证