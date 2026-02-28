# Kali Linux 测试指南

## 📋 测试前准备

### 1. 传输项目到Kali Linux
如果你还没有将项目传输到Kali，可以使用以下方法：

**方法一：使用传输脚本（在Windows中运行）**
```bash
# 编辑 scripts/transfer_to_kali.bat 中的Kali IP地址
# 然后运行：
scripts/transfer_to_kali.bat
```

**方法二：手动传输**
```bash
# 在Windows PowerShell中
scp -r d:\.ctfagent kali@<kali-ip>:/home/kali/
```

**方法三：使用Git（如果项目在Git仓库中）**
```bash
# 在Kali中
git clone <repository-url>
cd .ctfagent
```

### 2. 环境设置
在Kali Linux中，运行以下命令：

```bash
# 1. 进入项目目录
cd ~/.ctfagent

# 2. 运行Kali环境设置脚本
chmod +x scripts/setup_kali_venv.sh
./scripts/setup_kali_venv.sh

# 3. 激活虚拟环境
source venv/bin/activate
# 或使用快速脚本
./activate_project.sh
```

### 3. 配置环境变量
```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑.env文件，添加DeepSeek API密钥
nano .env
# 或使用vim
vim .env
```

在`.env`文件中，确保有以下配置：
```
DEEPSEEK_API_KEY=your_actual_api_key_here
AI_PROVIDER=deepseek
AI_MODEL=deepseek-chat
```

## 🧪 运行测试套件

### 测试1: 环境验证
```bash
# 验证Kali环境是否准备就绪
python3 scripts/verify_kali_environment.py
```

预期输出：应该显示所有检查通过（绿色✅）。

### 测试2: 配置验证
```bash
# 验证配置文件和环境变量
python3 scripts/validate_config.py
```

预期输出：应该显示"✅ 配置文件加载成功"和"✅ 环境变量文件加载成功"。

### 测试3: Kali准备测试
```bash
# 运行全面的Kali准备测试
python3 scripts/test_kali_preparedness.py
```

预期输出：应该显示所有4个测试通过（平台检测、配置文件、Kali特定检查、MCP服务器初始化）。

### 测试4: MCP服务器测试
```bash
# 测试MCP服务器功能
python3 scripts/test_mcp_server.py
```

预期输出：应该显示MCP服务器初始化成功，工具注册成功。

### 测试5: AI代理测试
```bash
# 测试ReAct AI代理
python3 scripts/test_react_agent.py
```

预期输出：应该显示AI代理初始化成功，挑战分析测试通过。

### 测试6: 完整集成测试
```bash
# 运行完整的集成测试
python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')
from scripts.test_react_agent import test_react_agent_integration

async def run_all_tests():
    print('=== 完整集成测试 ===')
    success = await test_react_agent_integration()
    if success:
        print('✅ 所有集成测试通过')
    else:
        print('❌ 集成测试失败')
    return success

asyncio.run(run_all_tests())
"
```

## 🔧 安全工具测试

### 验证安全工具安装
在Kali中，安全工具应该已经预装。验证：

```bash
# 检查工具是否安装
which sqlmap    # 应该显示 /usr/bin/sqlmap
which nmap      # 应该显示 /usr/bin/nmap

# 检查工具版本
sqlmap --version
nmap --version
```

### 测试工具连接
```bash
# 测试SQLMap包装器
python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')
from src.mcp_server.tools.sqlmap_wrapper import SQLMapWrapper

async def test():
    wrapper = SQLMapWrapper()
    connected = await wrapper.test_connection()
    print(f'SQLMap连接测试: {\"✅ 成功\" if connected else \"❌ 失败\"}')

asyncio.run(test())
"
```

## 🚀 实际攻击模拟测试

### 测试场景1: CTF挑战分析
```bash
# 运行CTF挑战分析测试
python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')
from src.agents.react_agent import ReActAgent
from src.utils.deepseek_client import DeepSeekClient

async def test_challenge_analysis():
    print('=== CTF挑战分析测试 ===')
    
    # 初始化客户端
    client = DeepSeekClient()
    
    # 测试挑战
    challenge = {
        'name': 'SQL注入挑战',
        'description': '目标网站: http://testphp.vulnweb.com，存在SQL注入漏洞',
        'url': 'http://testphp.vulnweb.com/artists.php?artist=1'
    }
    
    # 分析挑战
    analysis = await client.analyze_ctf_challenge(challenge)
    print(f'挑战分析结果: {analysis}')
    
    return analysis is not None

asyncio.run(test_challenge_analysis())
"
```

### 测试场景2: 攻击链规划
```bash
# 运行攻击链规划测试
python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')
from src.agents.react_agent import ReActAgent

async def test_attack_planning():
    print('=== 攻击链规划测试 ===')
    
    # 初始化代理
    agent = ReActAgent()
    
    # 测试攻击规划
    challenge_info = {
        'target': 'http://testphp.vulnweb.com',
        'vulnerability': 'SQL注入',
        'description': '艺术家页面存在SQL注入漏洞'
    }
    
    plan = await agent.plan_attack(challenge_info)
    print(f'攻击计划: {plan}')
    
    return plan is not None and len(plan.get('steps', [])) > 0

asyncio.run(test_attack_planning())
"
```

## 📊 测试结果收集

### 创建测试报告
```bash
# 运行所有测试并生成报告
python3 scripts/run_all_tests.py --report
```

如果`run_all_tests.py`不存在，可以使用以下脚本：

```bash
cat > run_kali_tests.sh << 'EOF'
#!/bin/bash
# Kali Linux完整测试脚本

echo "========================================"
echo "  Kali Linux完整测试套件"
echo "========================================"
echo "开始时间: $(date)"
echo ""

# 激活虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ 虚拟环境已激活"
else
    echo "❌ 虚拟环境不存在"
    exit 1
fi

# 运行测试
echo ""
echo "1. 环境验证测试..."
python3 scripts/verify_kali_environment.py
ENV_RESULT=$?

echo ""
echo "2. 配置验证测试..."
python3 scripts/validate_config.py
CONFIG_RESULT=$?

echo ""
echo "3. Kali准备测试..."
python3 scripts/test_kali_preparedness.py
KALI_RESULT=$?

echo ""
echo "4. MCP服务器测试..."
python3 scripts/test_mcp_server.py
MCP_RESULT=$?

echo ""
echo "5. AI代理测试..."
python3 scripts/test_react_agent.py
AI_RESULT=$?

# 总结
echo ""
echo "========================================"
echo "  测试结果总结"
echo "========================================"
echo "结束时间: $(date)"
echo ""
echo "测试结果:"
echo "  环境验证: $(if [ $ENV_RESULT -eq 0 ]; then echo '✅ 通过'; else echo '❌ 失败'; fi)"
echo "  配置验证: $(if [ $CONFIG_RESULT -eq 0 ]; then echo '✅ 通过'; else echo '❌ 失败'; fi)"
echo "  Kali准备: $(if [ $KALI_RESULT -eq 0 ]; then echo '✅ 通过'; else echo '❌ 失败'; fi)"
echo "  MCP服务器: $(if [ $MCP_RESULT -eq 0 ]; then echo '✅ 通过'; else echo '❌ 失败'; fi)"
echo "  AI代理: $(if [ $AI_RESULT -eq 0 ]; then echo '✅ 通过'; else echo '❌ 失败'; fi)"
echo ""
echo "总体结果: $(if [ $ENV_RESULT -eq 0 ] && [ $CONFIG_RESULT -eq 0 ] && [ $KALI_RESULT -eq 0 ] && [ $MCP_RESULT -eq 0 ] && [ $AI_RESULT -eq 0 ]; then echo '🎉 所有测试通过'; else echo '⚠️  部分测试失败'; fi)"
EOF

chmod +x run_kali_tests.sh
./run_kali_tests.sh
```

## 🐛 常见问题解决

### 问题1: Python包导入错误
```bash
# 重新安装依赖
pip install --upgrade -r requirements.txt

# 如果还有问题，尝试安装特定版本
pip install "mcp>=0.1.0" "openai>=1.0.0"
```

### 问题2: 虚拟环境激活失败
```bash
# 删除并重新创建虚拟环境
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 问题3: DeepSeek API连接失败
```bash
# 检查API密钥
echo $DEEPSEEK_API_KEY

# 测试API连接
python3 -c "
import os
from src.utils.deepseek_client import DeepSeekClient
import asyncio

async def test():
    client = DeepSeekClient()
    connected = await client.test_connection()
    print(f'API连接: {\"✅ 成功\" if connected else \"❌ 失败\"}')

asyncio.run(test())
"
```

### 问题4: 安全工具路径问题
```bash
# 检查工具路径配置
python3 -c "
from src.utils.config_manager import config
print('SQLMap路径:', config.get('tools.sqlmap.path'))
print('Nmap路径:', config.get('tools.nmap.path'))
"

# 如果路径不正确，更新配置文件
# 编辑 config/development.yaml
```

## 📝 测试结果反馈

测试完成后，请将以下信息反馈给我：

1. **测试环境信息**
   - Kali Linux版本: `cat /etc/os-release`
   - Python版本: `python3 --version`
   - 虚拟环境状态: `which python`

2. **测试结果**
   - 每个测试的通过/失败状态
   - 任何错误信息或警告
   - 测试截图或日志

3. **遇到的问题**
   - 描述遇到的问题
   - 错误消息全文
   - 已经尝试的解决方法

4. **建议和改进**
   - 测试过程中发现的任何问题
   - 功能改进建议
   - 用户体验反馈

## 📞 支持

如果在测试过程中遇到问题，可以：
1. 查看详细日志: `tail -f logs/ctf_ai.log`
2. 检查配置文件: `cat config/development.yaml`
3. 运行调试模式: `python3 scripts/test_mcp_server.py --debug`
4. 联系技术支持

---

**测试完成标准**: 所有6个核心测试通过，安全工具验证成功，AI代理功能正常。

**预计测试时间**: 30-60分钟

**测试负责人**: [你的名字]

**测试日期**: $(date)