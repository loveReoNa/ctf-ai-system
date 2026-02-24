# MCP服务器使用文档

## 概述

CTF AI MCP服务器是基于Model Context Protocol的安全工具管理服务器，提供统一的工具调用接口，支持sqlmap、nmap等安全工具的集成。

## 快速开始

### 1. 安装依赖

确保已安装所需依赖：

```bash
pip install -r requirements.txt
```

### 2. 配置工具路径

编辑 `config/development.yaml` 文件，确保工具路径正确：

```yaml
tools:
  sqlmap:
    path: "/usr/bin/sqlmap"  # Linux路径
    windows_path: "C:/Program Files/sqlmap/sqlmap.py"  # Windows路径
  nmap:
    path: "/usr/bin/nmap"
    windows_path: "C:/Program Files/Nmap/nmap.exe"
```

### 3. 启动MCP服务器

#### 方式一：使用启动脚本
```bash
python scripts/start_mcp_server.py
```

#### 方式二：直接运行
```bash
python src/mcp_server/server.py --server
```

#### 方式三：测试模式
```bash
python scripts/test_mcp_server.py
```

## 可用工具

### 1. SQLMap扫描工具

**工具名称**: `sqlmap_scan`

**描述**: 使用sqlmap进行SQL注入扫描

**参数**:
- `url` (必需): 目标URL
- `method`: HTTP方法 (GET/POST)，默认: GET
- `data`: POST数据
- `level`: 测试等级 (1-5)，默认: 1
- `risk`: 风险等级 (1-3)，默认: 1

**示例调用**:
```python
from src.mcp_server import CTFMCPServer

server = CTFMCPServer()
await server.initialize()

result = await server.handle_call_tool("sqlmap_scan", {
    "url": "http://testphp.vulnweb.com/artists.php?artist=1",
    "method": "GET",
    "level": 1,
    "risk": 1
})
```

### 2. Nmap扫描工具

**工具名称**: `nmap_scan`

**描述**: 使用nmap进行端口扫描

**参数**:
- `target` (必需): 目标主机或IP地址
- `ports`: 端口范围 (如: 80,443,1-1000)，默认: 1-1000
- `scan_type`: 扫描类型 (syn, connect, udp)，默认: syn

**示例调用**:
```python
result = await server.handle_call_tool("nmap_scan", {
    "target": "127.0.0.1",
    "ports": "80,443,8080",
    "scan_type": "syn"
})
```

## API接口

### 列出所有工具

```python
tools = await server.handle_list_tools()
```

返回格式:
```json
[
  {
    "name": "sqlmap_scan",
    "description": "使用sqlmap进行SQL注入扫描",
    "schema": {
      "type": "object",
      "properties": {...},
      "required": ["url"]
    }
  },
  ...
]
```

### 调用工具

```python
result = await server.handle_call_tool(tool_name, arguments)
```

返回格式:
```json
{
  "success": true,
  "return_code": 0,
  "stdout": "...",
  "stderr": "...",
  "vulnerabilities": [...],
  "summary": {...}
}
```

## 集成示例

### 与AI代理集成

```python
from src.mcp_server import CTFMCPServer
from src.utils.deepseek_client import deepseek_client

class CTFAIAgent:
    def __init__(self):
        self.mcp_server = CTFMCPServer()
        self.deepseek = deepseek_client
    
    async def analyze_and_attack(self, target_url: str):
        # 使用AI分析目标
        analysis = await self.deepseek.analyze_ctf_challenge(
            "SQL注入挑战",
            target_url
        )
        
        # 如果AI建议SQL注入测试
        if "SQL注入" in analysis["content"]:
            # 使用MCP服务器执行扫描
            result = await self.mcp_server.handle_call_tool("sqlmap_scan", {
                "url": target_url,
                "level": 2,
                "risk": 2
            })
            
            return result
        
        return {"message": "无漏洞发现"}
```

### Web界面集成

```python
from flask import Flask, jsonify, request
import asyncio

app = Flask(__name__)
server = None

@app.before_first_request
def initialize_server():
    global server
    server = CTFMCPServer()
    asyncio.run(server.initialize())

@app.route('/api/tools', methods=['GET'])
def list_tools():
    tools = asyncio.run(server.handle_list_tools())
    return jsonify(tools)

@app.route('/api/tools/<tool_name>/execute', methods=['POST'])
def execute_tool(tool_name):
    data = request.json
    result = asyncio.run(server.handle_call_tool(tool_name, data))
    return jsonify(result)
```

## 故障排除

### 1. 工具路径错误

**症状**: "SQLMap路径可能无效" 警告

**解决方案**:
1. 确认sqlmap/nmap已安装
2. 更新配置文件中的路径
3. 或将工具添加到系统PATH

### 2. MCP协议错误

**症状**: 服务器启动失败，MCP相关错误

**解决方案**:
1. 确保已安装mcp包: `pip install mcp`
2. 检查Python版本兼容性

### 3. 权限问题

**症状**: "Permission denied" 错误

**解决方案**:
1. 确保有执行工具的权限
2. 在Linux/macOS上可能需要sudo
3. 或使用适当的用户权限运行

## 扩展开发

### 添加新工具

1. 创建工具类继承 `CTFMCPTool`:
```python
from src.mcp_server import CTFMCPTool

class NewTool(CTFMCPTool):
    def __init__(self):
        super().__init__(
            name="new_tool",
            description="新工具描述"
        )
    
    def get_schema(self):
        return {
            "type": "object",
            "properties": {...},
            "required": [...]
        }
    
    async def execute(self, **kwargs):
        # 工具实现
        return {"success": True, "result": ...}
```

2. 在 `CTFMCPToolManager._register_tools()` 中注册工具

3. 更新配置文件（如果需要）

## 性能优化

1. **连接池**: 对于频繁调用的工具，使用连接池
2. **缓存**: 缓存扫描结果，避免重复扫描
3. **异步处理**: 所有工具调用都是异步的，支持并发
4. **超时控制**: 每个工具调用都有超时限制

## 安全注意事项

1. **权限隔离**: 工具在受限环境中运行
2. **输入验证**: 所有参数都经过验证
3. **日志记录**: 所有操作都有详细日志
4. **资源限制**: 限制工具的资源使用

## 下一步计划

1. 添加更多安全工具（Burp Suite, OWASP ZAP等）
2. 实现工具链编排（多工具协同工作）
3. 添加WebSocket实时通信
4. 开发图形化监控界面
```

## 版本历史

- v0.1.0 (2026-02-24): 初始版本，支持sqlmap和nmap