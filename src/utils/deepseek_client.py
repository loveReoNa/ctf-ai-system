"""
DeepSeek API客户端
"""
import os
from typing import Dict, Any, Optional, List
from openai import OpenAI
from openai.types.chat import ChatCompletion

from src.utils.config_manager import config
from src.utils.logger import logger

class DeepSeekClient:
    """DeepSeek API客户端"""
    
    def __init__(self):
        self.api_key = config.get("ai.api_key")
        self.base_url = config.get("ai.base_url", "https://api.deepseek.com")
        self.model = config.get("ai.model", "deepseek-chat")
        self.temperature = config.get("ai.temperature", 0.7)
        self.max_tokens = config.get("ai.max_tokens", 2000)
        self.timeout = config.get("ai.timeout", 30)
        
        # 初始化OpenAI客户端（兼容DeepSeek API）
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout
        )
        
        logger.info(f"DeepSeek客户端初始化完成，模型: {self.model}")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        发送聊天补全请求
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否使用流式响应
        
        Returns:
            响应结果
        """
        try:
            # 使用配置的参数或传入的参数
            temp = temperature if temperature is not None else self.temperature
            tokens = max_tokens if max_tokens is not None else self.max_tokens
            
            logger.debug(f"发送DeepSeek API请求，模型: {self.model}, 温度: {temp}")
            
            # 调用API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temp,
                max_tokens=tokens,
                stream=stream
            )
            
            if stream:
                # 处理流式响应
                return self._handle_stream_response(response)
            else:
                # 处理普通响应
                return self._handle_response(response)
                
        except Exception as e:
            logger.error(f"DeepSeek API调用失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": None
            }
    
    def _handle_response(self, response: ChatCompletion) -> Dict[str, Any]:
        """处理普通响应"""
        content = response.choices[0].message.content
        usage = response.usage
        
        result = {
            "success": True,
            "content": content,
            "model": response.model,
            "usage": {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens
            },
            "finish_reason": response.choices[0].finish_reason
        }
        
        logger.debug(f"DeepSeek响应接收，token使用: {usage.total_tokens}")
        return result
    
    def _handle_stream_response(self, response) -> Dict[str, Any]:
        """处理流式响应"""
        full_content = ""
        
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                full_content += content
        
        return {
            "success": True,
            "content": full_content,
            "model": self.model,
            "stream": True
        }
    
    async def analyze_ctf_challenge(
        self,
        challenge_description: str,
        target_url: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        分析CTF挑战
        
        Args:
            challenge_description: 挑战描述
            target_url: 目标URL
            context: 额外上下文
        
        Returns:
            分析结果
        """
        system_prompt = """你是一个专业的网络安全专家和CTF选手。请分析给定的CTF挑战，并提供攻击策略建议。

请按以下格式输出：
1. 挑战类型分析
2. 潜在漏洞分析
3. 攻击步骤建议
4. 推荐工具
5. 风险评估

保持回答专业、简洁、实用。"""
        
        user_prompt = f"""CTF挑战分析请求：

挑战描述：{challenge_description}
目标URL：{target_url}

{context if context else '无额外上下文'}"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return await self.chat_completion(messages)
    
    async def generate_attack_payload(
        self,
        vulnerability_type: str,
        target_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成攻击载荷
        
        Args:
            vulnerability_type: 漏洞类型（如SQL注入、XSS等）
            target_info: 目标信息
        
        Returns:
            生成的攻击载荷
        """
        system_prompt = f"""你是一个专业的渗透测试专家。请为{vulnerability_type}漏洞生成有效的攻击载荷。

要求：
1. 生成3-5个不同的有效载荷
2. 说明每个载荷的原理
3. 提供使用建议
4. 包含绕过WAF的技巧（如果适用）"""
        
        user_prompt = f"""为目标生成{vulnerability_type}攻击载荷：

目标信息：{target_info}
漏洞类型：{vulnerability_type}

请生成专业、有效的攻击载荷。"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return await self.chat_completion(messages)

# 全局DeepSeek客户端实例
deepseek_client = DeepSeekClient()
