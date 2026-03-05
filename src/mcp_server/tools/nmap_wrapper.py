#!/usr/bin/env python3
"""
Nmap工具包装器
提供高级的Nmap集成功能
"""
import asyncio
import json
import re
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.utils.logger import logger
from src.utils.config_manager import config


class NmapWrapper:
    """Nmap高级包装器"""
    
    def __init__(self):
        self.nmap_path = config.get("tools.nmap.windows_path", "nmap")
        self.logger = logger.getChild("nmap_wrapper")
        self.default_options = {
            "top_ports": 100,
            "script": "default",
            "version_intensity": 7,
            "os_detection": True,
            "traceroute": False,
            "timing_template": "T4"  # 激进扫描
        }
    
    async def scan(self, target: str, **kwargs) -> Dict[str, Any]:
        """
        执行Nmap扫描
        
        Args:
            target: 目标主机或网络
            **kwargs: 额外参数
            
        Returns:
            扫描结果
        """
        try:
            # 合并参数
            options = self.default_options.copy()
            options.update(kwargs)
            
            self.logger.info(f"开始Nmap扫描: {target}")
            
            # 构建命令
            cmd = self._build_command(target, options)
            
            # 创建临时文件用于XML输出
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.xml', delete=False) as tmp_file:
                output_file = tmp_file.name
                cmd.extend(["-oX", output_file])
            
            self.logger.debug(f"Nmap命令: {' '.join(cmd)}")
            
            # 执行命令
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # 等待完成（带超时）
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=options.get("timeout", 600)  # 默认10分钟超时
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "success": False,
                    "error": "扫描超时",
                    "target": target
                }
            
            # 解析结果
            result = self._parse_output(stdout, stderr, process.returncode, output_file)
            
            # 清理临时文件
            try:
                Path(output_file).unlink(missing_ok=True)
            except:
                pass
            
            return result
            
        except Exception as e:
            self.logger.error(f"Nmap扫描错误: {e}")
            return {
                "success": False,
                "error": str(e),
                "target": target
            }
    
    def _build_command(self, target: str, options: Dict[str, Any]) -> List[str]:
        """构建Nmap命令"""
        cmd = [self.nmap_path]
        
        # 添加扫描选项
        if options.get("top_ports"):
            cmd.extend(["--top-ports", str(options["top_ports"])])
        
        # 添加脚本扫描
        if options.get("script"):
            if options["script"] == "default":
                cmd.extend(["-sC"])  # 默认脚本
            elif options["script"] == "vuln":
                cmd.extend(["--script", "vuln"])
            elif options["script"] == "all":
                cmd.extend(["--script", "all"])
            else:
                cmd.extend(["--script", options["script"]])
        
        # 添加版本检测
        if options.get("version_intensity"):
            cmd.extend(["-sV", "--version-intensity", str(options["version_intensity"])])
        
        # 添加操作系统检测
        if options.get("os_detection"):
            cmd.extend(["-O"])
        
        # 添加路由追踪
        if options.get("traceroute"):
            cmd.append("--traceroute")
        
        # 添加时序模板
        if options.get("timing_template"):
            cmd.extend(["-T", options["timing_template"]])
        
        # 添加端口范围
        if options.get("ports"):
            cmd.extend(["-p", options["ports"]])
        
        # 添加扫描技术
        if options.get("scan_technique"):
            cmd.extend(["-s", options["scan_technique"]])
        
        # 添加目标
        cmd.append(target)
        
        return cmd
    
    def _parse_output(self, stdout: bytes, stderr: bytes, returncode: int, output_file: str) -> Dict[str, Any]:
        """解析Nmap输出"""
        stdout_str = stdout.decode('utf-8', errors='ignore')
        stderr_str = stderr.decode('utf-8', errors='ignore')
        
        result = {
            "success": returncode in [0, 1],  # Nmap返回1表示有警告但扫描完成
            "return_code": returncode,
            "stdout": stdout_str,
            "stderr": stderr_str,
            "hosts": [],
            "summary": {}
        }
        
        # 尝试从XML输出文件读取结果
        if Path(output_file).exists():
            try:
                xml_result = self._parse_xml_output(output_file)
                result.update(xml_result)
            except Exception as e:
                self.logger.warning(f"解析XML输出失败: {e}")
        
        # 从stdout提取信息
        self._extract_from_stdout(stdout_str, result)
        
        # 生成摘要
        total_hosts = len(result["hosts"])
        total_ports = sum(len(host.get("ports", [])) for host in result["hosts"])
        open_ports = sum(
            len([p for p in host.get("ports", []) if p.get("state") == "open"])
            for host in result["hosts"]
        )
        
        result["summary"] = {
            "total_hosts": total_hosts,
            "total_ports": total_ports,
            "open_ports": open_ports,
            "success": result["success"]
        }
        
        return result
    
    def _parse_xml_output(self, xml_file: str) -> Dict[str, Any]:
        """解析XML格式的Nmap输出"""
        result = {
            "hosts": [],
            "scan_info": {}
        }
        
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # 提取扫描信息
            scan_info = root.find("scaninfo")
            if scan_info is not None:
                result["scan_info"] = {
                    "type": scan_info.get("type", ""),
                    "protocol": scan_info.get("protocol", ""),
                    "num_services": scan_info.get("numservices", "")
                }
            
            # 提取主机信息
            for host in root.findall("host"):
                host_info = self._parse_host_element(host)
                if host_info:
                    result["hosts"].append(host_info)
            
        except Exception as e:
            self.logger.error(f"解析XML时出错: {e}")
        
        return result
    
    def _parse_host_element(self, host_element) -> Dict[str, Any]:
        """解析主机元素"""
        host_info = {
            "status": {},
            "addresses": [],
            "ports": [],
            "os": {},
            "hostnames": []
        }
        
        # 提取状态
        status = host_element.find("status")
        if status is not None:
            host_info["status"] = {
                "state": status.get("state", "unknown"),
                "reason": status.get("reason", "")
            }
        
        # 提取地址
        for addr in host_element.findall("address"):
            host_info["addresses"].append({
                "addr": addr.get("addr", ""),
                "addrtype": addr.get("addrtype", ""),
                "vendor": addr.get("vendor", "")
            })
        
        # 提取主机名
        for hostname in host_element.findall("hostnames/hostname"):
            host_info["hostnames"].append({
                "name": hostname.get("name", ""),
                "type": hostname.get("type", "")
            })
        
        # 提取端口
        ports_element = host_element.find("ports")
        if ports_element is not None:
            for port in ports_element.findall("port"):
                port_info = self._parse_port_element(port)
                if port_info:
                    host_info["ports"].append(port_info)
        
        # 提取操作系统信息
        os_element = host_element.find("os")
        if os_element is not None:
            os_matches = []
            for osmatch in os_element.findall("osmatch"):
                os_matches.append({
                    "name": osmatch.get("name", ""),
                    "accuracy": osmatch.get("accuracy", "")
                })
            host_info["os"] = {
                "matches": os_matches,
                "ports_used": []
            }
        
        return host_info
    
    def _parse_port_element(self, port_element) -> Dict[str, Any]:
        """解析端口元素"""
        port_info = {
            "port": port_element.get("portid", ""),
            "protocol": port_element.get("protocol", ""),
            "state": "unknown",
            "service": {},
            "scripts": []
        }
        
        # 提取状态
        state = port_element.find("state")
        if state is not None:
            port_info["state"] = state.get("state", "unknown")
        
        # 提取服务信息
        service = port_element.find("service")
        if service is not None:
            port_info["service"] = {
                "name": service.get("name", ""),
                "product": service.get("product", ""),
                "version": service.get("version", ""),
                "extrainfo": service.get("extrainfo", ""),
                "ostype": service.get("ostype", ""),
                "method": service.get("method", ""),
                "conf": service.get("conf", "")
            }
        
        # 提取脚本输出
        for script in port_element.findall("script"):
            script_info = {
                "id": script.get("id", ""),
                "output": script.get("output", ""),
                "elements": []
            }
            
            # 提取脚本元素
            for elem in script.findall("elem"):
                script_info["elements"].append({
                    "key": elem.get("key", ""),
                    "value": elem.text or ""
                })
            
            port_info["scripts"].append(script_info)
        
        return port_info
    
    def _extract_from_stdout(self, stdout: str, result: Dict[str, Any]) -> None:
        """从标准输出提取信息"""
        lines = stdout.split('\n')
        current_host = None
        
        for line in lines:
            line = line.strip()
            
            # 提取Nmap版本
            if "Nmap version" in line:
                result["nmap_version"] = line
            
            # 提取扫描开始时间
            elif "Starting Nmap" in line:
                result["scan_start"] = line
            
            # 提取主机发现
            elif "Nmap scan report for" in line:
                # 保存上一个主机
                if current_host:
                    result["hosts"].append(current_host)
                
                # 开始新主机
                host_match = re.search(r"Nmap scan report for (.+)", line)
                if host_match:
                    current_host = {
                        "target": host_match.group(1),
                        "ports": [],
                        "status": "up"
                    }
            
            # 提取端口信息
            elif re.match(r'^\d+/', line):
                if current_host:
                    port_match = re.match(r'(\d+)/(\w+)\s+(\w+)\s+(.+)', line)
                    if port_match:
                        port_info = {
                            "port": port_match.group(1),
                            "protocol": port_match.group(2),
                            "state": port_match.group(3),
                            "service": port_match.group(4)
                        }
                        current_host["ports"].append(port_info)
            
            # 提取扫描统计
            elif "Nmap done" in line:
                result["scan_end"] = line
                if current_host:
                    result["hosts"].append(current_host)
                    current_host = None
        
        # 确保最后一个主机被添加
        if current_host:
            result["hosts"].append(current_host)
    
    async def test_connection(self) -> bool:
        """测试Nmap连接"""
        try:
            process = await asyncio.create_subprocess_exec(
                self.nmap_path, "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                version = stdout.decode('utf-8', errors='ignore').strip()
                self.logger.info(f"Nmap版本: {version}")
                return True
            else:
                self.logger.warning(f"Nmap测试失败: {stderr.decode('utf-8', errors='ignore')}")
                return False
                
        except Exception as e:
            self.logger.error(f"Nmap连接测试错误: {e}")
            return False
    
    async def quick_scan(self, target: str) -> Dict[str, Any]:
        """快速扫描（常用端口）"""
        return await self.scan(
            target,
            top_ports=100,
            script="default",
            timing_template="T4"
        )
    
    async def full_scan(self, target: str) -> Dict[str, Any]:
        """完整扫描（所有端口）"""
        return await self.scan(
            target,
            ports="1-65535",
            script="vuln",
            version_intensity=9,
            os_detection=True,
            timing_template="T3"  # 正常速度
        )
    
    async def service_scan(self, target: str) -> Dict[str, Any]:
        """服务版本扫描"""
        return await self.scan(
            target,
            top_ports=1000,
            version_intensity=9,
            script="default",
            timing_template="T4"
        )


# 全局实例
nmap_wrapper = NmapWrapper()


async def test_nmap_wrapper():
    """测试Nmap包装器"""
    logger.info("测试Nmap包装器...")
    
    wrapper = NmapWrapper()
    
    # 测试连接
    connected = await wrapper.test_connection()
    if not connected:
        logger.error("Nmap连接测试失败")
        return False
    
    logger.info("Nmap连接测试成功")
    
    # 测试快速扫描（使用本地主机）
    test_target = "127.0.0.1"
    logger.info(f"测试快速扫描: {test_target}")
    
    result = await wrapper.quick_scan(test_target)
    
    logger.info(f"扫描结果: {json.dumps(result['summary'], indent=2, ensure_ascii=False)}")
    
    return result["success"]


if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(test_nmap_wrapper())
    exit_code = 0 if success else 1
    sys.exit(exit_code)