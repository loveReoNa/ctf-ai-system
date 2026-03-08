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
from src.mcp_server.tools.sqlmap_wrapper import sqlmap_wrapper


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


class SQLMapScanTool(CTFMCPTool):
    """SQLMap扫描工具"""
    
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
                },
                "parameter": {
                    "type": "string",
                    "description": "指定测试参数"
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
            parameter = kwargs.get("parameter")
            
            self.logger.info(f"开始SQLMap扫描: {url}")
            
            # 使用sqlmap_wrapper进行扫描
            scan_options = {
                "level": level,
                "risk": risk,
                "timeout": 300  # 5分钟超时
            }
            
            if method.upper() == "POST" and data:
                scan_options["data"] = data
            
            if parameter:
                scan_options["parameter"] = parameter
            
            # 执行扫描
            result = await sqlmap_wrapper.scan(url, **scan_options)
            
            # 确保结果包含必要的字段
            if "success" not in result:
                result["success"] = True if result.get("return_code", 1) == 0 else False
            
            if "command" not in result:
                cmd = f"sqlmap -u {url} --level={level} --risk={risk} --batch --random-agent --threads=10"
                if parameter:
                    cmd += f" -p {parameter}"
                result["command"] = cmd
            
            self.logger.info(f"SQLMap扫描完成: {url}, 成功: {result.get('success', False)}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"SQLMap执行错误: {e}")
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": str(e),
                "return_code": 1
            }


class SQLMapRequestFileTool(CTFMCPTool):
    """SQLMap请求文件扫描工具"""
    
    def __init__(self):
        super().__init__(
            name="sqlmap_request_file",
            description="使用请求文件进行SQLMap扫描"
        )
        self.sqlmap_path = get_tool_path("sqlmap")
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "request_file": {
                    "type": "string",
                    "description": "请求文件路径"
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
                },
                "parameter": {
                    "type": "string",
                    "description": "指定测试参数"
                }
            },
            "required": ["request_file"]
        }
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """执行SQLMap请求文件扫描"""
        try:
            request_file = kwargs.get("request_file")
            level = kwargs.get("level", 1)
            risk = kwargs.get("risk", 1)
            parameter = kwargs.get("parameter")
            
            self.logger.info(f"开始SQLMap请求文件扫描: {request_file}")
            
            # 使用sqlmap_wrapper进行扫描
            scan_options = {
                "level": level,
                "risk": risk,
                "timeout": 300
            }
            
            if parameter:
                scan_options["parameter"] = parameter
            
            # 执行扫描
            result = await sqlmap_wrapper.scan_with_request_file(request_file, **scan_options)
            
            # 确保结果包含必要的字段
            if "success" not in result:
                result["success"] = True if result.get("return_code", 1) == 0 else False
            
            if "command" not in result:
                cmd = f"sqlmap -r {request_file} --level={level} --risk={risk} --batch --random-agent"
                if parameter:
                    cmd += f" -p {parameter}"
                result["command"] = cmd
            
            self.logger.info(f"SQLMap请求文件扫描完成: {request_file}, 成功: {result.get('success', False)}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"SQLMap请求文件扫描错误: {e}")
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": str(e),
                "return_code": 1
            }


class SQLMapGetDBsTool(CTFMCPTool):
    """SQLMap获取数据库工具"""
    
    def __init__(self):
        super().__init__(
            name="sqlmap_get_dbs",
            description="获取数据库列表"
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
        """获取数据库列表"""
        try:
            url = kwargs.get("url")
            level = kwargs.get("level", 1)
            risk = kwargs.get("risk", 1)
            
            self.logger.info(f"获取数据库列表: {url}")
            
            # 使用sqlmap_wrapper获取数据库
            scan_options = {
                "level": level,
                "risk": risk
            }
            
            databases = await sqlmap_wrapper.get_dbs(url, **scan_options)
            
            result = {
                "success": True,
                "databases": databases,
                "count": len(databases),
                "command": f"sqlmap -u {url} --dbs --level={level} --risk={risk} --batch"
            }
            
            self.logger.info(f"获取数据库列表完成: {url}, 找到 {len(databases)} 个数据库")
            
            return result
            
        except Exception as e:
            self.logger.error(f"获取数据库列表错误: {e}")
            return {
                "success": False,
                "error": str(e),
                "databases": []
            }


class SQLMapGetTablesTool(CTFMCPTool):
    """SQLMap获取表工具"""
    
    def __init__(self):
        super().__init__(
            name="sqlmap_get_tables",
            description="获取数据库表列表"
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
                "database": {
                    "type": "string",
                    "description": "数据库名称"
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
            "required": ["url", "database"]
        }
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """获取表列表"""
        try:
            url = kwargs.get("url")
            database = kwargs.get("database")
            level = kwargs.get("level", 1)
            risk = kwargs.get("risk", 1)
            
            self.logger.info(f"获取表列表: {url}, 数据库: {database}")
            
            # 使用sqlmap_wrapper获取表
            scan_options = {
                "level": level,
                "risk": risk
            }
            
            tables = await sqlmap_wrapper.get_tables(url, database, **scan_options)
            
            result = {
                "success": True,
                "database": database,
                "tables": tables,
                "count": len(tables),
                "command": f"sqlmap -u {url} -D {database} --tables --level={level} --risk={risk} --batch"
            }
            
            self.logger.info(f"获取表列表完成: {database}, 找到 {len(tables)} 个表")
            
            return result
            
        except Exception as e:
            self.logger.error(f"获取表列表错误: {e}")
            return {
                "success": False,
                "error": str(e),
                "database": database,
                "tables": []
            }


class SQLMapGetColumnsTool(CTFMCPTool):
    """SQLMap获取列工具"""
    
    def __init__(self):
        super().__init__(
            name="sqlmap_get_columns",
            description="获取表列列表"
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
                "database": {
                    "type": "string",
                    "description": "数据库名称"
                },
                "table": {
                    "type": "string",
                    "description": "表名称"
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
            "required": ["url", "database", "table"]
        }
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """获取列列表"""
        try:
            url = kwargs.get("url")
            database = kwargs.get("database")
            table = kwargs.get("table")
            level = kwargs.get("level", 1)
            risk = kwargs.get("risk", 1)
            
            self.logger.info(f"获取列列表: {url}, 数据库: {database}, 表: {table}")
            
            # 使用sqlmap_wrapper获取列
            scan_options = {
                "level": level,
                "risk": risk
            }
            
            columns = await sqlmap_wrapper.get_columns(url, database, table, **scan_options)
            
            result = {
                "success": True,
                "database": database,
                "table": table,
                "columns": columns,
                "count": len(columns),
                "command": f"sqlmap -u {url} -D {database} -T {table} --columns --level={level} --risk={risk} --batch"
            }
            
            self.logger.info(f"获取列列表完成: {database}.{table}, 找到 {len(columns)} 个列")
            
            return result
            
        except Exception as e:
            self.logger.error(f"获取列列表错误: {e}")
            return {
                "success": False,
                "error": str(e),
                "database": database,
                "table": table,
                "columns": []
            }


class SQLMapDumpTableTool(CTFMCPTool):
    """SQLMap转储表工具"""
    
    def __init__(self):
        super().__init__(
            name="sqlmap_dump_table",
            description="转储表数据"
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
                "database": {
                    "type": "string",
                    "description": "数据库名称"
                },
                "table": {
                    "type": "string",
                    "description": "表名称"
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
            "required": ["url", "database", "table"]
        }
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """转储表数据"""
        try:
            url = kwargs.get("url")
            database = kwargs.get("database")
            table = kwargs.get("table")
            level = kwargs.get("level", 1)
            risk = kwargs.get("risk", 1)
            
            self.logger.info(f"转储表数据: {url}, 数据库: {database}, 表: {table}")
            
            # 使用sqlmap_wrapper转储表
            scan_options = {
                "level": level,
                "risk": risk
            }
            
            dump_result = await sqlmap_wrapper.dump_table(url, database, table, **scan_options)
            
            # 添加命令信息
            dump_result["command"] = f"sqlmap -u {url} -D {database} -T {table} --dump --level={level} --risk={risk} --batch"
            
            self.logger.info(f"转储表数据完成: {database}.{table}, 成功: {dump_result.get('success', False)}")
            
            return dump_result
            
        except Exception as e:
            self.logger.error(f"转储表数据错误: {e}")
            return {
                "success": False,
                "error": str(e),
                "database": database,
                "table": table,
                "data": []
            }


class SQLMapAutoExploitTool(CTFMCPTool):
    """SQLMap自动利用工具"""
    
    def __init__(self):
        super().__init__(
            name="sqlmap_auto_exploit",
            description="自动利用SQL注入漏洞"
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
        """自动利用SQL注入漏洞"""
        try:
            url = kwargs.get("url")
            level = kwargs.get("level", 1)
            risk = kwargs.get("risk", 1)
            
            self.logger.info(f"开始自动利用SQL注入: {url}")
            
            # 使用sqlmap_wrapper自动利用
            scan_options = {
                "level": level,
                "risk": risk,
                "timeout": 600  # 10分钟超时
            }
            
            exploit_result = await sqlmap_wrapper.auto_exploit(url, **scan_options)
            
            # 添加命令信息
            exploit_result["command"] = f"sqlmap -u {url} --auto-exploit --level={level} --risk={risk} --batch"
            
            self.logger.info(f"自动利用完成: {url}, 成功: {exploit_result.get('success', False)}")
            
            return exploit_result
            
        except Exception as e:
            self.logger.error(f"自动利用错误: {e}")
            return {
                "success": False,
                "error": str(e),
                "target": url,
                "steps": [],
                "databases": [],
                "tables": {},
                "data": {},
                "flag": None
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
        # 注册SQLMap扫描工具
        try:
            sqlmap_scan_tool = SQLMapScanTool()
            self.tools[sqlmap_scan_tool.name] = sqlmap_scan_tool
            self.log_info(f"工具注册成功: {sqlmap_scan_tool.name}")
        except Exception as e:
            self.log_error(f"SQLMap扫描工具注册失败: {e}")
        
        # 注册SQLMap请求文件工具
        try:
            sqlmap_request_file_tool = SQLMapRequestFileTool()
            self.tools[sqlmap_request_file_tool.name] = sqlmap_request_file_tool
            self.log_info(f"工具注册成功: {sqlmap_request_file_tool.name}")
        except Exception as e:
            self.log_error(f"SQLMap请求文件工具注册失败: {e}")
        
        # 注册SQLMap获取数据库工具
        try:
            sqlmap_get_dbs_tool = SQLMapGetDBsTool()
            self.tools[sqlmap_get_dbs_tool.name] = sqlmap_get_dbs_tool
            self.log_info(f"工具注册成功: {sqlmap_get_dbs_tool.name}")
        except Exception as e:
            self.log_error(f"SQLMap获取数据库工具注册失败: {e}")
        
        # 注册SQLMap获取表工具
        try:
            sqlmap_get_tables_tool = SQLMapGetTablesTool()
            self.tools[sqlmap_get_tables_tool.name] = sqlmap_get_tables_tool
            self.log_info(f"工具注册成功: {sqlmap_get_tables_tool.name}")
        except Exception as e:
            self.log_error(f"SQLMap获取表工具注册失败: {e}")
        
        # 注册SQLMap获取列工具
        try:
            sqlmap_get_columns_tool = SQLMapGetColumnsTool()
            self.tools[sqlmap_get_columns_tool.name] = sqlmap_get_columns_tool
            self.log_info(f"工具注册成功: {sqlmap_get_columns_tool.name}")
        except Exception as e:
            self.log_error(f"SQLMap获取列工具注册失败: {e}")
        
        # 注册SQLMap转储表工具
        try:
            sqlmap_dump_table_tool = SQLMapDumpTableTool()
            self.tools[sqlmap_dump_table_tool.name] = sqlmap_dump_table_tool
            self.log_info(f"工具注册成功: {sqlmap_dump_table_tool.name}")
        except Exception as e:
            self.log_error(f"SQLMap转储表工具注册失败: {e}")
        
        # 注册SQLMap自动利用工具
        try:
            sqlmap_auto_exploit_tool = SQLMapAutoExploitTool()
            self.tools[sqlmap_auto_exploit_tool.name] = sqlmap_auto_exploit_tool
            self.log_info(f"工具注册成功: {sqlmap_auto_exploit_tool.name}")
        except Exception as e:
            self.log_error(f"SQLMap自动利用工具注册失败: {e}")
        
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
        
        # 测试SQLMap工具
        if "sqlmap_scan" in self.tool_manager.tools:
            test_args = {
                "url": "http://testphp.vulnweb.com/artists.php?artist=1",
                "method": "GET",
                "level": 1,
                "risk": 1
            }
            
            self.logger.info(f"测试SQLMap工具，参数: {test_args}")
            try:
                # 实际执行测试
                result = await self.handle_call_tool("sqlmap_scan", test_args)
                self.logger.info(f"测试结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
                
                # 检查结果
                if result.get("success", False):
                    self.logger.info("SQLMap工具测试成功")
                else:
                    self.logger.warning(f"SQLMap工具测试失败: {result.get('error', '未知错误')}")
            except Exception as e:
                self.logger.error(f"SQLMap工具测试异常: {e}")
        
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