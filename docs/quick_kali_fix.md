# Kali Linux Python环境快速修复指南

## 问题症状

在Kali Linux中运行 `pip3 install -r requirements.txt` 时出现错误：

```
error: externally-managed-environment
This environment is externally managed
```

## 快速解决方案

### 方法1：使用虚拟环境（推荐）

在Kali终端中执行以下命令：

```bash
# 1. 进入项目目录
cd ~/ctf-ai-system

# 2. 安装虚拟环境支持
sudo apt install python3-venv -y

# 3. 创建虚拟环境
python3 -m venv venv

# 4. 激活虚拟环境
source venv/bin/activate

# 5. 验证激活（命令行前应有(venv)）
(venv) $ which python
/home/kali/ctf-ai-system/venv/bin/python

# 6. 安装依赖
pip install -r requirements.txt
```

### 方法2：使用自动化脚本

```bash
# 1. 进入项目目录
cd ~/ctf-ai-system

# 2. 给予脚本执行权限
chmod +x scripts/setup_kali_venv.sh

# 3. 运行设置脚本
./scripts/setup_kali_venv.sh
```

脚本会自动完成所有设置。

### 方法3：强制安装（不推荐）

```bash
# 不推荐！可能破坏系统Python环境
pip install --break-system-packages -r requirements.txt
```

## 验证修复

修复后运行以下命令验证：

```bash
# 1. 验证虚拟环境
source venv/bin/activate
python --version
pip --version

# 2. 验证包安装
python -c "import fastapi; print('✅ FastAPI导入成功')"

# 3. 运行项目测试
python scripts/validate_config.py
python scripts/test_mcp_server.py
```

## 日常使用

### 激活虚拟环境
```bash
# 每次打开新终端时
cd ~/ctf-ai-system
source venv/bin/activate
```

### 创建快捷方式
```bash
# 添加到 ~/.bashrc
echo "alias ctfai='cd ~/ctf-ai-system && source venv/bin/activate'" >> ~/.bashrc
source ~/.bashrc

# 之后只需输入
ctfai
```

### 退出虚拟环境
```bash
deactivate
```

## 常见问题

### Q: 为什么Kali禁止直接安装Python包？
A: Kali Linux 2024+ 版本使用"外部管理的Python环境"来保护系统Python不被破坏。

### Q: 虚拟环境会占用多少空间？
A: 大约100-200MB，包含所有Python包。

### Q: 每次都要激活虚拟环境吗？
A: 是的，每个新终端会话都需要激活。建议使用别名或脚本简化。

### Q: 可以删除虚拟环境重新创建吗？
A: 可以：
```bash
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 下一步

环境修复后，继续项目部署：

1. **配置环境变量**
   ```bash
   cp .env.example .env
   nano .env  # 添加DeepSeek API密钥
   ```

2. **运行完整测试**
   ```bash
   python scripts/validate_config.py
   python scripts/test_mcp_server.py
   python scripts/demo_mcp_server.py
   ```

3. **开始开发**
   ```bash
   # 启动MCP服务器
   python scripts/start_mcp_server.py
   ```

## 获取帮助

如果仍有问题：

1. 查看详细文档：`docs/kali_python_fix.md`
2. 运行环境验证：`python scripts/verify_kali_environment.py`
3. 检查Kali版本：`cat /etc/os-release`

---

**修复时间**: 约5-10分钟  
**难度**: 简单  
**影响**: 仅影响当前项目，不改变系统Python环境