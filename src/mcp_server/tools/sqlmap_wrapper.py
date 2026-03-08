#!/usr/bin/env python3
"""
SQLMap工具包装器
提供高级的SQLMap集成功能
"""
import asyncio
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
import xml.etree.ElementTree as ET

from src.utils.logger import logger
from src.utils.config_manager import config


class SQLMapWrapper:
    """SQLMap高级包装器"""
    
    def __init__(self):
        # 根据操作系统选择正确的路径
        import platform
        system = platform.system()
        
        if system == "Windows":
            self.sqlmap_path = config.get("tools.sqlmap.windows_path", "sqlmap")
        else:
            # Linux/macOS/Kali
            self.sqlmap_path = config.get("tools.sqlmap.path", "sqlmap")
            
        self.logger = logger.getChild("sqlmap_wrapper")
        self.default_options = {
            "batch": True,  # 无需交互
            "random_agent": True,  # 随机User-Agent
            "level": 1,
            "risk": 1,
            "threads": 10
        }
    
    async def scan(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        执行SQLMap扫描
        
        Args:
            url: 目标URL
            **kwargs: 额外参数
        
        Returns:
            扫描结果
        """
        try:
            # 合并参数
            options = self.default_options.copy()
            options.update(kwargs)
            
            self.logger.info(f"开始SQLMap扫描: {url}")
            
            # 构建命令
            cmd = self._build_command(url, options)
            
            # 创建临时目录用于输出
            import tempfile
            output_dir = tempfile.mkdtemp(prefix="sqlmap_")
            cmd.extend(["--output-dir", output_dir])
            
            self.logger.debug(f"SQLMap命令: {' '.join(cmd)}")
            
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
                    timeout=options.get("timeout", 300)  # 默认5分钟超时
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "success": False,
                    "error": "扫描超时",
                    "url": url
                }
            
            # 解析结果
            result = self._parse_output(stdout, stderr, process.returncode, output_dir)
            
            # 清理临时目录
            try:
                import shutil
                shutil.rmtree(output_dir, ignore_errors=True)
            except:
                pass
            
            return result
            
        except Exception as e:
            self.logger.error(f"SQLMap扫描错误: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": url
            }
    
    def _build_command(self, url: str, options: Dict[str, Any]) -> List[str]:
        """构建SQLMap命令"""
        cmd = [self.sqlmap_path, "-u", url]
        
        # 添加选项
        if options.get("batch"):
            cmd.append("--batch")
        
        if options.get("random_agent"):
            cmd.append("--random-agent")
        
        if options.get("level"):
            cmd.append(f"--level={options['level']}")
        
        if options.get("risk"):
            cmd.append(f"--risk={options['risk']}")
        
        if options.get("threads"):
            cmd.append(f"--threads={options['threads']}")
        
        # 添加方法特定参数
        if options.get("method") == "POST" and options.get("data"):
            cmd.extend(["--data", options["data"]])
        
        if options.get("cookie"):
            cmd.extend(["--cookie", options["cookie"]])
        
        if options.get("headers"):
            headers_file = self._create_headers_file(options["headers"])
            cmd.extend(["--headers-file", headers_file])
        
        # 添加扫描技术
        if options.get("techniques"):
            cmd.extend(["--technique", options["techniques"]])
        
        # 添加数据库类型
        if options.get("dbms"):
            cmd.extend(["--dbms", options["dbms"]])
        
        return cmd
    
    def _create_headers_file(self, headers: Dict[str, str]) -> str:
        """创建头部文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for key, value in headers.items():
                f.write(f"{key}: {value}\n")
            return f.name
    
    def _parse_output(self, stdout: bytes, stderr: bytes, returncode: int, output_dir: str) -> Dict[str, Any]:
        """解析SQLMap输出"""
        stdout_str = stdout.decode('utf-8', errors='ignore')
        stderr_str = stderr.decode('utf-8', errors='ignore')
        
        result = {
            "success": returncode == 0,
            "return_code": returncode,
            "stdout": stdout_str,
            "stderr": stderr_str,
            "vulnerabilities": [],
            "summary": {}
        }
        
        # 从stdout提取信息
        self._extract_from_stdout(stdout_str, result)
        
        # 生成摘要
        result["summary"] = {
            "vulnerability_count": len(result["vulnerabilities"]),
            "vulnerability_types": list(set(v.get("type", "") for v in result["vulnerabilities"])),
            "success": result["success"]
        }
        
        return result
    
    def _extract_from_stdout(self, stdout: str, result: Dict[str, Any]) -> None:
        """从标准输出提取信息"""
        # 提取注入点
        injection_patterns = [
            r"Parameter: (.+?) \((.+?)\)",
            r"Type: (.+?)",
            r"Title: (.+?)",
            r"Payload: (.+?)"
        ]
        
        lines = stdout.split('\n')
        current_vuln = {}
        
        for line in lines:
            line = line.strip()
            
            # 检查是否找到注入点
            if "sqlmap identified the following injection point" in line.lower():
                if current_vuln:
                    result["vulnerabilities"].append(current_vuln)
                    current_vuln = {}
            
            # 提取参数信息
            match = re.search(r"Parameter: (.+?) \((.+?)\)", line)
            if match:
                current_vuln["parameter"] = match.group(1)
                current_vuln["injection_type"] = match.group(2)
            
            # 提取漏洞类型
            match = re.search(r"Type: (.+?)", line)
            if match:
                current_vuln["type"] = match.group(1)
            
            # 提取标题
            match = re.search(r"Title: (.+?)", line)
            if match:
                current_vuln["title"] = match.group(1)
            
            # 提取载荷
            match = re.search(r"Payload: (.+?)", line)
            if match:
                current_vuln["payload"] = match.group(1)
    
    async def test_connection(self) -> bool:
        """测试SQLMap连接"""
        try:
            process = await asyncio.create_subprocess_exec(
                self.sqlmap_path, "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                version = stdout.decode('utf-8', errors='ignore').strip()
                self.logger.info(f"SQLMap版本: {version}")
                return True
            else:
                self.logger.warning(f"SQLMap测试失败: {stderr.decode('utf-8', errors='ignore')}")
                return False
                
        except Exception as e:
            self.logger.error(f"SQLMap连接测试错误: {e}")
            return False
    
    async def get_dbs(self, url: str, **kwargs) -> List[str]:
        """获取数据库列表"""
        try:
            options = self.default_options.copy()
            options.update(kwargs)
            options["dbs"] = True
            
            cmd = self._build_command(url, options)
            cmd.append("--dbs")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            output = stdout.decode('utf-8', errors='ignore')
            
            # 提取数据库名称
            dbs = []
            for line in output.split('\n'):
                if "available databases" in line.lower():
                    continue
                if "[" in line and "]" in line:
                    db_match = re.search(r'\[\*\] (.+)', line)
                    if db_match:
                        dbs.append(db_match.group(1).strip())
            
            return dbs
            
        except Exception as e:
            self.logger.error(f"获取数据库列表失败: {e}")
            return []
    
    async def get_tables(self, url: str, database: str, **kwargs) -> List[str]:
        """获取表列表"""
        try:
            options = self.default_options.copy()
            options.update(kwargs)
            
            cmd = self._build_command(url, options)
            cmd.extend(["-D", database, "--tables"])
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            output = stdout.decode('utf-8', errors='ignore')
            
            # 提取表名称
            tables = []
            for line in output.split('\n'):
                if "Database:" in line:
                    continue
                if "[" in line and "]" in line:
                    table_match = re.search(r'\[\*\] (.+)', line)
                    if table_match:
                        tables.append(table_match.group(1).strip())
            
            return tables
            
        except Exception as e:
            self.logger.error(f"获取表列表失败: {e}")
            return []


# 全局实例
sqlmap_wrapper = SQLMapWrapper()


async def test_sqlmap_wrapper():
    """测试SQLMap包装器"""
    logger.info("测试SQLMap包装器...")
    
    wrapper = SQLMapWrapper()
    
    # 测试连接
    connected = await wrapper.test_connection()
    if not connected:
        logger.error("SQLMap连接测试失败")
        return False
    
    logger.info("SQLMap连接测试成功")
    
    # 测试扫描（使用测试URL）
    test_url = "http://testphp.vulnweb.com/artists.php?artist=1"
    logger.info(f"测试扫描: {test_url}")
    
    result = await wrapper.scan(
        test_url,
        level=1,
        risk=1,
        timeout=60
    )
    
    logger.info(f"扫描结果: {json.dumps(result['summary'], indent=2, ensure_ascii=False)}")
    
    return result["success"]


if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(test_sqlmap_wrapper())
    exit_code = 0 if success else 1
    sys.exit(exit_code)