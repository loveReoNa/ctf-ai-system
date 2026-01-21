# 智能CTF攻击模拟系统 (Intelligent Attack Simulation System for CTF Challenges)

## 项目概述
基于AI的CTF攻击模拟系统，能够自主分析CTF Web挑战、规划攻击链并执行漏洞利用。

## 技术栈
- **后端**: Python 3.8+
- **AI框架**: OpenAI API + ReAct式代理
- **协议**: MCP (Model Context Protocol)
- **安全工具**: sqlmap, nmap, Burp Suite
- **虚拟化**: VMware + Kali Linux
- **前端**: Flask/Django + 可视化图表

## 项目结构
.ctfagent/
├── src/                    # 源代码
│   ├── mcp_server/        # MCP服务器实现
│   ├── agents/           # AI代理
│   ├── utils/            # 工具函数
│   └── web_ui/           # 前端界面
├── tests/                 # 测试代码
├── docs/                  # 文档
├── config/                # 配置文件
├── scripts/               # 脚本文件
└── data/                  # 数据文件


## 快速开始
1. 克隆仓库
2. 安装依赖: `pip install -r requirements.txt`
3. 配置环境变量
4. 运行MCP服务器: `python src/mcp_server/server.py`

## 开发环境
- **主环境**: Windows 10/11
- **运行环境**: Kali Linux虚拟机 (VMware)
- **开发工具**: VS Code with Remote SSH

## 许可证
MIT License
