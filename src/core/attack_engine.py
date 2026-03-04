#!/usr/bin/env python3
"""
攻击执行引擎
负责协调AI代理、工具链和攻击执行的核心引擎
"""

import asyncio
import json
import re
import time
import uuid
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from src.utils.logger import logger
from src.utils.tool_coordinator import ToolChainCoordinator, ToolChainContext
from src.utils.deepseek_client import DeepSeekClient
from src.utils.config_manager import ConfigManager


class AttackPhase(Enum):
    """攻击阶段"""
    RECONNAISSANCE = "reconnaissance"      # 侦察
    VULNERABILITY_ANALYSIS = "vulnerability_analysis"  # 漏洞分析
    EXPLOITATION = "exploitation"          # 利用
    POST_EXPLOITATION = "post_exploitation"  # 后利用
    REPORTING = "reporting"                # 报告


class AttackStatus(Enum):
    """攻击状态"""
    PENDING = "pending"        # 等待中
    RUNNING = "running"        # 运行中
    PAUSED = "paused"          # 暂停
    COMPLETED = "completed"    # 完成
    FAILED = "failed"          # 失败
    CANCELLED = "cancelled"    # 取消


@dataclass
class AttackStep:
    """攻击步骤"""
    step_id: str
    phase: AttackPhase
    description: str
    tool_name: Optional[str] = None
    tool_parameters: Dict[str, Any] = field(default_factory=dict)
    status: AttackStatus = AttackStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    next_steps: List[str] = field(default_factory=list)  # 后续步骤ID


@dataclass
class AttackPlan:
    """攻击计划"""
    plan_id: str
    target: str
    description: str
    steps: List[AttackStep] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: Optional[float] = None
    status: AttackStatus = AttackStatus.PENDING
    current_step_index: int = 0
    flags_found: List[str] = field(default_factory=list)
    vulnerabilities_found: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class AttackContext:
    """攻击上下文"""
    attack_id: str
    target: str
    plan: AttackPlan
    current_phase: AttackPhase = AttackPhase.RECONNAISSANCE
    execution_history: List[Dict[str, Any]] = field(default_factory=list)
    collected_data: Dict[str, Any] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    success: bool = False


class AttackExecutionEngine:
    """攻击执行引擎"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = logger.getChild("attack_engine")
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.to_dict()
        
        # 初始化组件
        self.ai_client = DeepSeekClient(self.config)
        self.tool_coordinator = ToolChainCoordinator()
        
        # 攻击状态跟踪
        self.active_attacks: Dict[str, AttackContext] = {}
        self.attack_history: List[AttackContext] = []
        
        # 性能指标
        self.metrics = {
            "total_attacks": 0,
            "successful_attacks": 0,
            "failed_attacks": 0,
            "average_execution_time": 0.0,
            "flags_found_total": 0
        }
        
        # 记录启动时间
        self.start_time = time.time()
        
        self.logger.info("攻击执行引擎初始化完成")
    
    async def initialize(self) -> bool:
        """初始化引擎"""
        try:
            # 初始化AI客户端
            if not await self.ai_client.initialize():
                self.logger.error("AI客户端初始化失败")
                return False
            
            # 初始化工具协调器
            if not await self.tool_coordinator.initialize():
                self.logger.warning("工具协调器初始化失败，继续运行")
            
            self.logger.info("攻击执行引擎初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"攻击执行引擎初始化失败: {e}")
            return False
    
    async def create_attack_plan(self, target: str, description: str = "") -> AttackPlan:
        """
        创建攻击计划
        
        Args:
            target: 攻击目标（URL或IP）
            description: 攻击描述
            
        Returns:
            攻击计划
        """
        plan_id = f"plan_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        self.logger.info(f"创建攻击计划: {plan_id}, 目标: {target}")
        
        # 使用AI生成攻击计划
        ai_plan = await self._generate_ai_attack_plan(target, description)
        
        # 转换为攻击步骤
        steps = self._convert_ai_plan_to_steps(ai_plan)
        
        plan = AttackPlan(
            plan_id=plan_id,
            target=target,
            description=description or f"针对 {target} 的攻击",
            steps=steps,
            status=AttackStatus.PENDING
        )
        
        self.logger.info(f"攻击计划创建完成，包含 {len(steps)} 个步骤")
        return plan
    
    async def _generate_ai_attack_plan(self, target: str, description: str) -> Dict[str, Any]:
        """使用AI生成攻击计划"""
        prompt = f"""
        作为网络安全专家，请为以下目标制定详细的攻击计划：
        
        目标: {target}
        描述: {description}
        
        请按照以下阶段制定计划：
        1. 侦察阶段：信息收集，端口扫描，服务识别
        2. 漏洞分析阶段：漏洞扫描，弱点识别
        3. 利用阶段：漏洞利用，权限提升
        4. 后利用阶段：数据提取，持久化访问
        5. 报告阶段：结果整理，报告生成
        
        请为每个阶段推荐具体的工具和步骤，考虑使用以下工具：
        - Nmap (端口扫描)
        - SQLMap (SQL注入检测)
        - Nikto (Web漏洞扫描)
        - Dirb/Dirbuster (目录爆破)
        - 其他相关工具
        
        请以JSON格式返回计划，包含以下字段：
        - phases: 各阶段列表
        - tools: 推荐工具列表
        - steps: 详细步骤列表
        - estimated_time: 预计执行时间（分钟）
        - risk_level: 风险等级（low/medium/high）
        """
        
        try:
            response = await self.ai_client.generate_response(prompt)
            
            # 尝试解析JSON响应
            try:
                plan = json.loads(response)
            except json.JSONDecodeError:
                # 如果响应不是JSON，尝试提取JSON部分
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    plan = json.loads(json_match.group())
                else:
                    # 创建默认计划
                    plan = self._create_default_attack_plan(target)
            
            return plan
            
        except Exception as e:
            self.logger.error(f"AI生成攻击计划失败: {e}")
            return self._create_default_attack_plan(target)
    
    def _create_default_attack_plan(self, target: str) -> Dict[str, Any]:
        """创建默认攻击计划"""
        return {
            "phases": [
                {
                    "name": "侦察阶段",
                    "description": "信息收集和端口扫描",
                    "tools": ["nmap_scan"],
                    "steps": [
                        "执行Nmap端口扫描",
                        "识别开放端口和服务",
                        "收集Web服务器信息"
                    ]
                },
                {
                    "name": "漏洞分析阶段",
                    "description": "Web漏洞扫描",
                    "tools": ["nikto_scan", "dirb_scan"],
                    "steps": [
                        "执行Nikto漏洞扫描",
                        "执行目录爆破",
                        "识别潜在漏洞"
                    ]
                },
                {
                    "name": "利用阶段",
                    "description": "SQL注入检测",
                    "tools": ["sqlmap_scan"],
                    "steps": [
                        "检测SQL注入漏洞",
                        "尝试利用漏洞",
                        "提取数据库信息"
                    ]
                }
            ],
            "tools": ["nmap_scan", "nikto_scan", "dirb_scan", "sqlmap_scan"],
            "steps": [
                "执行Nmap端口扫描",
                "执行Nikto漏洞扫描",
                "执行目录爆破",
                "检测SQL注入漏洞"
            ],
            "estimated_time": 30,
            "risk_level": "medium"
        }
    
    def _convert_ai_plan_to_steps(self, ai_plan: Dict[str, Any]) -> List[AttackStep]:
        """将AI计划转换为攻击步骤"""
        steps = []
        
        # 提取阶段信息
        phases = ai_plan.get("phases", [])
        tool_mapping = {
            "nmap_scan": ("Nmap端口扫描", AttackPhase.RECONNAISSANCE),
            "nikto_scan": ("Nikto漏洞扫描", AttackPhase.VULNERABILITY_ANALYSIS),
            "dirb_scan": ("Dirb目录爆破", AttackPhase.VULNERABILITY_ANALYSIS),
            "sqlmap_scan": ("SQLMap注入检测", AttackPhase.EXPLOITATION)
        }
        
        step_counter = 0
        
        for phase in phases:
            phase_name = phase.get("name", "")
            phase_tools = phase.get("tools", [])
            
            for tool in phase_tools:
                step_counter += 1
                step_id = f"step_{step_counter}"
                
                # 获取工具描述和阶段
                tool_desc, tool_phase = tool_mapping.get(tool, (f"执行{tool}", AttackPhase.RECONNAISSANCE))
                
                step = AttackStep(
                    step_id=step_id,
                    phase=tool_phase,
                    description=f"{phase_name}: {tool_desc}",
                    tool_name=tool,
                    tool_parameters={},
                    status=AttackStatus.PENDING
                )
                
                steps.append(step)
        
        # 如果没有步骤，创建默认步骤
        if not steps:
            steps = [
                AttackStep(
                    step_id="step_1",
                    phase=AttackPhase.RECONNAISSANCE,
                    description="Nmap端口扫描",
                    tool_name="nmap_scan",
                    status=AttackStatus.PENDING
                ),
                AttackStep(
                    step_id="step_2",
                    phase=AttackPhase.VULNERABILITY_ANALYSIS,
                    description="Nikto漏洞扫描",
                    tool_name="nikto_scan",
                    status=AttackStatus.PENDING
                ),
                AttackStep(
                    step_id="step_3",
                    phase=AttackPhase.EXPLOITATION,
                    description="SQLMap注入检测",
                    tool_name="sqlmap_scan",
                    status=AttackStatus.PENDING
                )
            ]
        
        # 设置步骤依赖关系
        for i in range(len(steps) - 1):
            steps[i].next_steps = [steps[i + 1].step_id]
        
        return steps
    
    async def execute_attack(self, plan: AttackPlan) -> AttackContext:
        """
        执行攻击计划
        
        Args:
            plan: 攻击计划
            
        Returns:
            攻击上下文
        """
        attack_id = f"attack_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        context = AttackContext(
            attack_id=attack_id,
            target=plan.target,
            plan=plan
        )
        
        # 记录攻击开始
        self.active_attacks[attack_id] = context
        self.metrics["total_attacks"] += 1
        
        self.logger.info(f"开始执行攻击: {attack_id}, 目标: {plan.target}")
        
        try:
            # 更新计划状态
            plan.status = AttackStatus.RUNNING
            plan.updated_at = time.time()
            
            # 执行攻击步骤
            await self._execute_attack_steps(context)
            
            # 攻击完成
            context.end_time = time.time()
            context.success = True
            
            plan.status = AttackStatus.COMPLETED
            plan.updated_at = time.time()
            
            self.metrics["successful_attacks"] += 1
            self.metrics["flags_found_total"] += len(plan.flags_found)
            
            execution_time = context.end_time - context.start_time
            self.metrics["average_execution_time"] = (
                (self.metrics["average_execution_time"] * (self.metrics["successful_attacks"] - 1) + execution_time) /
                self.metrics["successful_attacks"]
            )
            
            self.logger.info(f"攻击执行完成: {attack_id}, 耗时: {execution_time:.2f}秒")
            
        except Exception as e:
            self.logger.error(f"攻击执行失败: {attack_id}, 错误: {e}")
            
            context.end_time = time.time()
            context.success = False
            
            plan.status = AttackStatus.FAILED
            plan.updated_at = time.time()
            
            self.metrics["failed_attacks"] += 1
            
        finally:
            # 从活动攻击中移除，添加到历史记录
            self.active_attacks.pop(attack_id, None)
            self.attack_history.append(context)
            
            # 生成最终报告
            await self._generate_attack_report(context)
        
        return context
    
    async def _execute_attack_steps(self, context: AttackContext):
        """执行攻击步骤"""
        plan = context.plan
        
        for i, step in enumerate(plan.steps):
            # 更新当前步骤索引
            plan.current_step_index = i
            
            # 执行步骤
            await self._execute_attack_step(context, step)
            
            # 检查是否应该继续
            if step.status == AttackStatus.FAILED and self._is_critical_step(step):
                self.logger.warning(f"关键步骤失败，停止攻击: {step.step_id}")
                break
            
            # 短暂暂停，避免过快执行
            await asyncio.sleep(1)
    
    async def _execute_attack_step(self, context: AttackContext, step: AttackStep):
        """执行单个攻击步骤"""
        self.logger.info(f"执行攻击步骤: {step.step_id} - {step.description}")
        
        step.start_time = time.time()
        step.status = AttackStatus.RUNNING
        
        try:
            if step.tool_name:
                # 执行工具
                result = await self._execute_tool_step(context, step)
                step.result = result
                
                # 检查是否找到flag
                if result.get("success", False):
                    flags = self._extract_flags_from_result(result)
                    if flags:
                        context.plan.flags_found.extend(flags)
                        self.logger.info(f"步骤 {step.step_id} 找到flag: {flags}")
                    
                    # 提取漏洞信息
                    vulnerabilities = self._extract_vulnerabilities_from_result(result)
                    if vulnerabilities:
                        context.plan.vulnerabilities_found.extend(vulnerabilities)
                
                step.status = AttackStatus.COMPLETED if result.get("success", False) else AttackStatus.FAILED
            
            else:
                # 非工具步骤（如分析、等待等）
                await asyncio.sleep(2)  # 模拟执行
                step.result = {"message": "步骤执行完成", "success": True}
                step.status = AttackStatus.COMPLETED
            
        except Exception as e:
            self.logger.error(f"步骤执行失败: {step.step_id}, 错误: {e}")
            step.error = str(e)
            step.status = AttackStatus.FAILED
            step.result = {"error": str(e), "success": False}
        
        finally:
            step.end_time = time.time()
            
            # 记录执行历史
            execution_record = {
                "step_id": step.step_id,
                "description": step.description,
                "status": step.status.value,
                "execution_time": step.end_time - step.start_time,
                "result": step.result,
                "timestamp": time.time()
            }
            
            context.execution_history.append(execution_record)
            
            self.logger.info(f"步骤完成: {step.step_id}, 状态: {step.status.value}, "
                           f"耗时: {step.end_time - step.start_time:.2f}秒")
    
    async def _execute_tool_step(self, context: AttackContext, step: AttackStep) -> Dict[str, Any]:
        """执行工具步骤"""
        tool_name = step.tool_name
        target = context.target
        
        # 构建工具参数
        tool_params = step.tool_parameters.copy()
        tool_params["target"] = target
        
        # 根据工具类型调整参数
        if tool_name == "nmap_scan":
            tool_params.update({
                "ports": "80,443,8080,8443,3306,22,21",
                "scan_type": "syn",
                "service_version": True
            })
        elif tool_name == "sqlmap_scan":
            # 从上下文中获取URL
            url = self._extract_url_from_context(context)
            tool_params.update({
                "url": url or f"http://{target}",
                "level": 3,
                "risk": 2,
                "batch": True
            })
        elif tool_name == "nikto_scan":
            url = self._extract_url_from_context(context)
            tool_params.update({
                "url": url or f"http://{target}",
                "ssl": False
            })
        elif tool_name == "dirb_scan":
            url = self._extract_url_from_context(context)
            tool_params.update({
                "url": url or f"http://{target}",
                "wordlist": "common"
            })
        
        # 执行工具链
        chain_context = await self.tool_coordinator.execute_chain(
            chain_name="quick_scan" if tool_name == "nmap_scan" else "web_recon",
            target=target,
            strategy="sequential",
            custom_params={tool_name: tool_params}
        )
        
        # 获取工具执行结果
        for tool_result in chain_context.tools_executed:
            if tool_result.tool_name == tool_name:
                return {
                    "success": tool_result.success,
                    "output": tool_result.output,
                    "execution_time": tool_result.execution_time,
                    "flags_found": chain_context.flags_found
                }
        
        # 如果没有找到特定工具的结果，返回第一个结果
        if chain_context.tools_executed:
            first_result = chain_context.tools_executed[0]
            return {
                "success": first_result.success,
                "output": first_result.output,
                "execution_time": first_result.execution_time,
                "flags_found": chain_context.flags_found
            }
        
        return {
            "success": False,
            "error": "工具执行未返回结果",
            "flags_found": []
        }
    
    def _extract_url_from_context(self, context: AttackContext) -> Optional[str]:
        """从上下文中提取URL"""
        # 查找之前的Nmap扫描结果
        for record in context.execution_history:
            if "nmap" in record.get("description", "").lower() and record.get("result", {}).get("success", False):
                result = record["result"]
                output = result.get("output", {})
                parsed = output.get("parsed", {})
                
                if parsed.get("success", False):
                    hosts = parsed.get("hosts", [])
                    for host in hosts:
                        ports = host.get("ports", [])
                        for port in ports:
                            if port.get("port") in [80, 443, 8080, 8443] and port.get("state") == "open":
                                protocol = "https" if port["port"] in [443, 8443] else "http"
                                return f"{protocol}://{context.target}:{port['port']}"
        
        # 如果没有找到，使用默认URL
        if context.target.startswith("http"):
            return context.target
        else:
            return f"http://{context.target}"
    
    def _extract_flags_from_result(self, result: Dict[str, Any]) -> List[str]:
        """从结果中提取flag"""
        flags = []
        
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
        
        # 检查输出
        output = result.get("output", {})
        
        # 检查原始输出
        raw_output = output.get("raw", {})
        if isinstance(raw_output, dict):
            raw_output = json.dumps(raw_output)
        
        for pattern in flag_patterns:
            matches = re.findall(pattern, raw_output)
            flags.extend(matches)
        
        # 检查解析后的输出
        parsed_output = output.get("parsed", {})
        if isinstance(parsed_output, dict):
            parsed_str = json.dumps(parsed_output)
            for pattern in flag_patterns:
                matches = re.findall(pattern, parsed_str)
                flags.extend(matches)
        
        # 去重
        return list(set(flags))
    
    def _extract_vulnerabilities_from_result(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从结果中提取漏洞信息"""
        vulnerabilities = []
        
        output = result.get("output", {})
        parsed = output.get("parsed", {})
        
        if parsed.get("success", False):
            # 从解析结果中提取漏洞
            vulns = parsed.get("vulnerabilities", [])
            if vulns:
                vulnerabilities.extend(vulns)
            
            # 从其他字段提取
            if "issues_found" in parsed and parsed["issues_found"] > 0:
                vulnerabilities.append({
                    "type": "Web Vulnerability",
                    "severity": parsed.get("risk_level", "medium"),
                    "description": f"发现 {parsed['issues_found']} 个安全问题",
                    "source": parsed.get("tool", "unknown")
                })
        
        return vulnerabilities
    
    def _is_critical_step(self, step: AttackStep) -> bool:
        """检查是否是关键步骤"""
        critical_tools = ["nmap_scan"]  # Nmap是关键步骤
        return step.tool_name in critical_tools
    
    async def _generate_attack_report(self, context: AttackContext):
        """生成攻击报告"""
        try:
            report = {
                "attack_id": context.attack_id,
                "target": context.target,
                "start_time": context.start_time,
                "end_time": context.end_time,
                "execution_time": context.end_time - context.start_time if context.end_time else 0,
                "success": context.success,
                "flags_found": context.plan.flags_found,
                "vulnerabilities_found": context.plan.vulnerabilities_found,
                "execution_summary": {
                    "total_steps": len(context.plan.steps),
                    "completed_steps": sum(1 for s in context.plan.steps if s.status == AttackStatus.COMPLETED),
                    "failed_steps": sum(1 for s in context.plan.steps if s.status == AttackStatus.FAILED),
                    "success_rate": sum(1 for s in context.plan.steps if s.status == AttackStatus.COMPLETED) / len(context.plan.steps) if context.plan.steps else 0
                },
                "execution_history": context.execution_history,
                "recommendations": self._generate_recommendations(context)
            }
            
            # 保存报告到文件
            report_file = f"logs/attack_report_{context.attack_id}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"攻击报告已保存: {report_file}")
            
            # 使用AI生成分析报告
            ai_analysis = await self._generate_ai_analysis(context, report)
            if ai_analysis:
                analysis_file = f"logs/attack_analysis_{context.attack_id}.txt"
                with open(analysis_file, 'w', encoding='utf-8') as f:
                    f.write(ai_analysis)
                
                self.logger.info(f"攻击分析报告已保存: {analysis_file}")
            
        except Exception as e:
            self.logger.error(f"生成攻击报告失败: {e}")
    
    async def _generate_ai_analysis(self, context: AttackContext, report: Dict[str, Any]) -> Optional[str]:
        """使用AI生成分析报告"""
        try:
            prompt = f"""
            作为网络安全分析师，请分析以下攻击执行结果：
            
            攻击ID: {context.attack_id}
            目标: {context.target}
            执行时间: {report.get('execution_time', 0):.2f}秒
            成功: {context.success}
            
            发现的Flag: {len(context.plan.flags_found)} 个
            {json.dumps(context.plan.flags_found, indent=2, ensure_ascii=False)}
            
            发现的漏洞: {len(context.plan.vulnerabilities_found)} 个
            {json.dumps(context.plan.vulnerabilities_found, indent=2, ensure_ascii=False)}
            
            执行摘要:
            - 总步骤数: {report['execution_summary']['total_steps']}
            - 完成步骤: {report['execution_summary']['completed_steps']}
            - 失败步骤: {report['execution_summary']['failed_steps']}
            - 成功率: {report['execution_summary']['success_rate']:.2%}
            
            请提供详细的分析报告，包括：
            1. 攻击效果评估
            2. 发现的安全问题分析
            3. 改进建议
            4. 教育意义总结
            
            请以专业的技术报告格式回复。
            """
            
            response = await self.ai_client.generate_response(prompt)
            return response
            
        except Exception as e:
            self.logger.error(f"AI分析生成失败: {e}")
            return None
    
    def _generate_recommendations(self, context: AttackContext) -> List[str]:
        """生成安全建议"""
        recommendations = []
        
        # 基于发现的漏洞生成建议
        vulnerabilities = context.plan.vulnerabilities_found
        
        if any(v.get("type") == "SQL Injection" for v in vulnerabilities):
            recommendations.append("发现SQL注入漏洞，建议：")
            recommendations.append("  - 实施参数化查询或预编译语句")
            recommendations.append("  - 加强输入验证和过滤")
            recommendations.append("  - 部署Web应用防火墙(WAF)")
        
        if any("XSS" in v.get("type", "") for v in vulnerabilities):
            recommendations.append("发现XSS漏洞，建议：")
            recommendations.append("  - 实施输出编码")
            recommendations.append("  - 使用Content Security Policy (CSP)")
            recommendations.append("  - 启用HTTPOnly和Secure cookie标志")
        
        # 基于攻击结果生成建议
        if context.plan.flags_found:
            recommendations.append(f"成功找到 {len(context.plan.flags_found)} 个flag，攻击有效")
        
        if not recommendations:
            recommendations.append("未发现明显安全漏洞，建议：")
            recommendations.append("  - 定期进行安全评估")
            recommendations.append("  - 保持系统和应用更新")
            recommendations.append("  - 实施安全监控")
        
        return recommendations
    
    def get_attack_status(self, attack_id: str) -> Optional[Dict[str, Any]]:
        """获取攻击状态"""
        if attack_id in self.active_attacks:
            context = self.active_attacks[attack_id]
            return self._format_attack_status(context)
        
        # 在历史记录中查找
        for context in self.attack_history:
            if context.attack_id == attack_id:
                return self._format_attack_status(context)
        
        return None
    
    def _format_attack_status(self, context: AttackContext) -> Dict[str, Any]:
        """格式化攻击状态"""
        plan = context.plan
        
        return {
            "attack_id": context.attack_id,
            "target": context.target,
            "status": plan.status.value,
            "current_step": plan.current_step_index,
            "total_steps": len(plan.steps),
            "flags_found": len(plan.flags_found),
            "vulnerabilities_found": len(plan.vulnerabilities_found),
            "start_time": context.start_time,
            "end_time": context.end_time,
            "execution_time": context.end_time - context.start_time if context.end_time else time.time() - context.start_time,
            "success": context.success,
            "current_phase": context.current_phase.value
        }
    
    def get_engine_metrics(self) -> Dict[str, Any]:
        """获取引擎指标"""
        return {
            **self.metrics,
            "active_attacks": len(self.active_attacks),
            "total_history": len(self.attack_history),
            "uptime": time.time() - self.start_time if hasattr(self, 'start_time') else 0
        }
    
    async def stop_attack(self, attack_id: str) -> bool:
        """停止攻击"""
        if attack_id not in self.active_attacks:
            return False
        
        context = self.active_attacks[attack_id]
        context.plan.status = AttackStatus.CANCELLED
        context.end_time = time.time()
        context.success = False
        
        self.logger.info(f"攻击已停止: {attack_id}")
        
        # 移动到历史记录
        self.active_attacks.pop(attack_id)
        self.attack_history.append(context)
        
        return True
    
    async def pause_attack(self, attack_id: str) -> bool:
        """暂停攻击"""
        if attack_id not in self.active_attacks:
            return False
        
        context = self.active_attacks[attack_id]
        context.plan.status = AttackStatus.PAUSED
        
        self.logger.info(f"攻击已暂停: {attack_id}")
        return True
    
    async def resume_attack(self, attack_id: str) -> bool:
        """恢复攻击"""
        if attack_id not in self.active_attacks:
            return False
        
        context = self.active_attacks[attack_id]
        context.plan.status = AttackStatus.RUNNING
        
        self.logger.info(f"攻击已恢复: {attack_id}")
        return True


# 示例使用
async def demo_attack_engine():
    """演示攻击执行引擎的使用"""
    engine = AttackExecutionEngine()
    
    if not await engine.initialize():
        print("攻击执行引擎初始化失败")
        return
    
    print("攻击执行引擎初始化成功")
    
    # 创建攻击计划
    print("\n创建攻击计划...")
    plan = await engine.create_attack_plan(
        target="testphp.vulnweb.com",
        description="CTF Web挑战攻击测试"
    )
    
    print(f"攻击计划创建完成: {plan.plan_id}")
    print(f"包含 {len(plan.steps)} 个步骤:")
    for step in plan.steps:
        print(f"  - {step.description} ({step.tool_name})")
    
    # 执行攻击
    print("\n执行攻击...")
    context = await engine.execute_attack(plan)
    
    print(f"\n攻击执行完成: {context.attack_id}")
    print(f"成功: {context.success}")
    print(f"找到flag: {len(plan.flags_found)} 个")
    print(f"发现漏洞: {len(plan.vulnerabilities_found)} 个")
    
    # 获取引擎指标
    metrics = engine.get_engine_metrics()
    print(f"\n引擎指标:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    
    return context


if __name__ == "__main__":
    # 运行演示
    asyncio.run(demo_attack_engine())