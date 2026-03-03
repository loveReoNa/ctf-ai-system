"""
安全工具输出解析器
用于解析SQLMap、Nmap等安全工具的输出，提取结构化信息
"""
import re
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from src.utils.logger import logger


class VulnerabilitySeverity(Enum):
    """漏洞严重程度等级"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Vulnerability:
    """漏洞信息"""
    type: str
    severity: VulnerabilitySeverity
    description: str
    location: str
    payload: Optional[str] = None
    confidence: float = 0.0  # 置信度 0.0-1.0
    references: List[str] = field(default_factory=list)


@dataclass
class PortInfo:
    """端口信息"""
    port: int
    protocol: str
    state: str
    service: str
    version: Optional[str] = None
    banner: Optional[str] = None


@dataclass
class HostInfo:
    """主机信息"""
    ip: str
    hostname: Optional[str] = None
    os: Optional[str] = None
    ports: List[PortInfo] = field(default_factory=list)
    open_ports_count: int = 0


class ToolOutputParser:
    """工具输出解析器基类"""
    
    def __init__(self):
        self.logger = logger.getChild("tool_parser")
    
    def parse(self, output: str) -> Dict[str, Any]:
        """解析工具输出"""
        raise NotImplementedError("子类必须实现parse方法")
    
    def _extract_json(self, output: str) -> Optional[Dict[str, Any]]:
        """尝试从输出中提取JSON"""
        try:
            # 查找JSON对象
            json_pattern = r'\{.*\}'
            match = re.search(json_pattern, output, re.DOTALL)
            if match:
                return json.loads(match.group())
        except (json.JSONDecodeError, AttributeError):
            pass
        return None


class SQLMapParser(ToolOutputParser):
    """SQLMap输出解析器"""
    
    def parse(self, output: str) -> Dict[str, Any]:
        """
        解析SQLMap输出
        
        Args:
            output: SQLMap输出文本
            
        Returns:
            解析结果字典
        """
        self.logger.info("开始解析SQLMap输出")
        
        result = {
            "success": False,
            "vulnerabilities": [],
            "summary": {
                "injection_points": 0,
                "dbms_detected": None,
                "techniques": [],
                "risk_level": "unknown"
            },
            "raw_output": output[:1000]  # 保留部分原始输出用于调试
        }
        
        try:
            # 检查是否检测到注入点
            if "sqlmap identified the following injection point" in output.lower():
                result["success"] = True
                result["summary"]["injection_points"] = self._count_injection_points(output)
                
                # 提取漏洞信息
                vulnerabilities = self._extract_vulnerabilities(output)
                result["vulnerabilities"] = vulnerabilities
                
                # 提取数据库信息
                dbms = self._extract_dbms(output)
                if dbms:
                    result["summary"]["dbms_detected"] = dbms
                
                # 提取技术信息
                techniques = self._extract_techniques(output)
                result["summary"]["techniques"] = techniques
                
                # 确定风险等级
                result["summary"]["risk_level"] = self._determine_risk_level(output, vulnerabilities)
            
            # 检查是否有错误
            elif "all tested parameters appear to be not injectable" in output.lower():
                result["success"] = True
                result["summary"]["message"] = "未发现SQL注入漏洞"
            
            self.logger.info(f"SQLMap解析完成，发现{len(result['vulnerabilities'])}个漏洞")
            
        except Exception as e:
            self.logger.error(f"SQLMap解析错误: {e}")
            result["error"] = str(e)
        
        return result
    
    def _count_injection_points(self, output: str) -> int:
        """计算注入点数量"""
        count = 0
        # 查找注入点模式
        patterns = [
            r"Parameter: (.+?) \(.+?\)",
            r"Injection point: (.+?) \(.+?\)"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, output, re.IGNORECASE)
            count = max(count, len(matches))
        
        return count if count > 0 else 1
    
    def _extract_vulnerabilities(self, output: str) -> List[Dict[str, Any]]:
        """提取漏洞信息"""
        vulnerabilities = []
        
        # 查找漏洞部分
        vuln_section_pattern = r"---\s*\n\[.*?\]\s*(.+?)\s*\n---"
        vuln_sections = re.findall(vuln_section_pattern, output, re.DOTALL)
        
        for section in vuln_sections:
            vuln = {
                "type": "SQL Injection",
                "severity": "high",
                "description": "",
                "location": "",
                "payload": "",
                "confidence": 0.9
            }
            
            # 提取参数信息
            param_match = re.search(r"Parameter:\s*(.+?)\s*\(", section)
            if param_match:
                vuln["location"] = param_match.group(1).strip()
            
            # 提取类型信息
            type_match = re.search(r"Type:\s*(.+?)\s*\n", section)
            if type_match:
                vuln["description"] = f"SQL注入漏洞 - {type_match.group(1).strip()}"
            
            # 提取载荷
            payload_match = re.search(r"Payload:\s*(.+?)\s*\n", section)
            if payload_match:
                vuln["payload"] = payload_match.group(1).strip()
            
            vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    def _extract_dbms(self, output: str) -> Optional[str]:
        """提取数据库管理系统信息"""
        dbms_patterns = [
            r"back-end DBMS:\s*(.+)",
            r"DBMS:\s*(.+)"
        ]
        
        for pattern in dbms_patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_techniques(self, output: str) -> List[str]:
        """提取使用的技术"""
        techniques = []
        tech_pattern = r"technique:\s*(.+)"
        
        matches = re.findall(tech_pattern, output, re.IGNORECASE)
        for match in matches:
            tech = match.strip()
            if tech and tech not in techniques:
                techniques.append(tech)
        
        return techniques
    
    def _determine_risk_level(self, output: str, vulnerabilities: List[Dict[str, Any]]) -> str:
        """确定风险等级"""
        if not vulnerabilities:
            return "low"
        
        # 检查是否有高危关键词
        high_risk_keywords = [
            "stacked queries",
            "time-based blind",
            "error-based",
            "union query"
        ]
        
        for vuln in vulnerabilities:
            description = vuln.get("description", "").lower()
            for keyword in high_risk_keywords:
                if keyword in description:
                    return "high"
        
        return "medium"


class NmapParser(ToolOutputParser):
    """Nmap输出解析器"""
    
    def parse(self, output: str) -> Dict[str, Any]:
        """
        解析Nmap输出
        
        Args:
            output: Nmap输出文本
            
        Returns:
            解析结果字典
        """
        self.logger.info("开始解析Nmap输出")
        
        result = {
            "success": False,
            "hosts": [],
            "summary": {
                "hosts_scanned": 0,
                "open_ports": 0,
                "services_found": []
            },
            "raw_output": output[:1000]
        }
        
        try:
            # 解析grepable格式 (-oG)
            if "Host:" in output and "Ports:" in output:
                hosts = self._parse_grepable_format(output)
                result["hosts"] = hosts
                result["success"] = True
            # 解析普通格式
            else:
                hosts = self._parse_normal_format(output)
                result["hosts"] = hosts
                result["success"] = len(hosts) > 0
            
            # 生成摘要
            if result["success"]:
                result["summary"] = self._generate_summary(result["hosts"])
            
            self.logger.info(f"Nmap解析完成，发现{len(result['hosts'])}个主机")
            
        except Exception as e:
            self.logger.error(f"Nmap解析错误: {e}")
            result["error"] = str(e)
        
        return result
    
    def _parse_grepable_format(self, output: str) -> List[Dict[str, Any]]:
        """解析grepable格式输出"""
        hosts = []
        
        # 解析每行主机信息
        lines = output.strip().split('\n')
        for line in lines:
            if not line.startswith("Host:"):
                continue
            
            # 解析主机信息
            host_info = self._parse_grepable_line(line)
            if host_info:
                hosts.append(host_info)
        
        return hosts
    
    def _parse_grepable_line(self, line: str) -> Optional[Dict[str, Any]]:
        """解析单行grepable格式"""
        try:
            # 提取主机IP
            ip_match = re.search(r'Host:\s*([0-9.]+|[\w:]+)\s*\(([^)]*)\)', line)
            if not ip_match:
                return None
            
            ip = ip_match.group(1)
            hostname = ip_match.group(2) if ip_match.group(2) else None
            
            # 提取端口信息
            ports_match = re.search(r'Ports:\s*(.+?)(?:\s*Ignored State:|$)', line)
            if not ports_match:
                return None
            
            ports_str = ports_match.group(1)
            ports = self._parse_ports_string(ports_str)
            
            # 提取OS信息
            os_match = re.search(r'OS:\s*(.+?)(?:\s*Seq Index:|$)', line)
            os_info = os_match.group(1).strip() if os_match else None
            
            host_info = {
                "ip": ip,
                "hostname": hostname,
                "os": os_info,
                "ports": ports,
                "open_ports_count": len([p for p in ports if p.get("state") == "open"])
            }
            
            return host_info
            
        except Exception as e:
            self.logger.warning(f"解析grepable行失败: {e}")
            return None
    
    def _parse_ports_string(self, ports_str: str) -> List[Dict[str, Any]]:
        """解析端口字符串"""
        ports = []
        
        # 端口格式: 80/open/tcp//http//Apache httpd 2.4.41
        port_entries = ports_str.split(',')
        
        for entry in port_entries:
            entry = entry.strip()
            if not entry:
                continue
            
            parts = entry.split('/')
            if len(parts) >= 3:
                port_info = {
                    "port": int(parts[0]),
                    "state": parts[1],
                    "protocol": parts[2],
                    "service": parts[3] if len(parts) > 3 and parts[3] else "unknown",
                    "version": parts[4] if len(parts) > 4 and parts[4] else None
                }
                ports.append(port_info)
        
        return ports
    
    def _parse_normal_format(self, output: str) -> List[Dict[str, Any]]:
        """解析普通格式输出"""
        hosts = []
        current_host = None
        
        lines = output.strip().split('\n')
        for line in lines:
            line = line.strip()
            
            # 检测新的主机
            nmap_report_match = re.match(r'Nmap scan report for (.+)', line)
            if nmap_report_match:
                if current_host:
                    hosts.append(current_host)
                
                target = nmap_report_match.group(1)
                # 解析IP和主机名
                if '(' in target and ')' in target:
                    hostname = target.split('(')[0].strip()
                    ip = target.split('(')[1].replace(')', '').strip()
                else:
                    ip = target
                    hostname = None
                
                current_host = {
                    "ip": ip,
                    "hostname": hostname,
                    "os": None,
                    "ports": [],
                    "open_ports_count": 0
                }
                continue
            
            # 解析端口信息
            if current_host and re.match(r'^\d+/', line):
                port_info = self._parse_port_line(line)
                if port_info:
                    current_host["ports"].append(port_info)
                    if port_info.get("state") == "open":
                        current_host["open_ports_count"] += 1
            
            # 解析OS信息
            if current_host and "OS details:" in line:
                current_host["os"] = line.replace("OS details:", "").strip()
        
        # 添加最后一个主机
        if current_host:
            hosts.append(current_host)
        
        return hosts
    
    def _parse_port_line(self, line: str) -> Optional[Dict[str, Any]]:
        """解析端口行"""
        # 格式: 80/tcp open  http    Apache httpd 2.4.41
        parts = line.split()
        if len(parts) < 3:
            return None
        
        port_protocol = parts[0].split('/')
        if len(port_protocol) != 2:
            return None
        
        port_info = {
            "port": int(port_protocol[0]),
            "protocol": port_protocol[1],
            "state": parts[1],
            "service": parts[2] if len(parts) > 2 else "unknown",
            "version": " ".join(parts[3:]) if len(parts) > 3 else None
        }
        
        return port_info
    
    def _generate_summary(self, hosts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成摘要信息"""
        total_open_ports = sum(host.get("open_ports_count", 0) for host in hosts)
        
        # 收集所有服务
        services = []
        for host in hosts:
            for port in host.get("ports", []):
                if port.get("state") == "open":
                    service = port.get("service", "unknown")
                    if service not in services:
                        services.append(service)
        
        return {
            "hosts_scanned": len(hosts),
            "open_ports": total_open_ports,
            "services_found": services,
            "unique_services": len(services)
        }


class ToolParserFactory:
    """工具解析器工厂"""
    
    @staticmethod
    def get_parser(tool_name: str) -> Optional[ToolOutputParser]:
        """
        获取工具解析器
        
        Args:
            tool_name: 工具名称
            
        Returns:
            解析器实例或None
        """
        parsers = {
            "sqlmap": SQLMapParser,
            "nmap": NmapParser,
            "sqlmap_scan": SQLMapParser,
            "nmap_scan": NmapParser
        }
        
        parser_class = parsers.get(tool_name.lower())
        if parser_class:
            return parser_class()
        
        return None
    
    @staticmethod
    def parse_tool_output(tool_name: str, output: str) -> Dict[str, Any]:
        """
        解析工具输出
        
        Args:
            tool_name: 工具名称
            output: 工具输出
            
        Returns:
            解析结果
        """
        parser = ToolParserFactory.get_parser(tool_name)
        if parser:
            return parser.parse(output)
        else:
            # 返回原始输出
            return {
                "success": False,
                "error": f"不支持的工具: {tool_name}",
                "raw_output": output[:1000]
            }


# 全局解析器实例
tool_parser_factory = ToolParserFactory()