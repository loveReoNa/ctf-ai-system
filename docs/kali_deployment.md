# Kali Linux 部署指南

## 概述

本指南详细说明如何在Kali Linux环境中部署和运行CTF AI攻击模拟系统。

## 环境要求

### 硬件要求
- CPU: 4核心或以上
- 内存: 8GB或以上
- 硬盘: 50GB可用空间
- 网络: 可访问互联网

### 软件要求
- Kali Linux 2023.x 或更高版本
- Python 3.8+
- Git
- 安全工具: sqlmap, nmap (Kali默认已安装)

## 快速部署

### 步骤1: 获取项目代码

#### 选项A: 从Git克隆（推荐）
```bash
# 克隆项目
git clone <repository-url>
cd .ctfagent

# 或如果已从Windows复制，直接进入项目目录
cd /path/to/.ctfagent
```

#### 选项B: 重新创建项目
如果项目文件已通过共享文件夹或SCP复制到Kali：
```bash
# 进入项目目录
cd /path/to/project
```

### 步骤2: 环境验证

运行环境验证脚本：
```bash
# 确保有执行权限
chmod +x scripts/verify_kali_environment.py

# 运行验证
python3 scripts/verify_kali_environment.py
```

如果验证通过（80%以上），继续下一步。否则，根据脚本提示安装缺失的工具。

### 步骤3: 安装Python依赖

```bash
# 安装项目依赖
pip3 install -r requirements.txt

# 如果需要虚拟环境（可选）
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

### 步骤4: 配置环境

```bash
# 复制环境变量文件
cp .env.example .env

# 编辑配置文件（如果需要）
nano .env
```

在 `.env` 文件中设置以下关键变量：
```bash
# DeepSeek API配置
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com

# 项目配置
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### 步骤5: 验证配置

```bash
# 运行配置验证
python3 scripts/validate_config.py
```

如果显示所有检查通过，配置完成。

## 工具路径配置

Kali Linux中安全工具的默认路径：

### 自动检测配置
编辑 `config/development.yaml`，更新工具路径部分：

```yaml
tools:
  sqlmap:
    path: "/usr/bin/sqlmap"  # Kali默认路径
    windows_path: "C:/Program Files/sqlmap/sqlmap.py"  # 保留Windows路径
  nmap:
    path: "/usr/bin/nmap"    # Kali默认路径
    windows_path: "C:/Program Files/Nmap/nmap.exe"     # 保留Windows路径
```

或者使用环境变量自动检测：
```bash
# 在Kali中，工具路径通常已在PATH中
# 系统会自动找到sqlmap和nmap
```

## 运行测试

### 1. 测试MCP服务器框架

```bash
# 运行MCP服务器测试
python3 scripts/test_mcp_server.py
```

预期输出：
- ✅ 配置文件加载成功
- ✅ 工具注册成功
- ⚠ SQLMap连接测试（应该成功，因为Kali已安装）

### 2. 测试SQLMap包装器

```bash
# 直接测试SQLMap包装器
python3 -c "
import asyncio
from src.mcp_server.tools.sqlmap_wrapper import SQLMapWrapper

async def test():
    wrapper = SQLMapWrapper()
    connected = await wrapper.test_connection()
    print(f'SQLMap连接测试: {\"成功\" if connected else \"失败\"}')

asyncio.run(test())
"
```

### 3. 运行演示

```bash
# 运行完整演示
python3 scripts/demo_mcp_server.py
```

## 启动MCP服务器

### 开发模式启动

```bash
# 启动MCP服务器（开发模式）
python3 scripts/start_mcp_server.py
```

### 直接启动

```bash
# 直接运行MCP服务器
python3 src/mcp_server/server.py --server
```

### 后台运行

```bash
# 使用nohup在后台运行
nohup python3 scripts/start_mcp_server.py > mcp_server.log 2>&1 &

# 查看日志
tail -f mcp_server.log
```

## Kali特定优化

### 1. 性能优化

```bash
# 增加文件描述符限制（用于处理大量连接）
echo "* soft nofile 65535" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65535" | sudo tee -a /etc/security/limits.conf

# 重新登录生效
```

### 2. 安全加固

```bash
# 创建专用用户运行服务
sudo useradd -m -s /bin/bash ctfai
sudo passwd ctfai

# 将项目文件所有权转移给新用户
sudo chown -R ctfai:ctfai /path/to/.ctfagent
```

### 3. 服务化部署

创建systemd服务文件 `/etc/systemd/system/ctfai-mcp.service`：

```ini
[Unit]
Description=CTF AI MCP Server
After=network.target

[Service]
Type=simple
User=ctfai
WorkingDirectory=/path/to/.ctfagent
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 scripts/start_mcp_server.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启用服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable ctfai-mcp
sudo systemctl start ctfai-mcp
sudo systemctl status ctfai-mcp
```

## 故障排除

### 常见问题1: Python包安装失败

```bash
# 更新pip
pip3 install --upgrade pip

# 使用国内镜像（如需要）
pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 常见问题2: 工具路径错误

```bash
# 验证工具路径
which sqlmap
which nmap

# 如果不在PATH中，手动指定路径
export SQLMAP_PATH=/usr/bin/sqlmap
export NMAP_PATH=/usr/bin/nmap
```

### 常见问题3: 权限问题

```bash
# 确保有执行权限
chmod +x scripts/*.py
chmod +x src/mcp_server/server.py

# 如果使用非root用户，确保有访问权限
sudo chmod -R 755 /path/to/.ctfagent
```

### 常见问题4: DeepSeek API连接失败

```bash
# 测试网络连接
curl -I https://api.deepseek.com

# 验证API密钥
echo $DEEPSEEK_API_KEY

# 临时设置环境变量
export DEEPSEEK_API_KEY="your_key_here"
```

## 开发工作流程

### 双环境开发建议

```
Windows (开发)                    Kali (测试)
-----------                    -----------
1. 编写代码                     1. 拉取最新代码
2. 本地测试                     2. 运行集成测试  
3. Git提交                      3. 验证工具功能
4. 推送到仓库                   4. 反馈问题
```

### 文件同步方法

#### 方法1: Git仓库
```bash
# Kali中拉取更新
cd /path/to/.ctfagent
git pull origin main
```

#### 方法2: 共享文件夹
- 在VMware中设置共享文件夹
- 将项目放在共享目录中
- Kali中访问 `/mnt/hgfs/共享文件夹名`

#### 方法3: SCP传输
```bash
# 从Windows复制到Kali
scp -r /path/to/.ctfagent user@kali-ip:/home/user/
```

## 下一步开发

环境部署完成后，可以开始：

### 1. AI代理开发
```bash
# 创建AI代理框架
# 文件: src/agents/react_agent.py
```

### 2. Web界面开发
```bash
# 创建Flask/FastAPI应用
# 文件: src/web_ui/app.py
```

### 3. 完整系统测试
```bash
# 运行端到端测试
python3 tests/test_full_system.py
```

## 维护和监控

### 日志查看
```bash
# 查看应用日志
tail -f logs/ctf_ai.log

# 查看系统日志
sudo journalctl -u ctfai-mcp -f
```

### 性能监控
```bash
# 查看进程状态
ps aux | grep python

# 查看资源使用
top -p $(pgrep -f "python.*mcp")
```

## 安全注意事项

1. **API密钥保护**: 不要将 `.env` 文件提交到Git
2. **最小权限原则**: 使用非root用户运行服务
3. **网络隔离**: 测试时使用隔离的网络环境
4. **日志管理**: 定期清理敏感日志信息

## 支持与帮助

如果遇到问题：

1. 查看日志文件: `logs/ctf_ai.log`
2. 运行诊断: `python3 scripts/verify_kali_environment.py`
3. 检查配置: `python3 scripts/validate_config.py`
4. 查阅文档: `docs/` 目录

---

**最后更新**: 2026-02-25  
**适用版本**: Kali Linux 2023.x+