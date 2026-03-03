#!/usr/bin/env python3
"""
攻击执行引擎
负责执行攻击计划中的步骤，管理执行状态，处理工具调用和结果分析
"""

import asyncio
import json
import re
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from src.utils.logger import logger
from src.mcp_server.server import CTFMCPServer
from src.agents.react_agent import AttackStep, AttackPlan, CTFChallenge


class ExecutionStatus(Enum):
    """执行状态枚举"""
    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 执行中
    SUCCESS = "success"      # 执行成功
    FAILED = "failed"        # 执行失败
    TIMEOUT = "timeout"      # 执行超时
    SKIPPED = "skipped"      # 跳过执行


@dataclass
class ExecutionResult:
    """执行结果"""
    step_id: int
    action: str
    tool: Optional[str]
    status: ExecutionStatus
    output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    execution_time: float = 0.0
    flag_detected: bool = False
    flag: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionContext:
    """执行上下文"""
    plan: AttackPlan
    current_step: int = 0
    results: List[ExecutionResult] = field(default_factory=list)
    flags_found: List[str] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    status: ExecutionStatus = ExecutionStatus.PENDING


class AttackExecutor:
    """攻击执行引擎"""
    
    def __init__(self, mcp_server: Optional[CTFMCPServer] = None):
        """
        初始化攻击执行引擎
        
        Args:
            mcp_server: MCP服务器实例，如果为None则创建新实例
        """
        self.logger = logger.getChild("attack_executor")
        self.mcp_server = mcp_server or CTFMCPServer()
        self.context: Optional[ExecutionContext] = None
        
        # 执行配置
        self.config = {
            "step_timeout": 300,  # 单步超时时间（秒）
            "max_retries": 3,     # 最大重试次数
            "parallel_execution": False,  # 是否并行执行
            "continue_on_failure": False,  # 失败时是否继续
            "flag_patterns": [    # flag匹配模式
                r'flag\{[^}]+\}',
                r'FLAG\{[^}]+\}',
                r'ctf\{[^}]+\}',
                r'CTF\{[^}]+\}',
                r'[A-Za-z0-9]{32}',
                r'[A-Za-z0-9]{64}',
            ],
            "kali_optimizations": True,  # Kali环境优化
            "step_dependencies": True,   # 步骤依赖关系
            "monitoring_interval": 5,    # 监控间隔（秒）
        }
        
        # 工具映射
        self.tool_mapping = {
            "sqlmap_scan": self._execute_sqlmap,
            "nmap_scan": self._execute_nmap,
        }
        
        # 步骤依赖关系
        self.step_dependencies = {}
        
        # 执行监控
        self.monitoring_tasks = []
        
        self.logger.info("攻击执行引擎初始化完成")
    
    async def initialize(self) -> bool:
        """初始化执行引擎"""
        try:
            await self.mcp_server.initialize()
            self.logger.info("MCP服务器初始化完成")
            return True
        except Exception as e:
            self.logger.error(f"MCP服务器初始化失败: {e}")
            return False
    
    async def execute_plan(self, plan: AttackPlan) -> ExecutionContext:
        """
        执行攻击计划
        
        Args:
            plan: 攻击计划
            
        Returns:
            执行上下文
        """
        self.logger.info(f"开始执行攻击计划: {plan.challenge.title}")
        
        # 创建执行上下文
        self.context = ExecutionContext(plan=plan, status=ExecutionStatus.RUNNING)
        
        try:
            # 启动执行监控
            await self._start_monitoring()
            
            # 按顺序执行每个步骤
            for step in plan.steps:
                if self.context.status == ExecutionStatus.FAILED:
                    self.logger.warning("执行失败，跳过后续步骤")
                    break
                
                # 执行单个步骤
                result = await self._execute_step(step)
                self.context.results.append(result)
                self.context.current_step = step.step_id
                
                # 更新步骤状态
                step.success = result.status == ExecutionStatus.SUCCESS
                step.actual_result = json.dumps(result.output, ensure_ascii=False)
                
                # 检查是否找到flag
                if result.flag_detected and result.flag:
                    self.context.flags_found.append(result.flag)
                    self.logger.info(f"找到flag: {result.flag}")
                
                # 如果步骤失败且配置了停止条件，则停止执行
                if result.status == ExecutionStatus.FAILED and not self.config.get("continue_on_failure", False):
                    self.context.status = ExecutionStatus.FAILED
                    break
            
            # 更新执行状态
            if self.context.status == ExecutionStatus.RUNNING:
                if self.context.flags_found:
                    self.context.status = ExecutionStatus.SUCCESS
                else:
                    self.context.status = ExecutionStatus.SUCCESS if any(
                        r.status == ExecutionStatus.SUCCESS for r in self.context.results
                    ) else ExecutionStatus.FAILED
            
            self.context.end_time = time.time()
            
            # 停止监控
            await self._stop_monitoring()
            
            execution_time = self.context.end_time - self.context.start_time
            self.logger.info(f"攻击计划执行完成，状态: {self.context.status.value}, "
                           f"耗时: {execution_time:.2f}秒, "
                           f"找到flag: {len(self.context.flags_found)}个")
            
            return self.context
            
        except Exception as e:
            self.logger.error(f"攻击计划执行异常: {e}")
            self.context.status = ExecutionStatus.FAILED
            self.context.end_time = time.time()
            
            # 确保监控停止
            await self._stop_monitoring()
            
            raise
    
    async def _execute_step(self, step: AttackStep) -> ExecutionResult:
        """
        执行单个攻击步骤
        
        Args:
            step: 攻击步骤
            
        Returns:
            执行结果
        """
        self.logger.info(f"执行步骤 {step.step_id}: {step.action}")
        
        result = ExecutionResult(
            step_id=step.step_id,
            action=step.action,
            tool=step.tool,
            status=ExecutionStatus.PENDING
        )
        
        start_time = time.time()
        
        # 检查步骤依赖关系
        if self.config["step_dependencies"]:
            dependencies_met = await self._check_step_dependencies(step)
            if not dependencies_met:
                result.status = ExecutionStatus.SKIPPED
                result.error = "依赖步骤未完成"
                result.execution_time = time.time() - start_time
                self.logger.warning(f"步骤 {step.step_id} 跳过，依赖未满足")
                return result
        
        # 重试机制
        max_retries = self.config["max_retries"]
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                # 检查是否有工具需要执行
                if step.tool:
                    # 查找对应的工具执行函数
                    if step.tool in self.tool_mapping:
                        tool_func = self.tool_mapping[step.tool]
                        output = await self._execute_with_timeout(tool_func, step.parameters)
                    else:
                        # 使用MCP服务器执行工具
                        output = await self._execute_with_timeout(
                            self.mcp_server.handle_call_tool,
                            step.tool,
                            step.parameters
                        )
                    
                    result.output = output
                    
                    # 检查工具执行是否成功
                    if output.get("success", False):
                        result.status = ExecutionStatus.SUCCESS
                        
                        # 从输出中提取flag
                        flag = self._extract_flag_from_output(output)
                        if flag:
                            result.flag_detected = True
                            result.flag = flag
                            self.logger.info(f"步骤 {step.step_id} 找到flag: {flag}")
                        
                        # 成功，跳出重试循环
                        break
                    else:
                        result.status = ExecutionStatus.FAILED
                        result.error = output.get("error", "工具执行失败")
                        
                        # 如果还有重试机会，继续重试
                        if retry_count < max_retries:
                            retry_count += 1
                            wait_time = 2 ** retry_count  # 指数退避
                            self.logger.info(f"步骤 {step.step_id} 失败，{wait_time}秒后重试 (第{retry_count}次)")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            # 重试次数用完
                            break
                    
                else:
                    # 无工具步骤（如信息分析、手动操作）
                    result.status = ExecutionStatus.SUCCESS
                    result.output = {"message": "无工具步骤执行完成"}
                    self.logger.info(f"步骤 {step.step_id} 完成（无工具）")
                    break
                
            except asyncio.TimeoutError:
                result.status = ExecutionStatus.TIMEOUT
                result.error = f"步骤执行超时（{self.config['step_timeout']}秒）"
                self.logger.warning(f"步骤 {step.step_id} 执行超时")
                
                # 如果还有重试机会，继续重试
                if retry_count < max_retries:
                    retry_count += 1
                    wait_time = 2 ** retry_count
                    self.logger.info(f"步骤 {step.step_id} 超时，{wait_time}秒后重试 (第{retry_count}次)")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    break
                
            except Exception as e:
                result.status = ExecutionStatus.FAILED
                result.error = str(e)
                self.logger.error(f"步骤 {step.step_id} 执行失败: {e}")
                
                # 如果还有重试机会，继续重试
                if retry_count < max_retries:
                    retry_count += 1
                    wait_time = 2 ** retry_count
                    self.logger.info(f"步骤 {step.step_id} 异常，{wait_time}秒后重试 (第{retry_count}次)")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    break
        
        # 计算执行时间
        result.execution_time = time.time() - start_time
        
        # 添加元数据
        result.metadata = {
            "timestamp": time.time(),
            "retry_count": retry_count,
            "step_type": "tool" if step.tool else "manual",
            "dependencies_checked": self.config["step_dependencies"]
        }
        
        self.logger.info(f"步骤 {step.step_id} 执行完成，状态: {result.status.value}, "
                       f"耗时: {result.execution_time:.2f}秒, 重试次数: {retry_count}")
        
        return result
    
    async def _execute_sqlmap(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行SQLMap扫描"""
        try:
            # 调用MCP服务器的SQLMap工具
            result = await self.mcp_server.handle_call_tool("sqlmap_scan", parameters)
            
            # 增强结果分析
            if result.get("success", False):
                # 解析SQLMap输出，提取关键信息
                stdout = result.get("stdout", "")
                stderr = result.get("stderr", "")
                
                # 检查是否发现注入点
                injection_found = any(
                    keyword in stdout.lower() 
                    for keyword in ["injection", "vulnerable", "parameter"]
                )
                
                # 提取数据库信息
                db_match = re.search(r'Database: (.+)', stdout)
                db_type = db_match.group(1) if db_match else "unknown"
                
                # 增强结果
                result["analysis"] = {
                    "injection_found": injection_found,
                    "database_type": db_type,
                    "vulnerability_level": self._assess_sqlmap_vulnerability(stdout)
                }
            
            return result
            
        except Exception as e:
            self.logger.error(f"SQLMap执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": str(e)
            }
    
    async def _execute_nmap(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """执行Nmap扫描"""
        try:
            # 调用MCP服务器的Nmap工具
            result = await self.mcp_server.handle_call_tool("nmap_scan", parameters)
            
            # 增强结果分析
            if result.get("success", False):
                stdout = result.get("stdout", "")
                
                # 解析Nmap输出
                open_ports = self._parse_nmap_ports(stdout)
                services = self._parse_nmap_services(stdout)
                
                # 安全评估
                security_risks = self._assess_nmap_security_risks(open_ports)
                
                # 增强结果
                result["analysis"] = {
                    "open_ports": open_ports,
                    "services": services,
                    "security_risks": security_risks,
                    "total_ports_scanned": len(open_ports)
                }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Nmap执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": str(e)
            }
    
    def _extract_flag_from_output(self, output: Dict[str, Any]) -> Optional[str]:
        """从工具输出中提取flag"""
        if not output:
            return None
        
        # 检查stdout和stderr
        stdout = output.get("stdout", "")
        stderr = output.get("stderr", "")
        combined = stdout + stderr
        
        # 检查所有flag模式
        for pattern in self.config["flag_patterns"]:
            match = re.search(pattern, combined)
            if match:
                return match.group()
        
        # 检查analysis字段
        analysis = output.get("analysis", {})
        if isinstance(analysis, dict):
            analysis_str = json.dumps(analysis)
            for pattern in self.config["flag_patterns"]:
                match = re.search(pattern, analysis_str)
                if match:
                    return match.group()
        
        return None
    
    def _assess_sqlmap_vulnerability(self, output: str) -> str:
        """评估SQLMap发现的漏洞严重性"""
        output_lower = output.lower()
        
        if "critical" in output_lower or "high" in output_lower:
            return "critical"
        elif "medium" in output_lower:
            return "medium"
        elif "low" in output_lower:
            return "low"
        else:
            return "unknown"
    
    def _parse_nmap_ports(self, output: str) -> List[Dict[str, Any]]:
        """解析Nmap端口输出"""
        ports = []
        
        # 匹配端口行，例如: "22/tcp open  ssh"
        port_pattern = r'(\d+)/(tcp|udp)\s+(open|filtered|closed)\s+(.+)'
        
        for line in output.split('\n'):
            match = re.search(port_pattern, line)
            if match:
                port, protocol, state, service = match.groups()
                ports.append({
                    "port": int(port),
                    "protocol": protocol,
                    "state": state,
                    "service": service.strip()
                })
        
        return ports
    
    def _parse_nmap_services(self, output: str) -> List[str]:
        """解析Nmap服务信息"""
        services = []
        
        # 匹配服务版本信息
        service_pattern = r'(\d+)/(tcp|udp).*?([A-Za-z0-9-]+)'
        
        for line in output.split('\n'):
            match = re.search(service_pattern, line)
            if match:
                _, _, service = match.groups()
                if service not in services:
                    services.append(service)
        
        return services
    
    def _assess_nmap_security_risks(self, ports: List[Dict[str, Any]]) -> List[str]:
        """评估Nmap扫描的安全风险"""
        risks = []
        
        # 高风险端口
        high_risk_ports = {
            21: "FTP - 可能存在弱密码或匿名访问",
            22: "SSH - 可能存在弱密码或漏洞",
            23: "Telnet - 明文传输，不安全",
            25: "SMTP - 可能存在配置问题",
            80: "HTTP - 可能存在Web漏洞",
            443: "HTTPS - 可能存在SSL/TLS漏洞",
            3306: "MySQL - 可能存在弱密码",
            3389: "RDP - 可能存在暴力破解风险",
            5900: "VNC - 可能存在弱密码",
        }
        
        for port_info in ports:
            port_num = port_info["port"]
            if port_num in high_risk_ports and port_info["state"] == "open":
                risks.append(f"端口 {port_num} ({port_info['service']}): {high_risk_ports[port_num]}")
        
        return risks
    
    def generate_execution_report(self) -> Dict[str, Any]:
        """生成执行报告"""
        if not self.context:
            return {"error": "没有执行上下文"}
        
        total_time = (self.context.end_time or time.time()) - self.context.start_time
        
        # 统计执行结果
        stats = {
            "total_steps": len(self.context.plan.steps),
            "executed_steps": len(self.context.results),
            "successful_steps": sum(1 for r in self.context.results if r.status == ExecutionStatus.SUCCESS),
            "failed_steps": sum(1 for r in self.context.results if r.status == ExecutionStatus.FAILED),
            "timeout_steps": sum(1 for r in self.context.results if r.status == ExecutionStatus.TIMEOUT),
            "flags_found": len(self.context.flags_found),
            "total_execution_time": total_time,
            "average_step_time": sum(r.execution_time for r in self.context.results) / len(self.context.results) if self.context.results else 0
        }
        
        # 详细步骤结果
        step_details = []
        for result in self.context.results:
            step_details.append({
                "step_id": result.step_id,
                "action": result.action,
                "tool": result.tool,
                "status": result.status.value,
                "execution_time": result.execution_time,
                "flag_detected": result.flag_detected,
                "flag": result.flag,
                "error": result.error
            })
        
        # 安全评估
        security_assessment = self._generate_security_assessment()
        
        return {
            "challenge": {
                "title": self.context.plan.challenge.title,
                "category": self.context.plan.challenge.category,
                "difficulty": self.context.plan.challenge.difficulty,
                "target_url": self.context.plan.challenge.target_url
            },
            "execution_summary": {
                "status": self.context.status.value,
                "start_time": self.context.start_time,
                "end_time": self.context.end_time,
                "total_time": total_time,
                "statistics": stats
            },
            "flags": self.context.flags_found,
            "step_details": step_details,
            "security_assessment": security_assessment,
            "recommendations": self._generate_recommendations(),
            "success": self.context.status == ExecutionStatus.SUCCESS
        }
    
    def _generate_security_assessment(self) -> Dict[str, Any]:
        """生成安全评估"""
        if not self.context:
            return {}
        
        assessment = {
            "vulnerabilities_found": [],
            "risk_level": "low",
            "confidence": 0.0
        }
        
        # 分析执行结果，识别漏洞
        for result in self.context.results:
            if result.tool == "sqlmap_scan" and result.status == ExecutionStatus.SUCCESS:
                analysis = result.output.get("analysis", {})
                if analysis.get("injection_found", False):
                    assessment["vulnerabilities_found"].append({
                        "type": "SQL Injection",
                        "severity": analysis.get("vulnerability_level", "unknown"),
                        "tool": "sqlmap",
                        "step": result.step_id
                    })
            
            elif result.tool == "nmap_scan" and result.status == ExecutionStatus.SUCCESS:
                analysis = result.output.get("analysis", {})
                risks = analysis.get("security_risks", [])
                if risks:
                    assessment["vulnerabilities_found"].extend([
                        {
                            "type": "Open Port Risk",
                            "severity": "medium",
                            "description": risk,
                            "tool": "nmap",
                            "step": result.step_id
                        }
                        for risk in risks
                    ])
        
        # 计算风险等级
        if any(vuln["severity"] == "critical" for vuln in assessment["vulnerabilities_found"]):
            assessment["risk_level"] = "critical"
        elif any(vuln["severity"] == "medium" for vuln in assessment["vulnerabilities_found"]):
            assessment["risk_level"] = "medium"
        elif assessment["vulnerabilities_found"]:
            assessment["risk_level"] = "low"
        
        # 计算置信度
        total_steps = len(self.context.results)
        successful_steps = sum(1 for r in self.context.results if r.status == ExecutionStatus.SUCCESS)
        assessment["confidence"] = successful_steps / total_steps if total_steps > 0 else 0.0
        
        return assessment
    
    def _generate_recommendations(self) -> List[str]:
        """生成安全建议"""
        recommendations = []
        
        if not self.context:
            return recommendations
        
        # 基于执行结果生成建议
        for result in self.context.results:
            if result.tool == "sqlmap_scan" and result.status == ExecutionStatus.SUCCESS:
                analysis = result.output.get("analysis", {})
                if analysis.get("injection_found", False):
                    recommendations.append("发现SQL注入漏洞，建议：")
                    recommendations.append("  - 使用参数化查询或预编译语句")
                    recommendations.append("  - 实施输入验证和过滤")
                    recommendations.append("  - 使用Web应用防火墙(WAF)")
            
            elif result.tool == "nmap_scan" and result.status == ExecutionStatus.SUCCESS:
                analysis = result.output.get("analysis", {})
                risks = analysis.get("security_risks", [])
                if risks:
                    recommendations.append("发现开放端口安全风险，建议：")
                    recommendations.append("  - 关闭不必要的端口")
                    recommendations.append("  - 配置防火墙规则")
                    recommendations.append("  - 使用强密码和双因素认证")
        
        # 通用建议
        if not recommendations:
            recommendations.append("未发现明显安全漏洞，建议：")
            recommendations.append("  - 定期进行安全扫描")
            recommendations.append("  - 保持系统和软件更新")
            recommendations.append("  - 实施安全监控和日志审计")
        
        return recommendations
    
    async def _check_step_dependencies(self, step: AttackStep) -> bool:
        """
        检查步骤依赖关系
        
        Args:
            step: 当前步骤
            
        Returns:
            依赖是否满足
        """
        if not self.context:
            return True
        
        # 简单依赖检查：确保前序步骤成功
        for prev_step in self.context.plan.steps:
            if prev_step.step_id >= step.step_id:
                continue
            
            # 查找前序步骤的执行结果
            prev_result = next(
                (r for r in self.context.results if r.step_id == prev_step.step_id),
                None
            )
            
            if not prev_result:
                return False
            
            if prev_result.status != ExecutionStatus.SUCCESS:
                self.logger.warning(f"步骤 {step.step_id} 依赖步骤 {prev_step.step_id} 未成功")
                return False
        
        return True
    
    async def _execute_with_timeout(self, func, *args, **kwargs) -> Dict[str, Any]:
        """
        带超时的函数执行
        
        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            执行结果
        """
        try:
            return await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config["step_timeout"]
            )
        except asyncio.TimeoutError:
            self.logger.error(f"函数执行超时: {func.__name__}")
            raise
    
    async def _start_monitoring(self):
        """启动执行监控"""
        if not self.config.get("monitoring_interval", 0) > 0:
            return
        
        async def monitor():
            while self.context and self.context.status == ExecutionStatus.RUNNING:
                try:
                    # 监控当前执行状态
                    if self.context:
                        current_step = self.context.current_step
                        total_steps = len(self.context.plan.steps)
                        flags_found = len(self.context.flags_found)
                        
                        self.logger.info(
                            f"执行监控: 步骤 {current_step}/{total_steps}, "
                            f"找到flag: {flags_found}, "
                            f"运行时间: {time.time() - self.context.start_time:.1f}秒"
                        )
                    
                    await asyncio.sleep(self.config["monitoring_interval"])
                except Exception as e:
                    self.logger.error(f"监控任务异常: {e}")
                    break
        
        # 启动监控任务
        task = asyncio.create_task(monitor())
        self.monitoring_tasks.append(task)
    
    async def _stop_monitoring(self):
        """停止执行监控"""
        for task in self.monitoring_tasks:
            task.cancel()
        
        # 等待所有任务完成
        if self.monitoring_tasks:
            await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
            self.monitoring_tasks.clear()


# 示例使用
async def demo_attack_executor():
    """演示攻击执行引擎的使用"""
    from src.agents.react_agent import CTFChallenge, AttackStep, AttackPlan
    
    # 创建示例挑战
    challenge = CTFChallenge(
        id="web-001",
        title="SQL注入挑战",
        description="一个存在SQL注入漏洞的Web应用",
        target_url="http://testphp.vulnweb.com/artists.php?artist=1",
        category="web",
        difficulty="easy",
        hints=["尝试SQL注入", "查看URL参数"],
        expected_flag="flag{sql_injection_success}"
    )
    
    # 创建攻击计划
    plan = AttackPlan(challenge=challenge)
    plan.steps = [
        AttackStep(
            step_id=1,
            action="端口扫描",
            tool="nmap_scan",
            parameters={"target": "testphp.vulnweb.com", "ports": "80,443"},
            reasoning="收集目标信息，识别开放端口",
            expected_result="获取开放端口和服务信息"
        ),
        AttackStep(
            step_id=2,
            action="SQL注入扫描",
            tool="sqlmap_scan",
            parameters={"url": "http://testphp.vulnweb.com/artists.php?artist=1"},
            reasoning="扫描SQL注入漏洞",
            expected_result="识别SQL注入点"
        )
    ]
    
    # 创建执行引擎
    executor = AttackExecutor()
    
    # 初始化
    if not await executor.initialize():
        print("执行引擎初始化失败")
        return
    
    # 执行攻击计划
    print(f"开始执行攻击计划: {challenge.title}")
    context = await executor.execute_plan(plan)
    
    # 生成报告
    report = executor.generate_execution_report()
    
    print("\n" + "="*50)
    print("执行报告:")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("="*50)
    
    return report


if __name__ == "__main__":
    # 运行演示
    asyncio.run(demo_attack_executor())