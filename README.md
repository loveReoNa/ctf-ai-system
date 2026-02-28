# 智能CTF攻击模拟系统 (Intelligent Attack Simulation System for CTF Challenges)

## 项目概述
基于AI的CTF攻击模拟系统，能够自主分析CTF Web挑战、规划攻击链并执行漏洞利用。

## 核心功能
- **智能攻击模拟**: AI代理自主分析CTF挑战并执行攻击
- **工具集成**: 集成sqlmap、nmap等安全工具
- **MCP架构**: 基于Model Context Protocol的模块化工具管理
- **可视化界面**: 攻击过程实时监控和结果分析
- **教育价值**: 详细的攻击过程回放和分析

## 技术栈
- **后端**: Python 3.8+
- **Web框架**: FastAPI/Flask
- **AI框架**: DeepSeek API + ReAct式代理
- **协议**: MCP (Model Context Protocol)
- **安全工具**: sqlmap, nmap, Burp Suite, OWASP ZAP
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **前端**: React/Vue.js + D3.js/ECharts
- **容器化**: Docker

## 项目结构
```
.ctfagent/
├── src/                    # 源代码
│   ├── mcp_server/        # MCP服务器实现
│   │   ├── server.py      # MCP服务器主文件
│   │   ├── tools/         # 工具包装器
│   │   │   ├── sqlmap_wrapper.py
│   │   │   └── __init__.py
│   │   └── __init__.py
│   ├── agents/           # AI代理 (ReAct框架)
│   ├── utils/            # 工具函数
│   │   ├── config_manager.py  # 配置管理
│   │   ├── deepseek_client.py # DeepSeek API客户端
│   │   └── logger.py          # 日志系统
│   └── web_ui/           # 前端界面
├── tests/                 # 测试代码
├── docs/                  # 文档
├── config/                # 配置文件
│   └── development.yaml   # 开发环境配置
├── scripts/               # 脚本文件
│   ├── validate_config.py # 配置验证
│   ├── test_mcp_server.py # MCP服务器测试
│   └── start_mcp_server.py # 服务器启动脚本
├── data/                  # 数据文件
└── logs/                  # 日志文件
```

## 当前进度 (更新于2026年2月28日)

### ✅ 已完成
1. **项目基础架构** - ✅ 100%
   - 完整的项目目录结构
   - Git版本控制配置
   - Python虚拟环境配置

2. **配置管理系统** - ✅ 100%
   - YAML配置文件 (`config/development.yaml`)
   - 环境变量管理 (`.env`文件)
   - 配置管理器 (`src/utils/config_manager.py`)

3. **日志系统** - ✅ 100%
   - 多级别日志记录
   - JSON格式和彩色控制台输出
   - 文件轮转和备份

4. **DeepSeek API集成** - ✅ 100%
   - 完整的API客户端 (`src/utils/deepseek_client.py`)
   - CTF挑战分析功能
   - 攻击载荷生成功能

5. **MCP服务器基础框架** - ✅ 85% (已修复跨平台路径问题)
   - MCP协议实现 (`src/mcp_server/server.py`)
   - 工具管理器 (`CTFMCPToolManager`)
   - SQLMap和Nmap工具包装器 (支持Windows/Kali自动路径选择)
   - 工具调用接口
   - 跨平台路径适配 (`get_tool_path()`函数)

6. **Kali Linux环境部署** - ✅ 100%
   - Kali环境验证脚本 (`scripts/verify_kali_environment.py`)
   - 虚拟环境自动化脚本 (`scripts/setup_kali_venv.sh`)
   - Python依赖问题修复
   - 详细部署指南 (`docs/kali_python_fix.md`)

7. **ReAct AI代理框架** - ✅ 70% (已修复API响应处理)
   - ReAct代理核心实现 (`src/agents/react_agent.py`)
   - 挑战分析模块 (已修复字典响应处理)
   - 攻击链规划模块 (已修复字典响应处理)
   - 执行引擎基础
   - 测试套件 (`scripts/test_react_agent.py`) - 全部通过

### ⚠️ 进行中
1. **AI代理集成测试** - 连接测试和功能验证 ✅ (已完成)
2. **攻击链执行引擎完善** - 步骤自动执行和状态管理 ⏳ (等待Kali工具测试)
3. **结果分析和报告生成** - 自动生成攻击报告 ⏳

### 📋 待完成
1. Web管理界面开发
2. 安全工具扩展 (Burp Suite, OWASP ZAP)
3. 数据库持久化存储
4. 完整测试套件和性能优化
5. Docker容器化部署

### 📊 总体进度
- **第一阶段（基础架构）**: 100% ✅
- **第二阶段（AI代理开发）**: 70% ⏳ (已修复关键问题)
- **第三阶段（工具集成）**: 60% ⏳ (跨平台路径已修复)
- **总体项目进度**: 75% 📈

## 快速开始

### Windows 环境

#### 1. 环境准备
```bash
# 克隆仓库
git clone <repository-url>
cd .ctfagent

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑.env文件，添加DeepSeek API密钥
```

#### 2. 配置验证
```bash
# 验证配置
python scripts/validate_config.py
```

#### 3. 启动MCP服务器
```bash
# 方式一：使用启动脚本
python scripts/start_mcp_server.py

# 方式二：直接运行
python src/mcp_server/server.py --server

# 方式三：测试模式
python scripts/test_mcp_server.py
```

#### 4. 测试工具集成
```bash
# 测试SQLMap包装器
python -c "
from src.mcp_server.tools import sqlmap_wrapper
import asyncio

async def test():
    wrapper = sqlmap_wrapper.SQLMapWrapper()
    connected = await wrapper.test_connection()
    print(f'SQLMap连接: {\"成功\" if connected else \"失败\"}')

asyncio.run(test())
"
```

### Kali Linux 环境

Kali Linux已预装所有安全工具，部署更简单：

#### 1. 传输项目到Kali
```bash
# 方法一：使用传输脚本（在Windows中运行）
# 编辑 scripts/transfer_to_kali.bat 中的Kali IP地址
scripts/transfer_to_kali.bat

# 方法二：手动传输
scp -r .ctfagent kali@<kali-ip>:/home/kali/
```

#### 2. Kali环境验证
```bash
# 在Kali中运行
cd .ctfagent
python3 scripts/verify_kali_environment.py
```

#### 3. 安装依赖和配置
```bash
# 安装Python依赖
pip3 install -r requirements.txt

# 配置环境变量
cp .env.example .env
nano .env  # 添加DeepSeek API密钥
```

#### 4. 运行测试
```bash
# 验证配置
python3 scripts/validate_config.py

# 测试MCP服务器
python3 scripts/test_mcp_server.py

# 启动服务器
python3 scripts/start_mcp_server.py
```

#### 5. 验证工具可用性
```bash
# 在Kali中，安全工具应该已安装
which sqlmap  # 应该显示 /usr/bin/sqlmap
which nmap    # 应该显示 /usr/bin/nmap

# 测试工具连接
python3 -c "
import asyncio
from src.mcp_server.tools.sqlmap_wrapper import SQLMapWrapper

async def test():
    wrapper = SQLMapWrapper()
    connected = await wrapper.test_connection()
    print(f'SQLMap连接测试: {\"✅ 成功\" if connected else \"❌ 失败\"}')

asyncio.run(test())
"
```

详细Kali部署指南请参考 [docs/kali_deployment.md](docs/kali_deployment.md)

## MCP服务器使用

### 可用工具
1. **sqlmap_scan**: SQL注入扫描工具
   ```python
   from src.mcp_server import CTFMCPServer
   import asyncio
   
   async def scan():
       server = CTFMCPServer()
       await server.initialize()
       
       result = await server.handle_call_tool("sqlmap_scan", {
           "url": "http://testphp.vulnweb.com/artists.php?artist=1",
           "level": 1,
           "risk": 1
       })
       print(result)
   
   asyncio.run(scan())
   ```

2. **nmap_scan**: 端口扫描工具
   ```python
   result = await server.handle_call_tool("nmap_scan", {
       "target": "127.0.0.1",
       "ports": "80,443,8080"
   })
   ```

### API接口
- `handle_list_tools()`: 列出所有可用工具
- `handle_call_tool(name, arguments)`: 调用指定工具

详细文档请参考 [docs/mcp_server_usage.md](docs/mcp_server_usage.md)

## 开发指南

### 添加新工具
1. 创建工具类继承 `CTFMCPTool`
2. 实现 `get_schema()` 和 `execute()` 方法
3. 在 `CTFMCPToolManager._register_tools()` 中注册工具
4. 更新配置文件（如果需要）

### 配置说明
- 主配置文件: `config/development.yaml`
- 环境变量: `.env` 文件
- 日志配置: 通过配置文件或环境变量设置

### 测试
```bash
# 运行配置验证
python scripts/validate_config.py

# 测试MCP服务器
python scripts/test_mcp_server.py

# 测试DeepSeek API
python scripts/test_deepseek_api.py
```

## 项目计划

### 第一阶段：基础架构 ✅ (100%完成)
- [x] 项目结构搭建
- [x] 配置文件系统
- [x] 环境变量管理
- [x] 日志系统实现
- [x] DeepSeek API集成
- [x] MCP服务器基础框架
- [x] Kali Linux环境部署

### 第二阶段：核心AI代理 ⏳ (50%完成)
- [x] AI代理框架实现 (ReAct架构) - `src/agents/react_agent.py`
- [x] 挑战分析模块 - 自动漏洞识别
- [x] 攻击链规划模块 - 多步骤攻击计划
- [ ] DeepSeek API客户端完善 - 流式响应处理
- [ ] 攻击执行引擎 - 步骤自动执行
- [ ] 结果分析和报告生成

### 第三阶段：工具集成 ⏳ (30%完成)
- [x] MCP服务器核心实现 - 基础框架完成
- [x] SQLMap和Nmap工具集成
- [ ] 安全工具深度集成 (Burp Suite, OWASP ZAP)
- [ ] 工具调用接口开发 - 高级功能
- [ ] 攻击执行引擎 - 完整实现

### 第四阶段：Web界面 ⏳ (0%开始)
- [ ] 前端框架搭建 (React/Vue.js)
- [ ] 攻击链可视化 (D3.js/ECharts)
- [ ] 实时监控界面
- [ ] 结果报告生成

### 第五阶段：测试优化 ⏳ (10%开始)
- [x] 基础测试套件 - `scripts/test_react_agent.py`
- [ ] 单元测试和集成测试 - 完整覆盖
- [ ] 性能优化
- [ ] 安全性测试
- [ ] 用户体验优化
- [ ] Docker容器化部署

## 贡献指南
1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证
MIT License

## 联系方式
- 项目负责人: [Your Name]
- 邮箱: [Your Email]
- 项目文档: [docs/](docs/)

## 致谢
- DeepSeek API 提供AI能力
- sqlmap、nmap等开源安全工具
- MCP协议社区
- 所有贡献者和测试人员
