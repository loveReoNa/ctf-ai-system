"""
安全工具输出解析器
用于解析SQLMap、Nmap等安全工具的输出，提取结构化信息
增强版：支持更多工具，提供更详细的解析结果
"""

import re
import json
import xml.etree.ElementTree as ET
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
    cvss_score: Optional[float] = None
    remediation: Optional[str] = None


@dataclass
class PortInfo:
    """端口信息"""
    port: int
    protocol: str
    state: str
    service: str
    version: Optional[str] = None
    banner: Optional[str] = None
    cpe: Optional[str] = None  # Common Platform Enumeration


@dataclass
class HostInfo:
    """主机信息"""
    ip: str
    hostname: Optional[str] = None
    os: Optional[str] = None
    os_accuracy: Optional[int] = None
    ports: List[PortInfo] = field(default_factory=list)
    open_ports_count: int = 0
    vulnerabilities: List[Vulnerability] = field(default_factory=list)


@dataclass
class WebPath:
    """Web路径信息"""
    url: str
    status_code: int
    content_length: int
    title: Optional[str] = None
    redirect: Optional[str] = None
    content_type: Optional[str] = None


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
    
    def _extract_xml(self, output: str) -> Optional[ET.Element]:
        """尝试从输出中提取XML"""
        try:
            # 查找XML内容
            xml_pattern = r'<\?xml.*\?>.*'
            match = re.search(xml_pattern, output, re.DOTALL)
            if match:
                return ET.fromstring(match.group())
        except (ET.ParseError, AttributeError):
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
                "risk_level": "unknown",
                "tables_found": [],
                "columns_found": [],
                "data_dumped": False
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
                
                # 提取数据库结构信息
                tables = self._extract_tables(output)
                if tables:
                    result["summary"]["tables_found"] = tables
                
                columns = self._extract_columns(output)
                if columns:
                    result["summary"]["columns_found"] = columns
                
                # 检查是否dump了数据
                if "dumped table" in output.lower():
                    result["summary"]["data_dumped"] = True
                
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
                "confidence": 0.9,
                "cvss_score": 8.5,
                "remediation": "使用参数化查询或预编译语句，实施输入验证"
            }
            
            # 提取参数信息
            param_match = re.search(r"Parameter:\s*(.+?)\s*\(", section)
            if param_match:
                vuln["location"] = param_match.group(1).strip()
            
            # 提取类型信息
            type_match = re.search(r"Type:\s*(.+?)\s*\n", section)
            if type_match:
                vuln_type = type_match.group(1).strip()
                vuln["description"] = f"SQL注入漏洞 - {vuln_type}"
                
                # 根据类型调整严重性
                if "time-based blind" in vuln_type.lower():
                    vuln["severity"] = "medium"
                    vuln["cvss_score"] = 6.5
                elif "error-based" in vuln_type.lower():
                    vuln["severity"] = "high"
                    vuln["cvss_score"] = 8.0
                elif "union query" in vuln_type.lower():
                    vuln["severity"] = "critical"
                    vuln["cvss_score"] = 9.0
            
            # 提取载荷
            payload_match = re.search(r"Payload:\s*(.+?)\s*\n", section)
            if payload_match:
                vuln["payload"] = payload_match.group(1).strip()
            
            # 提取数据库信息
            db_match = re.search(r"back-end DBMS:\s*(.+)", section)
            if db_match:
                vuln["description"] += f" (DBMS: {db_match.group(1).strip()})"
            
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
    
    def _extract_tables(self, output: str) -> List[str]:
        """提取发现的表"""
        tables = []
        table_pattern = r"Database:\s*.+?\s*Table:\s*(.+)"
        
        matches = re.findall(table_pattern, output, re.IGNORECASE)
        for match in matches:
            table = match.strip()
            if table and table not in tables:
                tables.append(table)
        
        return tables
    
    def _extract_columns(self, output: str) -> List[str]:
        """提取发现的列"""
        columns = []
        column_pattern = r"Column:\s*(.+)"
        
        matches = re.findall(column_pattern, output, re.IGNORECASE)
        for match in matches:
            column = match.strip()
            if column and column not in columns:
                columns.append(column)
        
        return columns
    
    def _determine_risk_level(self, output: str, vulnerabilities: List[Dict[str, Any]]) -> str:
        """确定风险等级"""
        if not vulnerabilities:
            return "low"
        
        # 检查是否有高危关键词
        critical_keywords = ["union query", "stacked queries"]
        high_keywords = ["error-based", "boolean-based blind"]
        medium_keywords = ["time-based blind"]
        
        for vuln in vulnerabilities:
            description = vuln.get("description", "").lower()
            
            for keyword in critical_keywords:
                if keyword in description:
                    return "critical"
            
            for keyword in high_keywords:
                if keyword in description:
                    return "high"
            
            for keyword in medium_keywords:
                if keyword in description:
                    return "medium"
        
        return "low"


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
                "services_found": [],
                "os_detected": [],
                "vulnerabilities_found": 0
            },
            "raw_output": output[:1000]
        }
        
        try:
            # 解析XML格式 (-oX)
            if "<?xml" in output and "<nmaprun" in output:
                hosts = self._parse_xml_format(output)
                result["hosts"] = hosts
                result["success"] = len(hosts) > 0
            # 解析grepable格式 (-oG)
            elif "Host:" in output and "Ports:" in output:
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
    
    def _parse_xml_format(self, output: str) -> List[Dict[str, Any]]:
        """解析XML格式输出"""
        hosts = []
        
        try:
            root = ET.fromstring(output)
            
            for host in root.findall("host"):
                host_info = self._parse_xml_host(host)
                if host_info:
                    hosts.append(host_info)
        
        except ET.ParseError as e:
            self.logger.warning(f"XML解析失败，尝试其他格式: {e}")
            return self._parse_normal_format(output)
        
        return hosts
    
    def _parse_xml_host(self, host_elem: ET.Element) -> Optional[Dict[str, Any]]:
        """解析XML主机元素"""
        try:
            # 提取地址信息
            address_elem = host_elem.find("address[@addrtype='ipv4']")
            if address_elem is None:
                address_elem = host_elem.find("address[@addrtype='ipv6']")
            
            if address_elem is None:
                return None
            
            ip = address_elem.get("addr", "")
            
            # 提取主机名
            hostname = None
            hostnames_elem = host_elem.find("hostnames")
            if hostnames_elem is not None:
                hostname_elem = hostnames_elem.find("hostname")
                if hostname_elem is not None:
                    hostname = hostname_elem.get("name", "")
            
            # 提取OS信息
            os_info = None
            os_accuracy = None
            os_elem = host_elem.find("os")
            if os_elem is not None:
                os_match_elem = os_elem.find("osmatch")
                if os_match_elem is not None:
                    os_info = os_match_elem.get("name", "")
                    os_accuracy = os_match_elem.get("accuracy", "")
            
            # 提取端口信息
            ports = []
            ports_elem = host_elem.find("ports")
            if ports_elem is not None:
                for port_elem in ports_elem.findall("port"):
                    port_info = self._parse_xml_port(port_elem)
                    if port_info:
                        ports.append(port_info)
            
            host_info = {
                "ip": ip,
                "hostname": hostname,
                "os": os_info,
                "os_accuracy": int(os_accuracy) if os_accuracy and os_accuracy.isdigit() else None,
                "ports": ports,
                "open_ports_count": len([p for p in ports if p.get("state") == "open"])
            }
            
            return host_info
            
        except Exception as e:
            self.logger.warning(f"解析XML主机失败: {e}")
            return None
    
    def _parse_xml_port(self, port_elem: ET.Element) -> Optional[Dict[str, Any]]:
        """解析XML端口元素"""
        try:
            port_id = port_elem.get("portid", "")
            protocol = port_elem.get("protocol", "tcp")
            
            # 提取端口状态
            state_elem = port_elem.find("state")
            state = state_elem.get("state", "unknown") if state_elem is not None else "unknown"
            
            # 提取服务信息
            service_elem = port_elem.find("service")
            service = "unknown"
            version = None
            banner = None
            cpe = None
            
            if service_elem is not None:
                service = service_elem.get("name", "unknown")
                version = service_elem.get("version", "")
                banner = service_elem.get("product", "")
                if banner and version:
                    banner = f"{banner} {version}"
                
                # 提取CPE
                cpe_elem = service_elem.find("cpe")
                if cpe_elem is not None:
                    cpe = cpe_elem.text
            
            port_info = {
                "port": int(port_id) if port_id.isdigit() else 0,
                "protocol": protocol,
                "state": state,
                "service": service,
                "version": version,
                "banner": banner,
                "cpe": cpe
            }
            
            return port_info
            
        except Exception as e:
            self.logger.warning(f"解析XML端口失败: {e}")
            return None
    
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
                "os_accuracy": None,
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
                    "version": parts[4] if len(parts) > 4 and parts[4] else None,
                    "banner": parts[4] if len(parts) > 4 else None,
                    "cpe": None
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
                    "os_accuracy": None,
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
            elif current_host and "Running:" in line:
                current_host["os"] = line.replace("Running:", "").strip()
        
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
            "version": " ".join(parts[3:]) if len(parts) > 3 else None,
            "banner": " ".join(parts[3:]) if len(parts) > 3 else None,
            "cpe": None
        }
        
        return port_info
    
    def _generate_summary(self, hosts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成摘要信息"""
        total_open_ports = sum(host.get("open_ports_count", 0) for host in hosts)
        
        # 收集所有服务
        services = []
        os_list = []
        
        for host in hosts:
            # 收集OS信息
            if host.get("os"):
                os_list.append(host["os"])
            
            # 收集服务信息
            for port in host.get("ports", []):
                if port.get("state") == "open":
                    service = port.get("service", "unknown")
                    if service not in services:
                        services.append(service)
        
        return {
            "hosts_scanned": len(hosts),
            "open_ports": total_open_ports,
            "services_found": services,
            "unique_services": len(services),
            "os_detected": list(set(os_list)),
            "vulnerabilities_found": 0  # Nmap本身不检测漏洞
        }


class NiktoParser(ToolOutputParser):
    """Nikto输出解析器"""
    
    def parse(self, output: str) -> Dict[str, Any]:
        """
        解析Nikto输出
        
        Args:
            output: Nikto输出文本
            
        Returns:
            解析结果字典
        """
        self.logger.info("开始解析Nikto输出")
        
        result = {
            "success": False,
            "vulnerabilities": [],
            "summary": {
                "issues_found": 0,
                "server_info": {},
                "risk_level": "unknown"
            },
            "raw_output": output[:1000]
        }
        
        try:
            # 检查是否有漏洞发现
            if "+" in output and ":" in output:
                result["success"] = True
                
                # 提取服务器信息
                server_info = self._extract_server_info(output)
                result["summary"]["server_info"] = server_info
                
                # 提取漏洞信息
                vulnerabilities = self._extract_vulnerabilities(output)
                result["vulnerabilities"] = vulnerabilities
                result["summary"]["issues_found"] = len(vulnerabilities)
                
                # 确定风险等级
                result["summary"]["risk_level"] = self._determine_risk_level(vulnerabilities)
            
            self.logger.info(f"Nikto解析完成，发现{len(result['vulnerabilities'])}个问题")
            
        except Exception as e:
            self.logger.error(f"Nikto解析错误: {e}")
            result["error"] = str(e)
        
        return result
    
    def _extract_server_info(self, output: str) -> Dict[str, Any]:
        """提取服务器信息"""
        server_info = {}
        
        # 提取服务器类型
        server_match = re.search(r'Server:\s*(.+)', output)
        if server_match:
            server_info["type"] = server_match.group(1).strip()
        
        # 提取服务器版本
        version_match = re.search(r'Version:\s*(.+)', output)
        if version_match:
            server_info["version"] = version_match.group(1).strip()
        
        # 提取IP地址
        ip_match = re.search(r'Target IP:\s*(.+)', output)
        if ip_match:
            server_info["ip"] = ip_match.group(1).strip()
        
        # 提取主机名
        hostname_match = re.search(r'Target hostname:\s*(.+)', output)
        if hostname_match:
            server_info["hostname"] = hostname_match.group(1).strip()
        
        return server_info
    
    def _extract_vulnerabilities(self, output: str) -> List[Dict[str, Any]]:
        """提取漏洞信息"""
        vulnerabilities = []
        
        # Nikto输出格式: + /path:issue description
        lines = output.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('+') and ':' in line:
                # 解析漏洞行
                parts = line[1:].split(':', 1)
                if len(parts) == 2:
                    path = parts[0].strip()
                    description = parts[1].strip()
                    
                    vuln = {
                        "type": "Web Vulnerability",
                        "severity": self._classify_nikto_severity(description),
                        "description": description,
                        "location": path,
                        "confidence": 0.8,
                        "cvss_score": self._estimate_cvss_score(description),
                        "remediation": "更新服务器软件，配置安全头，修复配置问题"
                    }
                    
                    vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    def _classify_nikto_severity(self, description: str) -> str:
        """根据描述分类严重性"""
        description_lower = description.lower()
        
        if any(keyword in description_lower for keyword in ["xss", "sql injection", "rce", "remote code execution"]):
            return "high"
        elif any(keyword in description_lower for keyword in ["directory listing", "information disclosure", "backup file"]):
            return "medium"
        elif any(keyword in description_lower for keyword in ["server header", "cookie", "robots.txt"]):
            return "low"
        else:
            return "info"
    
    def _estimate_cvss_score(self, description: str) -> float:
        """估计CVSS分数"""
        description_lower = description.lower()
        
        if any(keyword in description_lower for keyword in ["xss", "sql injection", "rce"]):
            return 7.5
        elif any(keyword in description_lower for keyword in ["directory listing", "information disclosure"]):
            return 5.0
        elif any(keyword in description_lower for keyword in ["server header", "cookie"]):
            return 3.5
        else:
            return 2.0
    
    def _determine_risk_level(self, vulnerabilities: List[Dict[str, Any]]) -> str:
        """确定风险等级"""
        if not vulnerabilities:
            return "low"
        
        severities = [v.get("severity", "info") for v in vulnerabilities]
        
        if "high" in severities:
            return "high"
        elif "medium" in severities:
            return "medium"
        elif "low" in severities:
            return "low"
        else:
            return "info"


class DirbParser(ToolOutputParser):
    """Dirb输出解析器"""
    
    def parse(self, output: str) -> Dict[str, Any]:
        """
        解析Dirb输出
        
        Args:
            output: Dirb输出文本
            
        Returns:
            解析结果字典
        """
        self.logger.info("开始解析Dirb输出")
        
        result = {
            "success": False,
            "paths": [],
            "summary": {
                "paths_found": 0,
                "status_codes": {},
                "interesting_paths": []
            },
            "raw_output": output[:1000]
        }
        
        try:
            # 检查是否有路径发现
            if "DIRB" in output and "Scanning" in output:
                result["success"] = True
                
                # 提取发现的路径
                paths = self._extract_paths(output)
                result["paths"] = paths
                result["summary"]["paths_found"] = len(paths)
                
                # 分析状态码分布
                status_codes = self._analyze_status_codes(paths)
                result["summary"]["status_codes"] = status_codes
                
                # 标记有趣的路径
                interesting_paths = self._identify_interesting_paths(paths)
                result["summary"]["interesting_paths"] = interesting_paths
            
            self.logger.info(f"Dirb解析完成，发现{len(result['paths'])}个路径")
            
        except Exception as e:
            self.logger.error(f"Dirb解析错误: {e}")
            result["error"] = str(e)
        
        return result
    
    def _extract_paths(self, output: str) -> List[Dict[str, Any]]:
        """提取发现的路径"""
        paths = []
        
        # Dirb输出格式: + URL (CODE:Size)
        lines = output.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('+') and '(' in line and ')' in line:
                # 解析路径行
                url_part = line[1:].split('(')[0].strip()
                code_size_part = line.split('(')[1].split(')')[0]
                
                # 提取状态码和大小
                code_match = re.search(r'CODE:(\d+)', code_size_part)
                size_match = re.search(r'Size:(\d+)', code_size_part)
                
                if code_match:
                    path_info = {
                        "url": url_part,
                        "status_code": int(code_match.group(1)),
                        "content_length": int(size_match.group(1)) if size_match else 0
                    }
                    
                    paths.append(path_info)
        
        return paths
    
    def _analyze_status_codes(self, paths: List[Dict[str, Any]]) -> Dict[str, int]:
        """分析状态码分布"""
        status_codes = {}
        
        for path in paths:
            code = str(path.get("status_code", 0))
            status_codes[code] = status_codes.get(code, 0) + 1
        
        return status_codes
    
    def _identify_interesting_paths(self, paths: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """识别有趣的路径"""
        interesting_paths = []
        
        interesting_keywords = [
            "admin", "login", "config", "backup", "sql", "db", 
            "phpinfo", "test", "debug", "console", "api"
        ]
        
        for path in paths:
            url = path.get("url", "").lower()
            status_code = path.get("status_code", 0)
            
            # 检查是否有趣
            is_interesting = False
            reason = ""
            
            # 状态码检查
            if status_code == 200:
                is_interesting = True
                reason = "可访问页面"
            elif status_code == 403:
                is_interesting = True
                reason = "禁止访问（可能存在权限控制）"
            elif status_code == 301 or status_code == 302:
                is_interesting = True
                reason = "重定向"
            
            # 关键词检查
            for keyword in interesting_keywords:
                if keyword in url:
                    is_interesting = True
                    reason = f"包含关键词 '{keyword}'"
                    break
            
            # 文件扩展名检查
            if any(url.endswith(ext) for ext in [".bak", ".old", ".tmp", ".swp", ".sql", ".db"]):
                is_interesting = True
                reason = "备份或临时文件"
            
            if is_interesting:
                interesting_path = path.copy()
                interesting_path["reason"] = reason
                interesting_paths.append(interesting_path)
        
        return interesting_paths


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
            "nmap_scan": NmapParser,
            "nikto": NiktoParser,
            "nikto_scan": NiktoParser,
            "dirb": DirbParser,
            "dirb_scan": DirbParser,
            "gobuster": DirbParser,  # 类似Dirb
            "ffuf": DirbParser,      # 类似Dirb
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