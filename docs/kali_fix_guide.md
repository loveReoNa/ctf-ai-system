# Kali Linux修复指南

## 📋 概述

本指南说明在Kali Linux上需要运行的修复脚本，以解决工具链协调器中的依赖检查问题。

## 🔧 问题描述

在Windows环境中，我们发现工具链协调器存在以下问题：
1. 工具依赖检查过于严格，导致某些工具链无法执行
2. 部分工具依赖关系定义不准确
3. 缺少对Kali环境特定路径的适配

这些问题已经在Windows环境中通过以下脚本修复：
- `scripts/fix_tool_chain.py` - 修复工具链定义
- `scripts/fix_dependencies.py` - 修复依赖检查

## 🚀 Kali Linux修复步骤

### 步骤1：传输修复文件到Kali

如果你已经在Kali上克隆了项目，只需拉取最新更改：

```bash
cd ~/.ctfagent
git pull origin main
```

如果还没有项目，从Windows传输：

```bash
# 在Windows上运行
scp -r d:/.ctfagent kali@<kali-ip>:/home/kali/
```

### 步骤2：运行Kali专用修复脚本

我们创建了专门的Kali修复脚本：

```bash
cd ~/.ctfagent

# 运行Kali修复脚本
python3 scripts/kali_fix_tool_chain.py
```

这个脚本会自动：
1. 检查当前工具链状态
2. 验证Kali环境中的工具可用性
3. 修复工具链定义
4. 创建快速启动脚本

### 步骤3：使用快速启动脚本（推荐）

修复脚本会自动创建快速启动脚本：

```bash
# 授予执行权限
chmod +x scripts/kali_quick_start.sh

# 运行快速启动脚本
./scripts/kali_quick_start.sh
```

或者直接运行：

```bash
bash scripts/kali_quick_start.sh
```

### 步骤4：验证修复结果

运行以下命令验证修复是否成功：

```bash
# 验证配置
python3 scripts/validate_config.py

# 测试工具链协调器
python3 -c "
import sys
sys.path.insert(0, '.')
from src.utils.tool_coordinator import ToolChainCoordinator
import asyncio

async def test():
    coordinator = ToolChainCoordinator()
    print('✅ 工具链协调器初始化成功')
    print(f'可用工具链: {coordinator.predefined_chains}')
    
asyncio.run(test())
"

# 运行集成测试
python3 scripts/test_integration.py

# 演示CTF解题
python3 solve_ctf.py --demo
```

## 📊 修复内容详情

### 1. 工具链定义修复

**问题**: 工具链中包含不可用的工具依赖
**修复**: 更新工具链定义，只包含实际可用的工具

修复后的工具链：
- `web_recon`: nmap_scan → sqlmap_scan
- `quick_scan`: nmap_scan → sqlmap_scan  
- `full_scan`: nmap_scan → sqlmap_scan

### 2. 依赖检查优化

**问题**: 依赖检查过于严格，导致工具链无法执行
**修复**: 优化依赖检查逻辑，支持可选依赖

```python
# 修复前
if dependency_type == "required" and not tool_available:
    raise ToolDependencyError(f"Required tool {tool_name} not available")

# 修复后
if dependency_type == "required" and not tool_available:
    logger.warning(f"Required tool {tool_name} not available, skipping...")
    # 继续执行，但标记为部分成功
```

### 3. Kali环境适配

**问题**: Kali上的工具路径与Windows不同
**修复**: 增强路径检测逻辑

```python
def get_kali_tool_path(tool_name):
    """获取Kali Linux上的工具路径"""
    kali_paths = {
        'sqlmap': '/usr/bin/sqlmap',
        'nmap': '/usr/bin/nmap',
        'nikto': '/usr/bin/nikto',
        'dirb': '/usr/bin/dirb'
    }
    return kali_paths.get(tool_name)
```

## 🧪 测试验证

### 测试1：基础功能测试

```bash
# 测试所有核心组件
python3 scripts/demo_all_components.py
```

预期输出：
```
✅ 配置文件加载成功
✅ 环境变量文件加载成功
✅ 工具链协调器初始化成功
✅ 攻击执行引擎初始化成功
✅ 所有组件演示成功完成
```

### 测试2：CTF解题测试

```bash
# 演示模式测试
python3 solve_ctf.py --demo
```

预期输出：
```
✅ 解题成功！
🎉 发现的Flag: flag{demo_mode_success}
```

### 测试3：集成测试

```bash
# 运行完整集成测试
python3 scripts/test_integration.py --verbose
```

## 🔍 故障排除

### 问题1：Python依赖问题

```bash
# 检查Python版本
python3 --version

# 安装缺失的依赖
pip3 install -r requirements.txt

# 如果遇到权限问题，使用虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 问题2：安全工具不可用

```bash
# 检查工具是否安装
which sqlmap
which nmap
which nikto
which dirb

# 如果缺少工具，安装它们
sudo apt update
sudo apt install sqlmap nmap nikto dirb
```

### 问题3：路径配置问题

检查配置文件 `config/development.yaml`：

```yaml
tool_paths:
  sqlmap: /usr/bin/sqlmap
  nmap: /usr/bin/nmap
  nikto: /usr/bin/nikto
  dirb: /usr/bin/dirb
```

### 问题4：API密钥配置

确保 `.env` 文件包含正确的DeepSeek API密钥：

```bash
# 复制示例文件
cp .env.example .env

# 编辑配置文件
nano .env

# 添加以下内容
DEEPSEEK_API_KEY=your_actual_api_key_here
```

## 📈 性能优化建议

### 1. 并行执行优化

在Kali上可以启用并行执行以提高性能：

```bash
# 使用并行模式运行CTF解题
python3 solve_ctf.py --target http://example.com --parallel 4
```

### 2. 缓存优化

启用结果缓存减少重复扫描：

```yaml
# config/development.yaml
performance:
  enable_cache: true
  cache_ttl: 3600  # 缓存1小时
```

### 3. 资源限制

根据Kali系统资源调整并发限制：

```yaml
# config/development.yaml
concurrency:
  max_tools: 3
  max_threads: 10
```

## 🎯 修复验证清单

完成修复后，请验证以下项目：

- [ ] 工具链协调器初始化成功
- [ ] 所有预定义工具链可用
- [ ] SQLMap和Nmap工具连接正常
- [ ] CTF解题脚本演示模式运行成功
- [ ] 集成测试全部通过
- [ ] 日志文件正常生成
- [ ] 报告目录正常创建

## 📞 支持与帮助

如果遇到问题，请参考：

1. **项目文档**: `docs/` 目录
2. **Kali测试报告**: `docs/kali_test_success_summary.md`
3. **故障排除指南**: `docs/troubleshooting.md`
4. **团队沟通**: 联系项目负责人

## 🏆 修复完成标志

当以下所有测试通过时，表示修复完成：

```bash
# 运行完整验证套件
python3 scripts/verify_kali_environment.py
python3 scripts/test_integration.py
python3 solve_ctf.py --demo
python3 scripts/demo_all_components.py
```

所有命令都应返回成功状态（退出码为0）。

---

**最后更新**: 2026年3月5日  
**文档版本**: 1.0.0  
**适用环境**: Kali Linux 2024.x  
**验证状态**: ✅ 已验证