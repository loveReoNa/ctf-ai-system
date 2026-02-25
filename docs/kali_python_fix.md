# Kali Linux Python环境问题解决方案

## 问题描述

Kali Linux 2024+ 版本默认使用"外部管理的Python环境"，禁止直接使用`pip install`安装系统级Python包。错误信息如下：

```
error: externally-managed-environment
This environment is externally managed
```

## 解决方案

### 方案1：使用虚拟环境（推荐）

#### 快速解决步骤

```bash
# 1. 安装虚拟环境支持
sudo apt install python3-venv -y

# 2. 进入项目目录
cd ~/ctf-ai-system

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

#### 自动化脚本

使用提供的设置脚本：
```bash
# 给予执行权限
chmod +x scripts/setup_kali_venv.sh

# 运行设置脚本
./scripts/setup_kali_venv.sh
```

### 方案2：使用pipx（适用于应用程序）

```bash
# 安装pipx
sudo apt install pipx -y
pipx ensurepath

# 使用pipx安装（适用于独立应用）
# 但我们的项目需要虚拟环境，不推荐此方案
```

### 方案3：强制覆盖系统保护（不推荐）

```bash
# 不推荐！可能破坏系统Python环境
pip install --break-system-packages -r requirements.txt
```

## 详细步骤

### 步骤1：设置虚拟环境

```bash
# 进入项目目录
cd ~/ctf-ai-system

# 运行设置脚本
./scripts/setup_kali_venv.sh
```

脚本会自动：
1. 安装必要的系统包
2. 创建虚拟环境
3. 激活虚拟环境
4. 安装所有依赖
5. 配置环境变量
6. 创建快速激活脚本

### 步骤2：验证安装

```bash
# 激活虚拟环境
source venv/bin/activate

# 验证Python包
python -c "
import fastapi
print('✅ FastAPI导入成功')

from src.utils.logger import logger
print('✅ 项目模块导入成功')

from src.mcp_server.tools.sqlmap_wrapper import SQLMapWrapper
print('✅ SQLMap包装器导入成功')
"
```

### 步骤3：运行项目

```bash
# 确保虚拟环境已激活
source venv/bin/activate

# 验证配置
python scripts/validate_config.py

# 测试MCP服务器
python scripts/test_mcp_server.py

# 运行演示
python scripts/demo_mcp_server.py
```

## 虚拟环境管理

### 激活虚拟环境

```bash
# 方法1：手动激活
source venv/bin/activate

# 方法2：使用快速脚本
./activate_project.sh

# 方法3：添加到shell配置（可选）
echo "alias ctfai='cd ~/ctf-ai-system && source venv/bin/activate'" >> ~/.bashrc
source ~/.bashrc
# 之后只需输入: ctfai
```

### 退出虚拟环境

```bash
deactivate
```

### 更新依赖

```bash
# 激活虚拟环境
source venv/bin/activate

# 更新requirements.txt中的包
pip install --upgrade -r requirements.txt

# 添加新包
pip install 包名
pip freeze > requirements.txt  # 更新requirements.txt
```

### 重新创建虚拟环境

```bash
# 删除旧环境
rm -rf venv

# 重新创建
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 项目脚本适配

所有项目脚本现在应该在虚拟环境中运行。已更新的脚本：

### 1. 验证脚本
```bash
#!/bin/bash
# scripts/verify_kali_environment.py 已适配虚拟环境
```

### 2. 启动脚本
```bash
#!/bin/bash
# scripts/start_mcp_server.py 现在检查虚拟环境
```

### 3. 测试脚本
```bash
#!/bin/bash
# scripts/test_mcp_server.py 自动激活虚拟环境
```

## 常见问题

### Q1：每次打开终端都要重新激活虚拟环境吗？
**A**：是的，每次新开终端都需要激活。建议：
- 使用`./activate_project.sh`快速激活
- 或创建shell别名

### Q2：虚拟环境会占用多少空间？
**A**：大约100-200MB，包含所有Python包。

### Q3：可以共享虚拟环境吗？
**A**：不推荐。虚拟环境包含绝对路径，最好在每个开发环境中单独创建。

### Q4：如何知道虚拟环境是否激活？
**A**：命令行前会有`(venv)`提示符：
```
(venv) kali@kali:~/ctf-ai-system$
```

### Q5：安装包时仍然报错？
**A**：确保虚拟环境已激活：
```bash
# 检查
echo $VIRTUAL_ENV
# 应该有输出，如: /home/kali/ctf-ai-system/venv
```

## 开发工作流

### 标准工作流程
```bash
# 1. 打开终端
# 2. 进入项目目录
cd ~/ctf-ai-system

# 3. 激活虚拟环境
source venv/bin/activate

# 4. 开发/运行代码
python your_script.py

# 5. 退出虚拟环境（可选）
deactivate
```

### 快速开发脚本

创建`dev.sh`：
```bash
#!/bin/bash
cd ~/ctf-ai-system
source venv/bin/activate
exec "$@"
```

使用：
```bash
./dev.sh python scripts/test_mcp_server.py
```

## 与IDE集成

### VS Code
1. 打开项目文件夹
2. 选择Python解释器：`Ctrl+Shift+P` → "Python: Select Interpreter"
3. 选择：`./venv/bin/python`

### PyCharm
1. 打开项目
2. File → Settings → Project → Python Interpreter
3. 添加虚拟环境路径：`./venv/bin/python`

## 备份和恢复

### 备份虚拟环境配置
```bash
# 导出已安装包列表
pip freeze > requirements.frozen.txt

# 备份虚拟环境（不推荐直接复制）
# 最好备份requirements.txt和项目代码
```

### 恢复虚拟环境
```bash
# 在新环境中
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.frozen.txt
```

## 性能优化

### 使用pip缓存
```bash
# 创建pip缓存目录
mkdir -p ~/.cache/pip

# 使用国内镜像加速
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

### 清理虚拟环境
```bash
# 清理缓存
pip cache purge

# 删除不必要的包
pip autoremove
```

## 总结

Kali Linux的Python外部管理环境是为了系统稳定性设计的。对于开发项目，**使用虚拟环境是最佳实践**。

**关键命令总结**：
```bash
# 初始设置
./scripts/setup_kali_venv.sh

# 日常使用
source venv/bin/activate          # 激活
python scripts/test_mcp_server.py # 运行
deactivate                        # 退出
```

现在您可以继续在Kali中部署和开发CTF AI攻击模拟系统了！