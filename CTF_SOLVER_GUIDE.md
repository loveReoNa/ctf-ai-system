# CTF解题系统使用指南

## 概述

本系统是一个基于AI的CTF（Capture The Flag）解题系统，专门用于解决Web安全挑战，特别是SQL注入漏洞。系统集成了SQLMap等安全工具，并提供了智能的自动化解题流程。

## 系统架构

```
ctf-ai-system/
├── src/
│   ├── mcp_server/
│   │   ├── tools/
│   │   │   ├── sqlmap_wrapper.py    # SQLMap包装器
│   │   │   └── nmap_wrapper.py      # Nmap包装器
│   │   └── server.py                # MCP服务器
│   └── utils/
│       ├── logger.py                # 日志系统
│       ├── config_manager.py        # 配置管理
│       └── deepseek_client.py       # AI客户端
├── scripts/
│   ├── solve_ctf_final.py           # 最终版解题脚本
│   ├── solve_ctf_aggressive.py      # 激进版解题脚本
│   └── solve_ctf_enhanced.py        # 增强版解题脚本
├── config/
│   └── development.yaml             # 配置文件
├── .env                             # 环境变量
└── requirements.txt                 # 依赖包
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境

1. 复制环境变量模板：
   ```bash
   cp .env.example .env
   ```

2. 编辑`.env`文件，设置必要的环境变量（如DeepSeek API密钥）

### 3. 运行CTF解题器

#### 基本用法

```bash
# 使用GET请求文件
python solve_ctf_final.py "http://target.com" -r ctf_request_get.txt

# 直接扫描URL
python solve_ctf_final.py "http://target.com/check.php?username=admin&password=test"

# 详细输出
python solve_ctf_final.py "http://target.com" -r request.txt -v
```

#### 参数说明

- `target`: 目标URL（必需）
- `-r, --request-file`: 包含HTTP请求的文件
- `-u, --username-param`: 用户名参数名（默认: username）
- `-p, --password-param`: 密码参数名（默认: password）
- `-v, --verbose`: 详细输出模式

## 请求文件格式

### GET请求示例

```
GET /check.php?username=admin&password=test HTTP/1.1
Host: target.com
User-Agent: Mozilla/5.0
Accept: text/html
Connection: close
```

### POST请求示例

```
POST /login.php HTTP/1.1
Host: target.com
User-Agent: Mozilla/5.0
Content-Type: application/x-www-form-urlencoded
Content-Length: 27

username=admin&password=test
```

## 解题流程

系统按照以下流程自动解题：

1. **漏洞检测**：使用SQLMap检测SQL注入漏洞
2. **自动利用**：自动枚举数据库、表和数据
3. **Flag提取**：从数据中提取flag
4. **报告生成**：生成详细的解题报告

## 高级功能

### 1. 激进模式

使用更激进的参数进行扫描：

```bash
python solve_ctf_aggressive.py "http://target.com" -r request.txt
```

### 2. 手动payload测试

系统包含常见的手动SQL注入payload，用于绕过WAF或特殊过滤。

### 3. 智能参数识别

系统自动识别注入参数，支持GET和POST两种请求方式。

## 实战示例

### 示例1：解决BUUOJ SQL注入挑战

```bash
# 创建GET请求文件
cat > ctf_request_get.txt << 'EOF'
GET /check.php?username=admin&password=test HTTP/1.1
Host: 600ac8e9-f9ec-49c6-b102-89b50c62b2be.node5.buuoj.cn:81
User-Agent: Mozilla/5.0
Accept: text/html
Connection: close
EOF

# 运行解题器
python solve_ctf_final.py "http://600ac8e9-f9ec-49c6-b102-89b50c62b2be.node5.buuoj.cn:81" -r ctf_request_get.txt -v
```

### 示例2：直接扫描带参数的URL

```bash
python solve_ctf_final.py "http://target.com/check.php?username=admin&password=test" -v
```

## 输出说明

### 控制台输出

```
================================================================================
CTF SQL注入解题器
================================================================================
目标: http://target.com
时间: 2026-03-08 12:00:00
================================================================================

🔍 阶段1: 检测SQL注入漏洞...
✅ 发现 1 个漏洞

⚡ 阶段2: 自动利用漏洞...
🎉🎉🎉 找到Flag: flag{example_flag_123} 🎉🎉🎉

================================================================================
CTF解题完成摘要
================================================================================
目标: http://target.com
挑战类型: sql-injection
耗时: 0:02:30
完成阶段: vulnerability_detection, exploitation
发现漏洞: 1
找到Flag: 1

🎉 发现的Flag:
  flag{example_flag_123}

成功: ✅ 是
================================================================================
```

### 报告文件

系统会在`reports/`目录下生成JSON格式的详细报告，包含：
- 解题时间线
- 发现的漏洞详情
- 提取的数据
- 使用的payload
- 系统配置信息

## 故障排除

### 常见问题

1. **SQLMap未安装**
   ```
   错误: SQLMap连接测试失败
   解决: 安装SQLMap - pip install sqlmap 或从官网下载
   ```

2. **请求文件格式错误**
   ```
   错误: 无效的请求文件
   解决: 确保请求文件符合HTTP协议格式
   ```

3. **目标不可达**
   ```
   错误: 连接超时
   解决: 检查网络连接和目标URL
   ```

### 调试模式

使用`-v`参数启用详细日志：

```bash
python solve_ctf_final.py "http://target.com" -r request.txt -v
```

## 扩展开发

### 添加新工具

1. 在`src/mcp_server/tools/`目录下创建新的工具包装器
2. 实现工具接口
3. 在解题脚本中集成新工具

### 自定义payload

编辑`solve_ctf_final.py`中的`_try_manual_payloads`方法，添加自定义payload。

## 安全注意事项

1. **合法使用**：仅用于授权的CTF比赛或安全测试
2. **目标权限**：确保拥有测试目标的权限
3. **数据保护**：不要泄露提取的敏感数据
4. **遵守法律**：遵守当地网络安全法律法规

## 性能优化

1. **并发扫描**：调整`threads`参数提高扫描速度
2. **缓存结果**：系统会自动缓存扫描结果
3. **智能超时**：根据网络状况自动调整超时时间

## 联系与支持

如有问题或建议，请通过以下方式联系：

- GitHub Issues: [项目仓库地址]
- 邮箱: [联系邮箱]
- 文档: [项目文档地址]

---

**免责声明**: 本工具仅用于教育和授权的安全测试。使用者需对使用本工具造成的任何后果负责。