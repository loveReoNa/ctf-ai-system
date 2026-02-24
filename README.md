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

## 当前进度

### ✅ 已完成
1. **项目基础架构**
   - 完整的项目目录结构
   - Git版本控制配置

2. **配置管理系统**
   - YAML配置文件 (`config/development.yaml`)
   - 环境变量管理 (`.env`文件)
   - 配置管理器 (`src/utils/config_manager.py`)

3. **日志系统**
   - 多级别日志记录
   - JSON格式和彩色控制台输出
   - 文件轮转和备份

4. **DeepSeek API集成**
   - 完整的API客户端
   - CTF挑战分析功能
   - 攻击载荷生成功能

5. **MCP服务器基础框架**
   - MCP协议实现
   - 工具管理器
   - SQLMap和Nmap工具包装器
   - 工具调用接口

### ⚠️ 进行中
1. **AI代理框架** (ReAct架构)
2. **Web可视化界面**
3. **安全工具深度集成**

### 📋 待完成
1. 攻击链规划模块
2. 实时监控仪表板
3. 完整测试套件
4. Docker容器化

## 快速开始

### 1. 环境准备
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

### 2. 配置验证
```bash
# 验证配置
python scripts/validate_config.py
```

### 3. 启动MCP服务器
```bash
# 方式一：使用启动脚本
python scripts/start_mcp_server.py

# 方式二：直接运行
python src/mcp_server/server.py --server

# 方式三：测试模式
python scripts/test_mcp_server.py
```

### 4. 测试工具集成
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

### 第一阶段：基础架构 ✅
- [x] 项目结构搭建
- [x] 配置文件系统
- [x] 环境变量管理
- [x] 日志系统实现
- [x] DeepSeek API集成
- [x] MCP服务器基础框架

### 第二阶段：核心AI代理 ⏳
- [ ] AI代理框架实现 (ReAct架构)
- [ ] 挑战分析模块
- [ ] 攻击链规划模块
- [ ] DeepSeek API客户端完善

### 第三阶段：工具集成 ⏳
- [ ] MCP服务器核心实现
- [ ] 安全工具深度集成
- [ ] 工具调用接口开发
- [ ] 攻击执行引擎

### 第四阶段：Web界面 ⏳
- [ ] 前端框架搭建
- [ ] 攻击链可视化
- [ ] 实时监控界面
- [ ] 结果报告生成

### 第五阶段：测试优化 ⏳
- [ ] 单元测试和集成测试
- [ ] 性能优化
- [ ] 安全性测试
- [ ] 用户体验优化

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
