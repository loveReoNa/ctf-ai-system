# CTF Agent 智能攻击模拟系统

## 概述

CTF Agent 是一个基于AI的智能攻击模拟系统，专门用于自动解决CTF（Capture The Flag）挑战。系统采用ReAct（Reasoning + Acting）框架，能够自主分析CTF挑战、规划攻击链并执行漏洞利用。

## 核心特性

- 🤖 **AI驱动的攻击模拟**：使用DeepSeek API进行智能分析和规划
- 🔧 **多工具集成**：集成SQLMap、Nmap等安全工具
- 🌐 **RESTful API**：提供完整的API接口，支持远程调用
- 📊 **实时可视化**：攻击过程可视化和管理界面
- 🐳 **容器化支持**：支持Docker部署
- 📝 **详细报告**：自动生成攻击报告和日志

## 系统架构

```
ctf-ai-system/
├── src/
│   ├── api/              # API服务器
│   ├── agents/           # AI代理实现
│   ├── mcp_server/       # 工具集成层
│   ├── utils/            # 工具函数
│   └── web_ui/           # Web界面
├── config/               # 配置文件
├── scripts/              # 工具脚本
├── logs/                 # 日志文件
├── reports/              # 攻击报告
└── tests/                # 测试文件
```

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd ctf-ai-system

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置系统

```bash
# 复制环境变量文件
cp .env.example .env

# 编辑.env文件，设置DeepSeek API密钥
# DEEPSEEK_API_KEY=your_api_key_here
```

### 3. 启动系统

#### 方式一：使用启动脚本（推荐）

```bash
# 交互式启动
python start_ctf_agent.py

# 或快速启动
python start_ctf_agent.py --quick
```

#### 方式二：手动启动

```bash
# 启动API服务器
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload

# 在另一个终端启动MCP服务器（如果需要）
python src/mcp_server/server.py
```

### 4. 验证安装

打开浏览器访问：http://localhost:8000/docs

您应该能看到Swagger API文档界面。

## API使用示例

### 1. 检查系统状态

```bash
curl http://localhost:8000/status
```

### 2. 提交CTF挑战

```bash
curl -X POST http://localhost:8000/challenge \
  -H "Content-Type: application/json" \
  -d '{
    "title": "SQL注入挑战",
    "description": "一个存在SQL注入漏洞的Web应用",
    "target_url": "http://testphp.vulnweb.com/artists.php?artist=1",
    "category": "web",
    "difficulty": "easy",
    "hints": ["尝试SQL注入", "查看URL参数"]
  }'
```

### 3. 检查任务状态

```bash
# 替换{task_id}为实际的任务ID
curl http://localhost:8000/tasks/{task_id}
```

### 4. 直接执行工具

```bash
curl -X POST http://localhost:8000/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "sqlmap_scan",
    "parameters": {
      "url": "http://testphp.vulnweb.com/artists.php?artist=1",
      "level": 1,
      "risk": 1
    }
  }'
```

## Python客户端使用

### 基本使用

```python
from api_client_example import CTFAgentClient

# 创建客户端
client = CTFAgentClient("http://localhost:8000")

# 提交挑战
challenge = {
    "title": "测试挑战",
    "description": "测试描述",
    "target_url": "http://example.com",
    "category": "web",
    "difficulty": "easy"
}

response = client.submit_challenge(challenge)
task_id = response["task_id"]
print(f"任务ID: {task_id}")

# 等待任务完成
status = client.wait_for_task_completion(task_id)
print(f"任务结果: {status}")
```

### 完整示例

运行提供的示例客户端：

```bash
# 完整工作流程演示
python api_client_example.py --demo full

# 工具执行演示
python api_client_example.py --demo tools

# 快速测试
python api_client_example.py --demo quick
```

## 支持的CTF挑战类型

### Web安全
- SQL注入
- XSS跨站脚本
- 文件包含
- 命令注入
- SSRF服务器端请求伪造

### 网络扫描
- 端口扫描
- 服务识别
- 漏洞扫描

### 其他类型
- 密码破解
- 逆向工程（基础）
- 取证分析

## 工具集成

### 已集成工具
- **SQLMap**: SQL注入自动化检测和利用
- **Nmap**: 网络端口扫描和服务识别
- **自定义脚本**: Python脚本执行环境

### 计划集成工具
- OWASP ZAP
- Burp Suite
- Hydra
- John the Ripper

## 配置说明

### 主要配置文件

1. **config/development.yaml** - 主配置文件
2. **.env** - 环境变量（API密钥等）
3. **pyproject.toml** - 项目元数据

### 关键配置项

```yaml
# config/development.yaml 示例
ai:
  provider: "deepseek"
  model: "deepseek-chat"
  temperature: 0.7

mcp:
  enabled: true
  tools:
    sqlmap:
      path: "/usr/bin/sqlmap"
    nmap:
      path: "/usr/bin/nmap"

api:
  server:
    host: "0.0.0.0"
    port: 8000
  cors:
    allow_origins: ["*"]
```

## 开发指南

### 添加新工具

1. 在 `src/mcp_server/tools/` 目录下创建工具包装器
2. 实现工具接口
3. 在MCP服务器中注册工具
4. 更新工具映射

### 扩展AI代理

1. 修改 `src/agents/react_agent.py`
2. 添加新的分析策略
3. 实现新的攻击步骤类型

### 添加新的API端点

1. 在 `src/api/server.py` 中添加新的路由
2. 定义请求/响应模型
3. 实现业务逻辑

## 故障排除

### 常见问题

1. **API服务器无法启动**
   - 检查端口是否被占用
   - 检查Python依赖是否安装完整

2. **DeepSeek API调用失败**
   - 检查 `.env` 文件中的API密钥
   - 检查网络连接

3. **工具执行失败**
   - 检查工具是否已安装
   - 检查工具路径配置

4. **任务卡住**
   - 检查日志文件 `logs/api_server.log`
   - 检查目标是否可达

### 日志查看

```bash
# 查看API服务器日志
tail -f logs/api_server.log

# 查看MCP服务器日志
tail -f logs/mcp_server.log
```

## 安全注意事项

⚠️ **重要警告**

1. **仅用于授权测试**：仅在拥有明确授权的目标上使用本系统
2. **遵守法律法规**：遵守当地网络安全法律法规
3. **教育目的**：本系统主要用于网络安全教育和研究
4. **数据保护**：不要泄露测试中获取的敏感数据

## 项目路线图

### 已完成
- [x] 基础项目架构
- [x] ReAct AI代理框架
- [x] SQLMap集成
- [x] RESTful API服务器
- [x] 配置和日志系统

### 进行中
- [ ] Web可视化界面
- [ ] 更多工具集成（Nmap, ZAP等）
- [ ] 攻击链可视化
- [ ] 教育模式

### 计划中
- [ ] Docker容器化
- [ ] 分布式部署
- [ ] 机器学习优化
- [ ] 多语言支持

## 贡献指南

欢迎贡献！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 联系方式

- 项目仓库：<repository-url>
- 问题反馈：GitHub Issues
- 邮箱：<contact-email>

## 致谢

- DeepSeek AI - 提供AI能力
- SQLMap/Nmap - 安全工具
- FastAPI - Web框架
- 所有贡献者和用户

---

**免责声明**: 本工具仅用于教育和授权的安全测试。使用者需对使用本工具造成的任何后果负责。