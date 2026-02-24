#!/usr/bin/env python3
"""
验证DeepSeek配置是否正确
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config_manager import config
from src.utils.deepseek_client import DeepSeekClient

def validate_deepseek_config():
    """验证DeepSeek配置"""
    print("=" * 50)
    print("DeepSeek配置验证")
    print("=" * 50)
    
    # 检查环境变量
    print("\n1. 检查环境变量:")
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    if deepseek_key:
        print(f"  ✓ DEEPSEEK_API_KEY: {'*' * 8}{deepseek_key[-4:]}")
    else:
        print("  ✗ DEEPSEEK_API_KEY 未设置")
        return False
    
    # 检查配置文件
    print("\n2. 检查配置文件:")
    ai_config = config.get("ai", {})
    if ai_config:
        print(f"  ✓ AI配置加载成功")
        print(f"    提供商: {ai_config.get('provider')}")
        print(f"    模型: {ai_config.get('model')}")
        print(f"    API地址: {ai_config.get('base_url')}")
    else:
        print("  ✗ AI配置加载失败")
        return False
    
    # 测试API连接
    print("\n3. 测试DeepSeek API连接:")
    try:
        client = DeepSeekClient()
        print("  ✓ DeepSeek客户端初始化成功")
        
        # 发送简单的测试请求
        test_messages = [
            {"role": "system", "content": "你是一个有帮助的助手。"},
            {"role": "user", "content": "请回复'Hello from CTF AI System!'"}
        ]
        
        print("  正在发送测试请求...")
        # 注意：这里需要异步调用，简化版本先不实际发送
        print("  ⚠ 跳过实际API调用测试（避免消耗API额度）")
        print("  提示：要完整测试，请运行 test_deepseek_api.py")
        
    except Exception as e:
        print(f"  ✗ DeepSeek客户端初始化失败: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ DeepSeek配置验证通过！")
    print("\n下一步:")
    print("1. 确保 .env 文件中的DEEPSEEK_API_KEY正确")
    print("2. 运行 test_deepseek_api.py 进行完整API测试")
    print("3. 开始开发MCP服务器集成")
    
    return True

def main():
    """主函数"""
    if not validate_deepseek_config():
        print("\n❌ 配置验证失败，请检查上述问题。")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
