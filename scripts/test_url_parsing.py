#!/usr/bin/env python3
"""
测试URL解析功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.tool_coordinator import ToolChainCoordinator

def test_url_parsing():
    """测试URL解析"""
    coordinator = ToolChainCoordinator()
    
    test_cases = [
        "http://e579ae13-2404-401e-ac7b-17d68115f1a9.node5.buuoj.cn:81",
        "https://example.com:443",
        "http://example.com",
        "example.com:8080",
        "192.168.1.1:80",
        "192.168.1.1",
        "localhost:3000"
    ]
    
    print("测试URL解析功能:")
    print("=" * 80)
    
    for url in test_cases:
        result = coordinator._parse_target_url(url)
        print(f"输入: {url}")
        print(f"  主机名: {result['hostname']}")
        print(f"  端口: {result['port']}")
        print(f"  是URL: {result['is_url']}")
        print()
    
    print("测试工具参数构建:")
    print("=" * 80)
    
    # 测试Nmap参数构建
    test_url = "http://e579ae13-2404-401e-ac7b-17d68115f1a9.node5.buuoj.cn:81"
    print(f"测试Nmap参数构建 - 目标: {test_url}")
    
    from dataclasses import dataclass, field
    import time
    
    @dataclass
    class MockContext:
        chain_id: str = "test"
        target: str = test_url
        tools_executed: list = field(default_factory=list)
        current_state: dict = field(default_factory=dict)
        start_time: float = field(default_factory=time.time)
        end_time: float = None
        flags_found: list = field(default_factory=list)
    
    context = MockContext()
    params = {}
    
    nmap_params = coordinator._build_tool_parameters("nmap_scan", test_url, context, params)
    print(f"  Nmap参数: {nmap_params}")
    
    sqlmap_params = coordinator._build_tool_parameters("sqlmap_scan", test_url, context, params)
    print(f"  SQLMap参数: {sqlmap_params}")
    
    print("\n测试完成!")

if __name__ == "__main__":
    test_url_parsing()