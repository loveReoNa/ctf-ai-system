#!/usr/bin/env python3
"""
工具链协调器
负责多工具协同执行、依赖管理和结果整合
"""

import asyncio
import json
import time
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from urllib.parse import urlparse

from src.utils.logger import logger
from src.utils.tool_parser import ToolParserFactory
from src.mcp_server.server import CTFMCPServer


class ToolDependencyType(Enum):
    """工具依赖类型"""
    REQUIRED = "required"      # 必须成功
    OPTIONAL = "optional"      # 可选，失败不影响后续
    PARALLEL = "parallel"      # 可并行执行


@dataclass
class ToolDependency:
    """工具依赖关系"""
    source_tool: str           # 依赖的工具
    target_tool: str           # 被依赖的工具
    dependency_type: ToolDependencyType = ToolDependencyType.REQUIRED
    condition: Optional[str] = None  # 依赖条件表达式


@dataclass
class ToolExecutionResult:
    """工具执行结果"""
    tool_name: str
    success: bool
    output: Dict[str, Any]
    execution_time: float
    dependencies: List[str] = field(default_factory=list)
    next_tools: List[str] = field(default_factory=list)  # 后续可执行工具


@dataclass
class ToolChainContext:
    """工具链执行上下文"""
    chain_id: str
    target: str
    tools_executed: List[ToolExecutionResult] = field(default_factory=list)
    current_state: Dict[str, Any] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    flags_found: List[str] = field(default_factory=list)


class ToolChainCoordinator:
    """工具链协调器"""
    
    def __init__(self, mcp_server: Optional[CTFMCPServer] = None):
        self.logger = logger.getChild("tool_coordinator")
        self.mcp_server = mcp_server or CTFMCPServer()
        self.parser_factory = ToolParserFactory()
        
        # 工具依赖图
        self.tool_dependencies: Dict[str, List[ToolDependency]] = {}
        
        # 工具执行策略
        self.execution_strategies = {
            "sequential": self._execute_sequential,
            "parallel": self._execute_parallel,
            "conditional": self._execute_conditional
        }
        
        # 预定义工具链（只包含实际可用的工具）
        self.predefined_chains = {
            "web_recon": ["nmap_scan", "sqlmap_scan"],  # 移除了dirb_scan和xss_scan
            "full_scan": ["nmap_scan", "sqlmap_scan"],  # 移除了nikto_scan和wpscan
            "quick_scan": ["nmap_scan", "sqlmap_scan"]
        }
        
        # 初始化依赖关系
        self._initialize_dependencies()
        
        self.logger.info("工具链协调器初始化完成")
    
    def _initialize_dependencies(self):
        """初始化工具依赖关系"""
        # Nmap -> SQLMap: 端口扫描结果作为SQLMap的输入
        self._add_dependency(
            ToolDependency(
                source_tool="nmap_scan",
                target_tool="sqlmap_scan",
                dependency_type=ToolDependencyType.REQUIRED,
                condition="has_web_ports"
            )
        )
        
        # Nmap -> Dirb: 发现Web端口后执行目录扫描
        self._add_dependency(
            ToolDependency(
                source_tool="nmap_scan",
                target_tool="dirb_scan",
                dependency_type=ToolDependencyType.OPTIONAL,
                condition="port_80_open or port_443_open"
            )
        )
        
        # SQLMap -> XSS扫描: SQL注入成功后尝试XSS
        self._add_dependency(
            ToolDependency(
                source_tool="sqlmap_scan",
                target_tool="xss_scan",
                dependency_type=ToolDependencyType.OPTIONAL,
                condition="sql_injection_found"
            )
        )
    
    def _add_dependency(self, dependency: ToolDependency):
        """添加工具依赖关系"""
        if dependency.source_tool not in self.tool_dependencies:
            self.tool_dependencies[dependency.source_tool] = []
        self.tool_dependencies[dependency.source_tool].append(dependency)
    
    async def initialize(self) -> bool:
        """初始化协调器"""
        try:
            await self.mcp_server.initialize()
            self.logger.info("MCP服务器初始化完成")
            return True
        except Exception as e:
            self.logger.error(f"MCP服务器初始化失败: {e}")
            return False
    
    async def execute_chain(self, chain_name: str, target: str, 
                           strategy: str = "sequential", 
                           custom_params: Optional[Dict[str, Any]] = None) -> ToolChainContext:
        """
        执行预定义工具链
        
        Args:
            chain_name: 工具链名称
            target: 目标（URL或IP）
            strategy: 执行策略（sequential, parallel, conditional）
            custom_params: 自定义参数
            
        Returns:
            工具链执行上下文
        """
        if chain_name not in self.predefined_chains:
            raise ValueError(f"未知的工具链: {chain_name}")
        
        tool_list = self.predefined_chains[chain_name]
        self.logger.info(f"执行工具链 '{chain_name}': {tool_list}")
        
        # 创建执行上下文
        context = ToolChainContext(
            chain_id=f"{chain_name}_{int(time.time())}",
            target=target
        )
        
        # 获取执行策略函数
        if strategy not in self.execution_strategies:
            self.logger.warning(f"未知策略 '{strategy}'，使用默认sequential")
            strategy = "sequential"
        
        strategy_func = self.execution_strategies[strategy]
        
        try:
            # 执行工具链
            await strategy_func(tool_list, target, context, custom_params or {})
            
            # 更新上下文
            context.end_time = time.time()
            
            # 分析结果
            self._analyze_chain_results(context)
            
            execution_time = context.end_time - context.start_time
            self.logger.info(f"工具链执行完成，耗时: {execution_time:.2f}秒，"
                           f"执行工具: {len(context.tools_executed)}个，"
                           f"找到flag: {len(context.flags_found)}个")
            
        except Exception as e:
            self.logger.error(f"工具链执行失败: {e}")
            context.end_time = time.time()
        
        return context
    
    async def _execute_sequential(self, tool_list: List[str], target: str, 
                                 context: ToolChainContext, params: Dict[str, Any]):
        """顺序执行策略"""
        for tool_name in tool_list:
            # 检查依赖关系
            if not await self._check_dependencies(tool_name, context):
                self.logger.warning(f"工具 {tool_name} 依赖未满足，跳过")
                continue
            
            # 执行工具
            result = await self._execute_tool(tool_name, target, context, params)
            context.tools_executed.append(result)
            
            # 更新执行状态
            self._update_execution_state(tool_name, result, context)
            
            # 如果工具失败且是必须的，停止执行
            if not result.success and self._is_required_tool(tool_name):
                self.logger.warning(f"必须工具 {tool_name} 执行失败，停止工具链")
                break
    
    async def _execute_parallel(self, tool_list: List[str], target: str,
                               context: ToolChainContext, params: Dict[str, Any]):
        """并行执行策略"""
        # 分组可并行执行的工具
        parallel_groups = self._group_parallel_tools(tool_list)
        
        for group in parallel_groups:
            # 并行执行组内工具
            tasks = []
            for tool_name in group:
                if await self._check_dependencies(tool_name, context):
                    task = self._execute_tool(tool_name, target, context, params)
                    tasks.append(task)
            
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        self.logger.error(f"工具 {group[i]} 执行异常: {result}")
                        continue
                    
                    context.tools_executed.append(result)
                    self._update_execution_state(group[i], result, context)
    
    async def _execute_conditional(self, tool_list: List[str], target: str,
                                  context: ToolChainContext, params: Dict[str, Any]):
        """条件执行策略"""
        for tool_name in tool_list:
            # 检查执行条件
            if not await self._evaluate_execution_condition(tool_name, context):
                self.logger.info(f"工具 {tool_name} 执行条件不满足，跳过")
                continue
            
            # 检查依赖关系
            if not await self._check_dependencies(tool_name, context):
                self.logger.warning(f"工具 {tool_name} 依赖未满足，跳过")
                continue
            
            # 执行工具
            result = await self._execute_tool(tool_name, target, context, params)
            context.tools_executed.append(result)
            
            # 更新执行状态
            self._update_execution_state(tool_name, result, context)
    
    async def _execute_tool(self, tool_name: str, target: str,
                           context: ToolChainContext, params: Dict[str, Any]) -> ToolExecutionResult:
        """执行单个工具"""
        self.logger.info(f"执行工具: {tool_name}, 目标: {target}")
        
        start_time = time.time()
        
        try:
            # 构建工具参数
            tool_params = self._build_tool_parameters(tool_name, target, context, params)
            
            # 调用MCP服务器执行工具
            raw_result = await self.mcp_server.handle_call_tool(tool_name, tool_params)
            
            # 解析工具输出
            parsed_result = self.parser_factory.parse_tool_output(tool_name, raw_result.get("stdout", ""))
            
            # 检查是否找到flag
            flag = self._extract_flag_from_result(parsed_result)
            if flag:
                context.flags_found.append(flag)
                self.logger.info(f"工具 {tool_name} 找到flag: {flag}")
            
            # 获取依赖关系
            dependencies = self._get_tool_dependencies(tool_name)
            next_tools = self._get_next_tools(tool_name, parsed_result)
            
            execution_time = time.time() - start_time
            
            result = ToolExecutionResult(
                tool_name=tool_name,
                success=raw_result.get("success", False) and parsed_result.get("success", False),
                output={
                    "raw": raw_result,
                    "parsed": parsed_result
                },
                execution_time=execution_time,
                dependencies=dependencies,
                next_tools=next_tools
            )
            
            self.logger.info(f"工具 {tool_name} 执行完成，"
                           f"成功: {result.success}, 耗时: {execution_time:.2f}秒")
            
            return result
            
        except Exception as e:
            self.logger.error(f"工具 {tool_name} 执行失败: {e}")
            
            execution_time = time.time() - start_time
            
            return ToolExecutionResult(
                tool_name=tool_name,
                success=False,
                output={"error": str(e)},
                execution_time=execution_time,
                dependencies=[],
                next_tools=[]
            )
    
    def _parse_target_url(self, target: str) -> Dict[str, Any]:
        """解析目标URL，提取主机名和端口"""
        result = {
            "original": target,
            "hostname": target,
            "port": None,
            "is_url": False
        }
        
        # 检查是否是URL格式
        if target.startswith(("http://", "https://")):
            result["is_url"] = True
            try:
                parsed = urlparse(target)
                result["hostname"] = parsed.hostname or target
                result["port"] = parsed.port
                
                # 如果没有端口但有协议，设置默认端口
                if not result["port"]:
                    if parsed.scheme == "https":
                        result["port"] = 443
                    elif parsed.scheme == "http":
                        result["port"] = 80
            except Exception as e:
                self.logger.warning(f"URL解析失败: {e}")
        
        # 如果不是URL，尝试从字符串中提取主机名和端口
        else:
            # 检查是否有端口号（格式如: hostname:port）
            match = re.match(r'^([^:]+):(\d+)$', target)
            if match:
                result["hostname"] = match.group(1)
                result["port"] = int(match.group(2))
        
        return result
    
    def _build_tool_parameters(self, tool_name: str, target: str,
                              context: ToolChainContext, params: Dict[str, Any]) -> Dict[str, Any]:
        """构建工具参数"""
        # 解析目标
        target_info = self._parse_target_url(target)
        
        # 根据工具类型构建参数
        if tool_name == "nmap_scan":
            # Nmap需要主机名，而不是完整的URL
            base_params = {"target": target_info["hostname"]}
            
            # 如果有特定端口，添加到扫描端口
            ports = params.get("nmap_ports", "80,443,8080,8443")
            if target_info["port"]:
                # 将特定端口添加到扫描列表中
                port_list = ports.split(",")
                if str(target_info["port"]) not in port_list:
                    port_list.append(str(target_info["port"]))
                ports = ",".join(port_list)
            
            base_params.update({
                "ports": ports,
                "scan_type": params.get("nmap_scan_type", "syn")
            })
            
        elif tool_name == "sqlmap_scan":
            # SQLMap需要完整的URL
            url = self._extract_url_from_context(context, target)
            if not url and target_info["is_url"]:
                url = target
            elif not url:
                # 构建默认URL
                port_suffix = f":{target_info['port']}" if target_info["port"] else ""
                url = f"http://{target_info['hostname']}{port_suffix}"
            
            base_params = {
                "target": target_info["hostname"],  # 保持向后兼容
                "url": url
            }
            base_params.update({
                "method": params.get("sqlmap_method", "GET"),
                "level": params.get("sqlmap_level", 1),
                "risk": params.get("sqlmap_risk", 1)
            })
        else:
            base_params = {"target": target}
        
        # 合并自定义参数
        if tool_name in params:
            base_params.update(params[tool_name])
        
        return base_params
    
    def _extract_url_from_context(self, context: ToolChainContext, target: str) -> Optional[str]:
        """从上下文中提取URL"""
        # 首先解析目标
        target_info = self._parse_target_url(target)
        
        # 查找之前的Nmap扫描结果
        for result in context.tools_executed:
            if result.tool_name == "nmap_scan" and result.success:
                parsed = result.output.get("parsed", {})
                if parsed.get("success", False):
                    # 检查是否有Web端口
                    hosts = parsed.get("hosts", [])
                    for host in hosts:
                        ports = host.get("ports", [])
                        for port in ports:
                            if port.get("port") in [80, 443, 8080, 8443] and port.get("state") == "open":
                                protocol = "https" if port["port"] in [443, 8443] else "http"
                                port_num = port["port"]
                                # 如果目标已经有端口，使用目标的端口
                                if target_info["port"]:
                                    port_num = target_info["port"]
                                return f"{protocol}://{target_info['hostname']}:{port_num}"
        
        # 如果没有找到，使用解析后的信息构建URL
        if target_info["is_url"]:
            return target
        else:
            port_suffix = f":{target_info['port']}" if target_info["port"] else ""
            return f"http://{target_info['hostname']}{port_suffix}"
    
    async def _check_dependencies(self, tool_name: str, context: ToolChainContext) -> bool:
        """检查工具依赖关系"""
        # 查找所有以当前工具为目标工具的依赖关系
        # 即检查哪些工具需要在当前工具之前执行
        required_dependencies = []
        
        for source_tool, deps in self.tool_dependencies.items():
            for dep in deps:
                if dep.target_tool == tool_name:
                    required_dependencies.append((source_tool, dep))
        
        # 如果没有依赖关系，直接返回True
        if not required_dependencies:
            return True
        
        # 检查所有依赖关系
        for source_tool, dep in required_dependencies:
            # 查找依赖工具的执行结果
            dep_result = next(
                (r for r in context.tools_executed if r.tool_name == source_tool),
                None
            )
            
            if not dep_result:
                self.logger.warning(f"依赖工具 {source_tool} 未执行")
                return False
            
            if not dep_result.success and dep.dependency_type == ToolDependencyType.REQUIRED:
                self.logger.warning(f"必须依赖工具 {source_tool} 执行失败")
                return False
            
            # 检查条件
            if dep.condition and not self._evaluate_condition(dep.condition, dep_result, context):
                self.logger.info(f"依赖条件不满足: {dep.condition}")
                if dep.dependency_type == ToolDependencyType.REQUIRED:
                    return False
        
        return True
    
    def _evaluate_condition(self, condition: str, result: ToolExecutionResult, 
                           context: ToolChainContext) -> bool:
        """评估条件表达式"""
        try:
            # 简单的条件评估
            if condition == "has_web_ports":
                parsed = result.output.get("parsed", {})
                if parsed.get("success", False):
                    hosts = parsed.get("hosts", [])
                    for host in hosts:
                        ports = host.get("ports", [])
                        for port in ports:
                            if port.get("port") in [80, 443, 8080, 8443] and port.get("state") == "open":
                                return True
                return False
            
            elif condition == "sql_injection_found":
                parsed = result.output.get("parsed", {})
                if parsed.get("success", False):
                    vulnerabilities = parsed.get("vulnerabilities", [])
                    return len(vulnerabilities) > 0
                return False
            
            elif condition == "port_80_open" or condition == "port_443_open":
                port_num = 80 if condition == "port_80_open" else 443
                parsed = result.output.get("parsed", {})
                if parsed.get("success", False):
                    hosts = parsed.get("hosts", [])
                    for host in hosts:
                        ports = host.get("ports", [])
                        for port in ports:
                            if port.get("port") == port_num and port.get("state") == "open":
                                return True
                return False
            
            # 默认返回True
            return True
            
        except Exception as e:
            self.logger.error(f"条件评估失败: {condition}, 错误: {e}")
            return False
    
    async def _evaluate_execution_condition(self, tool_name: str, context: ToolChainContext) -> bool:
        """评估工具执行条件"""
        # 简单的执行条件逻辑
        if tool_name == "sqlmap_scan":
            # 只有在发现Web端口时才执行SQLMap
            for result in context.tools_executed:
                if result.tool_name == "nmap_scan" and result.success:
                    return self._evaluate_condition("has_web_ports", result, context)
            return False
        
        return True
    
    def _group_parallel_tools(self, tool_list: List[str]) -> List[List[str]]:
        """分组可并行执行的工具"""
        # 简单的分组策略：无依赖关系的工具可以并行
        groups = []
        current_group = []
        
        for tool in tool_list:
            # 检查是否有依赖关系
            has_deps = tool in self.tool_dependencies and any(
                dep.dependency_type == ToolDependencyType.REQUIRED 
                for dep in self.tool_dependencies[tool]
            )
            
            if has_deps and current_group:
                groups.append(current_group)
                current_group = [tool]
            else:
                current_group.append(tool)
        
        if current_group:
            groups.append(current_group)
        
        return groups
    
    def _update_execution_state(self, tool_name: str, result: ToolExecutionResult, 
                               context: ToolChainContext):
        """更新执行状态"""
        # 更新当前状态
        context.current_state[tool_name] = {
            "success": result.success,
            "execution_time": result.execution_time,
            "timestamp": time.time()
        }
        
        # 从结果中提取有用信息
        if result.success:
            parsed = result.output.get("parsed", {})
            if parsed.get("success", False):
                # 存储关键信息
                if tool_name == "nmap_scan":
                    context.current_state["open_ports"] = parsed.get("summary", {}).get("open_ports", 0)
                    context.current_state["services"] = parsed.get("summary", {}).get("services_found", [])
                elif tool_name == "sqlmap_scan":
                    context.current_state["sql_injection_found"] = len(parsed.get("vulnerabilities", [])) > 0
    
    def _is_required_tool(self, tool_name: str) -> bool:
        """检查是否是必须工具"""
        # 基础工具通常是必须的
        required_tools = ["nmap_scan", "sqlmap_scan"]
        return tool_name in required_tools
    
    def _get_tool_dependencies(self, tool_name: str) -> List[str]:
        """获取工具依赖"""
        if tool_name in self.tool_dependencies:
            return [dep.source_tool for dep in self.tool_dependencies[tool_name]]
        return []
    
    def _get_next_tools(self, tool_name: str, result: Dict[str, Any]) -> List[str]:
        """获取后续可执行工具"""
        next_tools = []
        
        if tool_name == "nmap_scan" and result.get("success", False):
            # 如果发现Web端口，建议执行Web扫描工具
            if self._evaluate_condition("has_web_ports", 
                                       ToolExecutionResult(tool_name="", success=True, output={"parsed": result}, execution_time=0), 
                                       ToolChainContext(chain_id="", target="")):
                next_tools.extend(["sqlmap_scan", "dirb_scan", "nikto_scan"])
        
        elif tool_name == "sqlmap_scan" and result.get("success", False):
            # 如果发现SQL注入，建议执行进一步利用
            if self._evaluate_condition("sql_injection_found",
                                       ToolExecutionResult(tool_name="", success=True, output={"parsed": result}, execution_time=0),
                                       ToolChainContext(chain_id="", target="")):
                next_tools.extend(["sqlmap_data_dump", "sqlmap_shell"])
        
        return next_tools
    
    def _extract_flag_from_result(self, result: Dict[str, Any]) -> Optional[str]:
        """从结果中提取flag"""
        # 检查常见flag模式
        flag_patterns = [
            r'flag\{[^}]+\}',
            r'FLAG\{[^}]+\}',
            r'ctf\{[^}]+\}',
            r'CTF\{[^}]+\}',
            r'[A-Za-z0-9]{32}',
            r'[A-Za-z0-9]{64}',
        ]
        
        import re
        
        # 检查stdout
        stdout = result.get("stdout", "")
        if isinstance(stdout, dict):
            stdout = json.dumps(stdout)
        
        for pattern in flag_patterns:
            match = re.search(pattern, stdout)
            if match:
                return match.group()
        
        # 检查其他字段
        for key, value in result.items():
            if isinstance(value, str):
                for pattern in flag_patterns:
                    match = re.search(pattern, value)
                    if match:
                        return match.group()
        
        return None
    
    def _analyze_chain_results(self, context: ToolChainContext):
        """分析工具链结果"""
        if not context.tools_executed:
            return
        
        # 计算统计信息
        total_tools = len(context.tools_executed)
        successful_tools = sum(1 for r in context.tools_executed if r.success)
        total_time = sum(r.execution_time for r in context.tools_executed)
        
        # 生成摘要
        context.current_state["chain_summary"] = {
            "total_tools": total_tools,
            "successful_tools": successful_tools,
            "success_rate": successful_tools / total_tools if total_tools > 0 else 0,
            "total_execution_time": total_time,
            "average_tool_time": total_time / total_tools if total_tools > 0 else 0,
            "flags_found": len(context.flags_found)
        }
        
        self.logger.info(f"工具链分析完成: {context.current_state['chain_summary']}")
    
    def generate_chain_report(self, context: ToolChainContext) -> Dict[str, Any]:
        """生成工具链执行报告"""
        if not context.tools_executed:
            return {"error": "没有执行结果"}
        
        total_time = (context.end_time or time.time()) - context.start_time
        
        # 工具执行详情
        tool_details = []
        for result in context.tools_executed:
            tool_details.append({
                "tool": result.tool_name,
                "success": result.success,
                "execution_time": result.execution_time,
                "dependencies": result.dependencies,
                "next_tools": result.next_tools,
                "output_summary": {
                    "success": result.output.get("parsed", {}).get("success", False),
                    "message": result.output.get("parsed", {}).get("message", "")
                }
            })
        
        # 安全评估
        security_assessment = self._generate_security_assessment(context)
        
        return {
            "chain_id": context.chain_id,
            "target": context.target,
            "execution_summary": {
                "start_time": context.start_time,
                "end_time": context.end_time,
                "total_time": total_time,
                "tools_executed": len(context.tools_executed),
                "tools_successful": sum(1 for r in context.tools_executed if r.success),
                "flags_found": context.flags_found,
                "chain_summary": context.current_state.get("chain_summary", {})
            },
            "tool_details": tool_details,
            "security_assessment": security_assessment,
            "recommendations": self._generate_recommendations(context),
            "success": any(r.success for r in context.tools_executed)
        }
    
    def _generate_security_assessment(self, context: ToolChainContext) -> Dict[str, Any]:
        """生成安全评估"""
        assessment = {
            "vulnerabilities": [],
            "risk_level": "low",
            "confidence": 0.0
        }
        
        for result in context.tools_executed:
            if result.success:
                parsed = result.output.get("parsed", {})
                
                if result.tool_name == "sqlmap_scan" and parsed.get("success", False):
                    vulns = parsed.get("vulnerabilities", [])
                    for vuln in vulns:
                        assessment["vulnerabilities"].append({
                            "type": "SQL Injection",
                            "severity": vuln.get("severity", "medium"),
                            "tool": "sqlmap",
                            "description": vuln.get("description", "")
                        })
                
                elif result.tool_name == "nmap_scan" and parsed.get("success", False):
                    # 检查高风险端口
                    hosts = parsed.get("hosts", [])
                    for host in hosts:
                        ports = host.get("ports", [])
                        for port in ports:
                            if port.get("state") == "open":
                                port_num = port.get("port", 0)
                                if port_num in [21, 22, 23, 25, 80, 443, 3306, 3389, 5900]:
                                    assessment["vulnerabilities"].append({
                                        "type": "Open Port Risk",
                                        "severity": "medium",
                                        "tool": "nmap",
                                        "description": f"开放端口 {port_num} ({port.get('service', 'unknown')})"
                                    })
        
        # 确定风险等级
        if any(v["severity"] == "critical" for v in assessment["vulnerabilities"]):
            assessment["risk_level"] = "critical"
        elif any(v["severity"] == "high" for v in assessment["vulnerabilities"]):
            assessment["risk_level"] = "high"
        elif any(v["severity"] == "medium" for v in assessment["vulnerabilities"]):
            assessment["risk_level"] = "medium"
        elif assessment["vulnerabilities"]:
            assessment["risk_level"] = "low"
        
        # 计算置信度
        if context.tools_executed:
            successful_tools = sum(1 for r in context.tools_executed if r.success)
            assessment["confidence"] = successful_tools / len(context.tools_executed)
        
        return assessment
    
    def _generate_recommendations(self, context: ToolChainContext) -> List[str]:
        """生成安全建议"""
        recommendations = []
        
        # 基于漏洞生成建议
        vulnerabilities_found = False
        
        for result in context.tools_executed:
            if result.tool_name == "sqlmap_scan" and result.success:
                parsed = result.output.get("parsed", {})
                if parsed.get("success", False) and parsed.get("vulnerabilities"):
                    vulnerabilities_found = True
                    recommendations.append("发现SQL注入漏洞，建议：")
                    recommendations.append("  - 使用参数化查询或预编译语句")
                    recommendations.append("  - 实施输入验证和过滤")
                    recommendations.append("  - 部署Web应用防火墙(WAF)")
            
            elif result.tool_name == "nmap_scan" and result.success:
                parsed = result.output.get("parsed", {})
                if parsed.get("success", False):
                    hosts = parsed.get("hosts", [])
                    for host in hosts:
                        ports = host.get("ports", [])
                        risky_ports = [p for p in ports if p.get("state") == "open" and p.get("port") in [21, 22, 23, 25, 3389]]
                        if risky_ports:
                            vulnerabilities_found = True
                            recommendations.append("发现高风险开放端口，建议：")
                            recommendations.append("  - 关闭不必要的服务端口")
                            recommendations.append("  - 配置防火墙规则限制访问")
                            recommendations.append("  - 使用强密码和双因素认证")
                            break
        
        # 通用建议
        if not vulnerabilities_found:
            recommendations.append("未发现明显安全漏洞，建议：")
            recommendations.append("  - 定期进行安全扫描和渗透测试")
            recommendations.append("  - 保持系统和应用程序更新")
            recommendations.append("  - 实施安全监控和日志审计")
        
        return recommendations


# 示例使用
async def demo_tool_chain():
    """演示工具链协调器的使用"""
    coordinator = ToolChainCoordinator()
    
    if not await coordinator.initialize():
        print("工具链协调器初始化失败")
        return
    
    # 执行Web侦察工具链
    print("执行Web侦察工具链...")
    context = await coordinator.execute_chain(
        chain_name="web_recon",
        target="testphp.vulnweb.com",
        strategy="sequential"
    )
    
    # 生成报告
    report = coordinator.generate_chain_report(context)
    
    print("\n" + "="*50)
    print("工具链执行报告:")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("="*50)
    
    return report


if __name__ == "__main__":
    # 运行演示
    asyncio.run(demo_tool_chain())