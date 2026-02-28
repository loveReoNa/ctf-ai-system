#!/usr/bin/env python3
"""
ReAct AI代理实现
基于Reasoning + Acting框架的智能攻击代理
"""

import asyncio
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from src.utils.logger import logger
from src.utils.deepseek_client import DeepSeekClient
from src.mcp_server.server import CTFMCPServer


class AgentState(Enum):
    """代理状态枚举"""
    IDLE = "idle"           # 空闲状态
    ANALYZING = "analyzing" # 分析挑战
    PLANNING = "planning"   # 规划攻击
    EXECUTING = "executing" # 执行攻击
    OBSERVING = "observing" # 观察结果
    COMPLETED = "completed" # 完成
    FAILED = "failed"       # 失败


class ToolType(Enum):
    """工具类型枚举"""
    SCANNING = "scanning"       # 扫描工具
    EXPLOITATION = "exploitation" # 利用工具
    INFORMATION = "information"   # 信息收集
    POST_EXPLOITATION = "post_exploitation" # 后渗透


@dataclass
class CTFChallenge:
    """CTF挑战数据结构"""
    id: str
    title: str
    description: str
    target_url: str
    category: str  # web, crypto, pwn, etc.
    difficulty: str  # easy, medium, hard
    hints: List[str] = field(default_factory=list)
    expected_flag: Optional[str] = None


@dataclass
class AttackStep:
    """攻击步骤"""
    step_id: int
    action: str
    tool: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""
    expected_result: str = ""
    actual_result: Optional[str] = None
    success: Optional[bool] = None
    timestamp: str = ""


@dataclass
class AttackPlan:
    """攻击计划"""
    challenge: CTFChallenge
    steps: List[AttackStep] = field(default_factory=list)
    current_step: int = 0
    vulnerabilities: List[str] = field(default_factory=list)
    confidence: float = 0.0  # 0-1之间的置信度


class ReActAgent:
    """ReAct AI代理主类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化ReAct代理
        
        Args:
            config: 代理配置
        """
        self.config = config
        self.state = AgentState.IDLE
        self.logger = logger.getChild("react_agent")
        
        # 初始化AI客户端（DeepSeekClient从配置管理器读取配置）
        self.ai_client = DeepSeekClient()
        
        # 初始化MCP服务器
        self.mcp_server = CTFMCPServer()
        
        # 当前攻击计划
        self.current_plan: Optional[AttackPlan] = None
        
        # 执行历史
        self.execution_history: List[Dict[str, Any]] = []
        
        # 工具映射
        self.tool_mapping = {
            "sqlmap_scan": ToolType.EXPLOITATION,
            "nmap_scan": ToolType.SCANNING,
        }
        
        self.logger.info("ReAct代理初始化完成")
    
    async def initialize(self):
        """初始化代理"""
        try:
            await self.mcp_server.initialize()
            self.logger.info("MCP服务器初始化完成")
            return True
        except Exception as e:
            self.logger.error(f"MCP服务器初始化失败: {e}")
            return False
    
    def set_challenge(self, challenge: CTFChallenge):
        """设置当前挑战"""
        self.current_plan = AttackPlan(challenge=challenge)
        self.state = AgentState.ANALYZING
        self.logger.info(f"设置挑战: {challenge.title}")
    
    async def analyze_challenge(self) -> Dict[str, Any]:
        """
        分析CTF挑战
        
        Returns:
            分析结果
        """
        if not self.current_plan:
            raise ValueError("未设置挑战")
        
        self.state = AgentState.ANALYZING
        self.logger.info("开始分析挑战...")
        
        challenge = self.current_plan.challenge
        
        # 构建分析提示
        prompt = f"""
        请分析以下CTF挑战：
        
        标题: {challenge.title}
        类别: {challenge.category}
        难度: {challenge.difficulty}
        目标URL: {challenge.target_url}
        描述: {challenge.description}
        
        提示:
        {chr(10).join(f'- {hint}' for hint in challenge.hints)}
        
        请分析：
        1. 可能的漏洞类型
        2. 攻击入口点
        3. 需要收集的信息
        4. 建议的攻击策略
        
        请以JSON格式回复，包含以下字段：
        - vulnerabilities: 可能的漏洞列表
        - entry_points: 攻击入口点
        - information_needed: 需要收集的信息
        - strategy: 攻击策略描述
        - confidence: 分析置信度 (0-1)
        """
        
        try:
            # 调用AI进行分析
            response = await self.ai_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3  # 低温度以获得更确定的回答
            )
            
            # 解析AI响应
            analysis_result = self._parse_analysis_response(response)
            
            # 更新攻击计划
            if "vulnerabilities" in analysis_result:
                self.current_plan.vulnerabilities = analysis_result["vulnerabilities"]
            
            if "confidence" in analysis_result:
                self.current_plan.confidence = analysis_result["confidence"]
            
            self.logger.info(f"挑战分析完成，置信度: {self.current_plan.confidence:.2f}")
            self.logger.info(f"识别到漏洞: {self.current_plan.vulnerabilities}")
            
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"挑战分析失败: {e}")
            self.state = AgentState.FAILED
            return {"error": str(e)}
    
    def _parse_analysis_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """解析AI分析响应"""
        try:
            # 检查响应是否成功
            if not response.get("success", False):
                return {
                    "raw_response": response.get("error", "API调用失败"),
                    "vulnerabilities": ["API错误"],
                    "confidence": 0.1
                }
            
            # 获取响应内容
            content = response.get("content", "")
            if not content:
                return {
                    "raw_response": "空响应",
                    "vulnerabilities": ["未知"],
                    "confidence": 0.3
                }
            
            # 尝试从响应中提取JSON
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            # 如果找不到JSON，返回原始响应
            return {
                "raw_response": content,
                "vulnerabilities": ["未知"],
                "confidence": 0.5
            }
        except json.JSONDecodeError as e:
            self.logger.warning(f"JSON解析失败: {e}")
            return {
                "raw_response": response.get("content", str(response)),
                "vulnerabilities": ["解析失败"],
                "confidence": 0.3
            }
    
    async def plan_attack(self) -> AttackPlan:
        """
        规划攻击链
        
        Returns:
            攻击计划
        """
        if not self.current_plan:
            raise ValueError("未设置挑战")
        
        self.state = AgentState.PLANNING
        self.logger.info("开始规划攻击链...")
        
        challenge = self.current_plan.challenge
        
        # 获取可用工具
        available_tools = await self.mcp_server.handle_list_tools()
        
        # 构建规划提示
        prompt = f"""
        基于以下分析结果，规划攻击链：
        
        挑战: {challenge.title}
        目标URL: {challenge.target_url}
        识别到的漏洞: {', '.join(self.current_plan.vulnerabilities)}
        置信度: {self.current_plan.confidence:.2f}
        
        可用工具:
        {chr(10).join(f'- {tool["name"]}: {tool["description"]}' for tool in available_tools)}
        
        请规划一个多步骤的攻击链，每个步骤应包含：
        1. 步骤编号
        2. 行动描述
        3. 使用的工具（如果有）
        4. 工具参数
        5. 推理过程
        6. 预期结果
        
        请以JSON数组格式回复，每个元素包含：
        - step_id: 步骤编号
        - action: 行动描述
        - tool: 工具名称（可选）
        - parameters: 工具参数（可选）
        - reasoning: 推理过程
        - expected_result: 预期结果
        """
        
        try:
            # 调用AI进行规划
            response = await self.ai_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5
            )
            
            # 解析攻击步骤
            attack_steps = self._parse_attack_steps(response)
            
            # 创建攻击步骤对象
            for i, step_data in enumerate(attack_steps):
                step = AttackStep(
                    step_id=i + 1,
                    action=step_data.get("action", f"步骤 {i+1}"),
                    tool=step_data.get("tool"),
                    parameters=step_data.get("parameters", {}),
                    reasoning=step_data.get("reasoning", ""),
                    expected_result=step_data.get("expected_result", ""),
                    timestamp=asyncio.get_event_loop().time()
                )
                self.current_plan.steps.append(step)
            
            self.logger.info(f"攻击规划完成，共 {len(self.current_plan.steps)} 个步骤")
            self.state = AgentState.IDLE
            
            return self.current_plan
            
        except Exception as e:
            self.logger.error(f"攻击规划失败: {e}")
            self.state = AgentState.FAILED
            raise
    
    def _parse_attack_steps(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析攻击步骤"""
        try:
            # 检查响应是否成功
            if not response.get("success", False):
                self.logger.warning(f"API调用失败: {response.get('error', '未知错误')}")
                return self._get_default_steps()
            
            # 获取响应内容
            content = response.get("content", "")
            if not content:
                self.logger.warning("API返回空内容")
                return self._get_default_steps()
            
            # 尝试从响应中提取JSON数组
            array_match = re.search(r'\[.*\]', content, re.DOTALL)
            if array_match:
                return json.loads(array_match.group())
            
            # 如果找不到JSON数组，创建默认步骤
            self.logger.warning("未找到JSON数组，使用默认步骤")
            return self._get_default_steps()
            
        except json.JSONDecodeError as e:
            self.logger.warning(f"攻击步骤JSON解析失败: {e}")
            return self._get_default_steps()
    
    def _get_default_steps(self) -> List[Dict[str, Any]]:
        """获取默认攻击步骤"""
        if not self.current_plan:
            return []
        
        return [
            {
                "step_id": 1,
                "action": "信息收集",
                "tool": "nmap_scan",
                "parameters": {"target": self.current_plan.challenge.target_url},
                "reasoning": "首先收集目标信息",
                "expected_result": "获取开放端口和服务信息"
            },
            {
                "step_id": 2,
                "action": "漏洞扫描",
                "tool": "sqlmap_scan",
                "parameters": {"url": self.current_plan.challenge.target_url},
                "reasoning": "扫描SQL注入漏洞",
                "expected_result": "识别SQL注入点"
            }
        ]
    
    async def execute_plan(self) -> Dict[str, Any]:
        """
        执行攻击计划
        
        Returns:
            执行结果
        """
        if not self.current_plan or not self.current_plan.steps:
            raise ValueError("没有可执行的攻击计划")
        
        self.state = AgentState.EXECUTING
        self.logger.info(f"开始执行攻击计划，共 {len(self.current_plan.steps)} 个步骤")
        
        results = {
            "total_steps": len(self.current_plan.steps),
            "successful_steps": 0,
            "failed_steps": 0,
            "steps_details": [],
            "flag_found": False,
            "final_flag": None
        }
        
        # 按顺序执行每个步骤
        for step in self.current_plan.steps:
            step_result = await self._execute_step(step)
            results["steps_details"].append(step_result)
            
            if step_result.get("success"):
                results["successful_steps"] += 1
            else:
                results["failed_steps"] += 1
            
            # 检查是否找到flag
            if step_result.get("flag_detected"):
                results["flag_found"] = True
                results["final_flag"] = step_result.get("flag")
                break
        
        # 更新状态
        if results["flag_found"]:
            self.state = AgentState.COMPLETED
            self.logger.info(f"攻击成功完成！找到flag: {results['final_flag']}")
        elif results["successful_steps"] > 0:
            self.state = AgentState.COMPLETED
            self.logger.info("攻击完成，但未找到flag")
        else:
            self.state = AgentState.FAILED
            self.logger.warning("攻击失败")
        
        return results
    
    async def _execute_step(self, step: AttackStep) -> Dict[str, Any]:
        """执行单个攻击步骤"""
        self.logger.info(f"执行步骤 {step.step_id}: {step.action}")
        
        step_result = {
            "step_id": step.step_id,
            "action": step.action,
            "tool": step.tool,
            "success": False,
            "result": None,
            "error": None,
            "flag_detected": False,
            "flag": None,
            "execution_time": None
        }
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            if step.tool and step.tool in self.tool_mapping:
                # 执行工具
                tool_result = await self.mcp_server.handle_call_tool(
                    step.tool, step.parameters
                )
                
                step_result["result"] = tool_result
                step_result["success"] = tool_result.get("success", False)
                
                # 检查是否找到flag
                if step_result["success"]:
                    flag = self._extract_flag_from_result(tool_result)
                    if flag:
                        step_result["flag_detected"] = True
                        step_result["flag"] = flag
            else:
                # 无工具步骤（如信息分析）
                step_result["success"] = True
                step_result["result"] = {"message": "步骤执行完成"}
            
            # 更新步骤状态
            step.success = step_result["success"]
            step.actual_result = json.dumps(step_result["result"], ensure_ascii=False)
            
        except Exception as e:
            self.logger.error(f"步骤 {step.step_id} 执行失败: {e}")
            step_result["error"] = str(e)
            step_result["success"] = False
            step.success = False
            step.actual_result = f"错误: {str(e)}"
        
        # 计算执行时间
        step_result["execution_time"] = asyncio.get_event_loop().time() - start_time
        
        # 记录执行历史
        self.execution_history.append({
            "timestamp": asyncio.get_event_loop().time(),
            "step": step.step_id,
            "action": step.action,
            "success": step_result["success"],
            "result": step_result["result"]
        })
        
        return step_result
    
    def _extract_flag_from_result(self, result: Dict[str, Any]) -> Optional[str]:
        """从工具结果中提取flag"""
        if not result:
            return None
        
        # 检查stdout中是否包含flag模式
        stdout = result.get("stdout", "")
        stderr = result.get("stderr", "")
        
        # 常见的flag格式
        flag_patterns = [
            r'flag\{[^}]+\}',
            r'FLAG\{[^}]+\}',
            r'ctf\{[^}]+\}',
            r'CTF\{[^}]+\}',
            r'[A-Za-z0-9]{32}',  # 32位哈希
            r'[A-Za-z0-9]{64}',  # 64位哈希
        ]
        
        for pattern in flag_patterns:
            match = re.search(pattern, stdout + stderr)
            if match:
                return match.group()
        
        return None
    
    async def run_full_attack(self, challenge: CTFChallenge) -> Dict[str, Any]:
        """
        运行完整的攻击流程
        
        Args:
            challenge: CTF挑战
            
        Returns:
            完整攻击结果
        """
        self.logger.info(f"开始完整攻击流程: {challenge.title}")
        
        try:
            # 1. 设置挑战
            self.set_challenge(challenge)
            
            # 2. 分析挑战
            analysis_result = await self.analyze_challenge()
            if "error" in analysis_result:
                return {"success": False, "error": "挑战分析失败", "details": analysis_result}
            
            # 3. 规划攻击
            attack_plan = await self.plan_attack()
            
            # 4. 执行攻击
            execution_result = await self.execute_plan()
            
            # 5. 生成报告
            report = self.generate_report(analysis_result, attack_plan, execution_result)
            
            self.logger.info("完整攻击流程完成")
            return report
            
        except Exception as e:
            self.logger.error(f"完整攻击流程失败: {e}")
            self.state = AgentState.FAILED
            return {
                "success": False,
                "error": str(e),
                "state": self.state.value
            }
    
    def generate_report(self, analysis: Dict[str, Any], 
                       plan: AttackPlan, 
                       execution: Dict[str, Any]) -> Dict[str, Any]:
        """生成攻击报告"""
        return {
            "challenge": {
                "title": plan.challenge.title,
                "category": plan.challenge.category,
                "difficulty": plan.challenge.difficulty,
                "target_url": plan.challenge.target_url
            },
            "analysis": analysis,
            "plan_summary": {
                "total_steps": len(plan.steps),
                "vulnerabilities": plan.vulnerabilities,
                "confidence": plan.confidence
            },
            "execution": execution,
            "agent_state": self.state.value,
            "timestamp": asyncio.get_event_loop().time(),
            "success": execution.get("flag_found", False) or execution.get("successful_steps", 0) > 0
        }
    
    def get_status(self) -> Dict[str, Any]:
        """获取代理状态"""
        return {
            "state": self.state.value,
            "current_plan": self.current_plan.challenge.title if self.current_plan else None,
            "execution_history_count": len(self.execution_history),
            "tools_available": list(self.tool_mapping.keys())
        }


# 示例使用
async def demo_react_agent():
    """演示ReAct代理的使用"""
    from src.utils.config_manager import config
    
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
    
    # 创建代理
    agent_config = {
        "ai": config.get("ai", {}),
        "mcp": config.get("mcp", {})
    }
    
    agent = ReActAgent(agent_config)
    
    # 初始化
    if not await agent.initialize():
        print("代理初始化失败")
        return
    
    # 运行完整攻击
    print(f"开始攻击挑战: {challenge.title}")
    result = await agent.run_full_attack(challenge)
    
    print("\n" + "="*50)
    print("攻击结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("="*50)
    
    return result


if __name__ == "__main__":
    # 运行演示
    asyncio.run(demo_react_agent())