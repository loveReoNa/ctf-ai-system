# Kali Linux 环境检查清单

## 安装后验证步骤

### ✅ 基础系统检查
- [ ] Kali Linux 已安装并更新
  ```bash
  sudo apt update && sudo apt upgrade -y
  ```
- [ ] 系统时间正确
  ```bash
  date
  ```
- [ ] 网络连接正常
  ```bash
  ping -c 3 8.8.8.8
  ```

### ✅ 开发工具检查
- [ ] Python 3.8+ 已安装
  ```bash
  python3 --version
  ```
- [ ] pip 已安装
  ```bash
  pip3 --version
  ```
- [ ] Git 已安装
  ```bash
  git --version
  ```

### ✅ 安全工具检查
- [ ] sqlmap 已安装
  ```bash
  which sqlmap
  sqlmap --version
  ```
- [ ] nmap 已安装
  ```bash
  which nmap
  nmap --version
  ```
- [ ] 其他工具（可选）
  ```bash
  which burpsuite    # Burp Suite Community
  which zaproxy      # OWASP ZAP
  ```

### ✅ 项目环境检查
- [ ] 项目文件已传输到Kali
  ```bash
  ls -la .ctfagent/
  ```
- [ ] 运行环境验证脚本
  ```bash
  cd .ctfagent
  python3 scripts/verify_kali_environment.py
  ```
- [ ] 安装Python依赖
  ```bash
  pip3 install -r requirements.txt
  ```
- [ ] 配置环境变量
  ```bash
  cp .env.example .env
  # 编辑 .env 文件，添加DeepSeek API密钥
  ```

### ✅ 配置验证
- [ ] 验证配置文件
  ```bash
  python3 scripts/validate_config.py
  ```
- [ ] 检查工具路径配置
  ```bash
  grep -A5 "tools:" config/development.yaml
  ```

### ✅ 功能测试
- [ ] 测试MCP服务器
  ```bash
  python3 scripts/test_mcp_server.py
  ```
- [ ] 测试SQLMap连接
  ```bash
  python3 -c "
  import asyncio
  from src.mcp_server.tools.sqlmap_wrapper import SQLMapWrapper
  
  async def test():
      wrapper = SQLMapWrapper()
      connected = await wrapper.test_connection()
      print(f'SQLMap连接: {\"✅ 成功\" if connected else \"❌ 失败\"}')
  
  asyncio.run(test())
  "
  ```
- [ ] 运行演示
  ```bash
  python3 scripts/demo_mcp_server.py
  ```

### ✅ 网络和服务检查
- [ ] SSH服务运行（用于文件传输）
  ```bash
  sudo systemctl status ssh
  ```
- [ ] 防火墙配置（如果需要）
  ```bash
  sudo ufw status
  ```
- [ ] 虚拟机网络设置
  - [ ] NAT模式（推荐开发）
  - [ ] 桥接模式（如果需要外部访问）

## 常见问题解决

### ❌ 问题：sqlmap命令未找到
**解决方案**：
```bash
# 检查是否安装
apt list --installed | grep sqlmap

# 如果未安装
sudo apt install sqlmap -y
```

### ❌ 问题：Python包安装失败
**解决方案**：
```bash
# 更新pip
pip3 install --upgrade pip

# 使用国内镜像
pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### ❌ 问题：无法连接到DeepSeek API
**解决方案**：
```bash
# 测试网络连接
curl -I https://api.deepseek.com

# 检查API密钥
echo $DEEPSEEK_API_KEY

# 临时设置
export DEEPSEEK_API_KEY="your_key_here"
```

### ❌ 问题：权限不足
**解决方案**：
```bash
# 添加执行权限
chmod +x scripts/*.py
chmod +x src/mcp_server/server.py

# 如果使用非root用户
sudo chmod -R 755 .ctfagent/
```

### ❌ 问题：虚拟机网络不通
**解决方案**：
1. 检查VMware网络设置
2. 确保Kali获取到IP地址
   ```bash
   ip addr show
   ```
3. 测试与宿主机的连接
   ```bash
   ping <windows-ip>
   ```

## 快速验证命令

一键验证脚本：
```bash
#!/bin/bash
echo "=== Kali环境快速验证 ==="
echo "1. 系统信息: $(uname -a)"
echo "2. Python版本: $(python3 --version)"
echo "3. sqlmap路径: $(which sqlmap)"
echo "4. nmap路径: $(which nmap)"
echo "5. 项目目录: $(pwd)"
echo "6. 依赖检查: $(pip3 list | grep -E 'fastapi|langchain|mcp' | wc -l) 个包已安装"
```

## 下一步行动

环境验证通过后，可以：

### 1. 开始开发AI代理
```bash
# 创建AI代理框架
# 文件: src/agents/react_agent.py
```

### 2. 测试完整工作流程
```bash
# 创建测试CTF挑战
# 运行端到端测试
```

### 3. 配置持续集成
```bash
# 设置Git hooks
# 配置自动化测试
```

## 维护建议

### 定期更新
```bash
# 每周更新系统
sudo apt update && sudo apt upgrade -y

# 更新Python包
pip3 install --upgrade -r requirements.txt
```

### 备份配置
```bash
# 备份重要配置文件
cp .env .env.backup
cp config/development.yaml config/development.yaml.backup
```

### 监控日志
```bash
# 查看应用日志
tail -f logs/ctf_ai.log

# 查看系统资源
htop
```

## 支持资源

- [Kali Linux官方文档](https://www.kali.org/docs/)
- [项目文档](docs/)
- [MCP服务器使用指南](docs/mcp_server_usage.md)
- [Kali部署指南](docs/kali_deployment.md)

---

**最后更新**: 2026-02-25  
**验证状态**: ✅ 通过基础检查