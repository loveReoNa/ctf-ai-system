#!/usr/bin/env python3
"""
CTF AI MCP服务器
基于Model Context Protocol的安全工具管理服务器
"""
import asyncio
import json
import os
import sys
import platform
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from src.utils.logger import logger, LoggerMixin
from src.utils.config_manager import config
from src.utils.tool_parser import tool_parser_factory


def get_tool_path(tool_name: str) -> str:
    """
    根据操作系统获取工具路径
    
    Args:
        tool_name: 工具名称 (sqlmap, nmap, burpsuite)
        
    Returns:
        工具路径字符串
    """
    # 检测操作系统
    system = platform.system().lower()
    
    # 构建配置键
    if system == "windows":
        config_key = f"tools.{tool_name}.windows_path"
    else:
        # Linux/macOS使用通用路径
        config_key = f"tools.{tool_name}.path"
    
    # 从配置获取路径
    path = config.get(config_key, tool_name)
    
    # 如果配置中没有，使用工具名称（假设在PATH中）
    return path


class CTFMCPTool:
    """MCP工具基类"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = logger.getChild(f"tool.{name}")
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """执行工具"""
        raise NotImplementedError("子类必须实现execute方法")
    
    def get_schema(self) -> Dict[str, Any]:
        """获取工具输入模式"""
        return {
            "type": "object",
            "properties": {},
            "required": []
        }


class SQLMapTool(CTFMCPTool):
    """SQLMap工具包装器"""
    
    def __init__(self):
        super().__init__(
            name="sqlmap_scan",
            description="使用sqlmap进行SQL注入扫描"
        )
        self.sqlmap_path = get_tool_path("sqlmap")
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "目标URL"
                },
                "method": {
                    "type": "string",
                    "description": "HTTP方法 (GET/POST)",
                    "default": "GET"
                },
                "data": {
                    "type": "string",
                    "description": "POST数据"
                },
                "level": {
                    "type": "integer",
                    "description": "测试等级 (1-5)",
                    "minimum": 1,
                    "maximum": 5,
                    "default": 1
                },
                "risk": {
                    "type": "integer",
                    "description": "风险等级 (1-3)",
                    "minimum": 1,
                    "maximum": 3,
                    "default": 1
                }
            },
            "required": ["url"]
        }
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """执行SQLMap扫描"""
        try:
            url = kwargs.get("url")
            method = kwargs.get("method", "GET")
            data = kwargs.get("data")
            level = kwargs.get("level", 1)
            risk = kwargs.get("risk", 1)
            
            self.logger.info(f"开始SQLMap扫描: {url}")
            
            # 构建命令
            cmd = [self.sqlmap_path, "-u", url, f"--level={level}", f"--risk={risk}", "--batch"]
            
            if method.upper() == "POST" and data:
                cmd.extend(["--data", data])
            
            # 执行命令
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            result = {
                "success": process.returncode == 0,
                "return_code": process.returncode,
                "stdout": stdout.decode('utf-8', errors='ignore'),
                "stderr": stderr.decode('utf-8', errors='ignore'),
                "command": " ".join(cmd)
            }
            
            if process.returncode == 0:
                self.logger.info(f"SQLMap扫描完成: {url}")
            else:
                self.logger.warning(f"SQLMap扫描失败: {url}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"SQLMap执行错误: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class NmapTool(CTFMCPTool):
    """Nmap工具包装器"""
    
    def __init__(self):
        super().__init__(
            name="nmap_scan",
            description="使用nmap进行端口扫描"
        )
        self.nmap_path = get_tool_path("nmap")
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "目标主机或IP地址"
                },
                "ports": {
                    "type": "string",
                    "description": "端口范围 (如: 80,443,1-1000)",
                    "default": "1-1000"
                },
                "scan_type": {
                    "type": "string",
                    "description": "扫描类型 (syn, connect, udp)",
                    "default": "syn"
                }
            },
            "required": ["target"]
        }
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """执行Nmap扫描"""
        try:
            target = kwargs.get("target")
            ports = kwargs.get("ports", "1-1000")
            scan_type = kwargs.get("scan_type", "syn")
            
            self.logger.info(f"开始Nmap扫描: {target}")
            
            # 构建命令
            cmd = [self.nmap_path, "-p", ports]
            
            if scan_type == "syn":
                cmd.append("-sS")
            elif scan_type == "connect":
                cmd.append("-sT")
            elif scan_type == "udp":
                cmd.append("-sU")
            
            cmd.extend([target, "-oG", "-"])  # Grepable输出
            
            # 执行命令
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            result = {
                "success": process.returncode == 0,
                "return_code": process.returncode,
                "stdout": stdout.decode('utf-8', errors='ignore'),
                "stderr": stderr.decode('utf-8', errors='ignore'),
                "command": " ".join(cmd)
            }
            
            if process.returncode == 0:
                self.logger.info(f"Nmap扫描完成: {target}")
            else:
                self.logger.warning(f"Nmap扫描失败: {target}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Nmap执行错误: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class CTFMCPToolManager(LoggerMixin):
    """MCP工具管理器"""
    
    def __init__(self):
        self.tools: Dict[str, CTFMCPTool] = {}
        self._register_tools()
    
    def _register_tools(self):
        """注册所有可用工具"""
        # 注册SQLMap工具
        try:
            sqlmap_tool = SQLMapTool()
            self.tools[sqlmap_tool.name] = sqlmap_tool
            self.log_info(f"工具注册成功: {sqlmap_tool.name}")
        except Exception as e:
            self.log_error(f"SQLMap工具注册失败: {e}")
        
        # 注册Nmap工具
        try:
            nmap_tool = NmapTool()
            self.tools[nmap_tool.name] = nmap_tool
            self.log_info(f"工具注册成功: {nmap_tool.name}")
        except Exception as e:
            self.log_error(f"Nmap工具注册失败: {e}")
    
    def get_tool(self, name: str) -> Optional[CTFMCPTool]:
        """获取工具实例"""
        return self.tools.get(name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有可用工具"""
        tools_list = []
        for name, tool in self.tools.items():
            tools_list.append({
                "name": name,
                "description": tool.description,
                "schema": tool.get_schema()
            })
        return tools_list
    
    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具"""
        tool = self.get_tool(name)
        if not tool:
            return {
                "success": False,
                "error": f"工具未找到: {name}"
            }
        
        try:
            self.log_info(f"执行工具: {name}, 参数: {arguments}")
            # 执行工具
            raw_result = await tool.execute(**arguments)
            
            # 解析工具输出
            parsed_result = self._parse_tool_output(name, raw_result)
            
            # 合并结果
            result = {
                **raw_result,
                "parsed": parsed_result
            }
            
            self.log_info(f"工具执行完成: {name}, 解析结果: {parsed_result.get('success', False)}")
            return result
            
        except Exception as e:
            self.log_error(f"工具执行失败: {name}, 错误: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_tool_output(self, tool_name: str, raw_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析工具输出
        
        Args:
            tool_name: 工具名称
            raw_result: 原始工具执行结果
            
        Returns:
            解析后的结果
        """
        try:
            # 检查工具是否执行成功
            if not raw_result.get("success", False):
                return {
                    "success": False,
                    "error": raw_result.get("error", "工具执行失败"),
                    "message": "工具执行失败，无法解析输出"
                }
            
            # 获取工具输出
            stdout = raw_result.get("stdout", "")
            stderr = raw_result.get("stderr", "")
            
            # 使用工具解析器工厂解析输出
            parsed_result = tool_parser_factory.parse_tool_output(tool_name, stdout)
            
            # 如果解析失败，尝试使用stderr
            if not parsed_result.get("success", False) and stderr:
                parsed_result = tool_parser_factory.parse_tool_output(tool_name, stderr)
            
            # 添加原始输出摘要
            parsed_result["raw_output_summary"] = {
                "stdout_length": len(stdout),
                "stderr_length": len(stderr),
                "has_stdout": bool(stdout),
                "has_stderr": bool(stderr)
            }
            
            return parsed_result
            
        except Exception as e:
            self.log_error(f"工具输出解析失败: {tool_name}, 错误: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "工具输出解析失败"
            }


class CTFMCPServer:
    """CTF MCP服务器主类"""
    
    def __init__(self):
        self.logger = logger.getChild("mcp_server")
        self.tool_manager = CTFMCPToolManager()
        self.session: Optional[ClientSession] = None
    
    async def initialize(self):
        """初始化MCP服务器"""
        self.logger.info("初始化CTF MCP服务器...")
        
        # 检查工具配置
        self._check_tool_configurations()
        
        self.logger.info(f"已注册工具: {list(self.tool_manager.tools.keys())}")
    
    def _check_tool_configurations(self):
        """检查工具配置"""
        sqlmap_path = get_tool_path("sqlmap")
        nmap_path = get_tool_path("nmap")
        
        # 检查路径是否存在
        if sqlmap_path and sqlmap_path != "sqlmap":
            if not Path(sqlmap_path).exists():
                self.logger.warning(f"SQLMap路径可能无效: {sqlmap_path}")
            else:
                self.logger.info(f"SQLMap路径有效: {sqlmap_path}")
        else:
            self.logger.info("使用默认SQLMap路径（假设在PATH中）")
        
        if nmap_path and nmap_path != "nmap":
            if not Path(nmap_path).exists():
                self.logger.warning(f"Nmap路径可能无效: {nmap_path}")
            else:
                self.logger.info(f"Nmap路径有效: {nmap_path}")
        else:
            self.logger.info("使用默认Nmap路径（假设在PATH中）")
    
    async def handle_list_tools(self) -> List[Dict[str, Any]]:
        """处理列出工具请求"""
        return self.tool_manager.list_tools()
    
    async def handle_call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """处理调用工具请求"""
        return await self.tool_manager.execute_tool(name, arguments)
    
    async def run_stdio_server(self):
        """运行标准IO MCP服务器"""
        self.logger.info("启动MCP标准IO服务器...")
        
        # 创建服务器参数
        server_params = StdioServerParameters(
            command="python",
            args=[str(Path(__file__).resolve())],
            env=os.environ.copy()
        )
        
        # 创建标准IO客户端
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                self.session = session
                
                # 初始化会话
                await session.initialize()
                self.logger.info("MCP会话初始化完成")
                
                # 主循环
                try:
                    while True:
                        await asyncio.sleep(1)
                except KeyboardInterrupt:
                    self.logger.info("收到中断信号，关闭服务器")
                except Exception as e:
                    self.logger.error(f"服务器错误: {e}")
    
    async def run_test(self):
        """运行测试模式"""
        self.logger.info("运行MCP服务器测试模式...")
        
        # 列出所有工具
        tools = await self.handle_list_tools()
        self.logger.info(f"可用工具: {json.dumps(tools, indent=2, ensure_ascii=False)}")
        
        # 测试SQLMap工具（模拟）
        if "sqlmap_scan" in self.tool_manager.tools:
            test_args = {
                "url": "http://testphp.vulnweb.com/artists.php?artist=1",
                "method": "GET",
                "level": 1,
                "risk": 1
            }
            
            self.logger.info(f"测试SQLMap工具，参数: {test_args}")
            # 注意：实际执行需要sqlmap安装，这里只演示框架
            # result = await self.handle_call_tool("sqlmap_scan", test_args)
            # self.logger.info(f"测试结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        self.logger.info("测试模式完成")


async def main():
    """主函数"""
    # 设置全局日志
    from src.utils.logger import setup_global_logging
    setup_global_logging(level="DEBUG")
    
    server = CTFMCPServer()
    
    try:
        await server.initialize()
        
        # 检查是否以服务器模式运行
        if len(sys.argv) > 1 and sys.argv[1] == "--server":
            await server.run_stdio_server()
        else:
            # 运行测试模式
            await server.run_test()
            
    except Exception as e:
        logger.error(f"MCP服务器运行失败: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    # 运行主函数
    exit_code = asyncio.run(main())
    sys.exit(exit_code)