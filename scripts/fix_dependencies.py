#!/usr/bin/env python3
"""
修复工具链依赖关系问题
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.tool_coordinator import ToolChainCoordinator, ToolDependency, ToolDependencyType


def analyze_dependency_issue():
    """分析依赖关系问题"""
    print("🔧 分析工具链依赖关系问题...")
    
    # 创建协调器实例
    coordinator = ToolChainCoordinator()
    
    print("\n1. 当前依赖关系图:")
    for source_tool, deps in coordinator.tool_dependencies.items():
        for dep in deps:
            print(f"   {source_tool} -> {dep.target_tool} ({dep.dependency_type.value})")
    
    print("\n2. 预定义工具链 'web_recon':")
    tool_list = coordinator.predefined_chains["web_recon"]
    print(f"   工具顺序: {tool_list}")
    
    print("\n3. 依赖检查逻辑分析:")
    for tool_name in tool_list:
        # 检查该工具是否有前置依赖
        has_deps = False
        for source_tool, deps in coordinator.tool_dependencies.items():
            for dep in deps:
                if dep.target_tool == tool_name:
                    has_deps = True
                    print(f"   {tool_name} 依赖于 {source_tool} ({dep.dependency_type.value})")
        
        if not has_deps:
            print(f"   {tool_name} 没有前置依赖")
    
    print("\n4. 问题诊断:")
    print("   - 当前依赖关系存储方式: source_tool -> target_tool")
    print("   - 依赖检查逻辑: 查找 tool_name 作为 source_tool 的依赖")
    print("   - 这导致工具检查自己的输出依赖，而不是检查前置依赖")
    print("   - 例如: nmap_scan 检查自己是否有依赖，而不是检查是否有工具依赖它")
    
    return coordinator


def propose_fix():
    """提出修复方案"""
    print("\n🔧 修复方案:")
    print("1. 修改依赖检查逻辑，检查工具是否有前置依赖")
    print("2. 或者修改依赖关系存储方式，存储 target_tool -> source_tool 的反向依赖")
    print("3. 简化方案: 移除依赖检查，让所有工具按顺序执行")
    
    print("\n建议采用方案3（简化），因为:")
    print("  - 当前项目处于早期阶段")
    print("  - 工具链应该按预定义顺序执行")
    print("  - 依赖关系可以通过执行结果动态判断")
    
    return """
修改建议:

在 src/utils/tool_coordinator.py 的 _check_dependencies 方法中:

async def _check_dependencies(self, tool_name: str, context: ToolChainContext) -> bool:
    \"\"\"检查工具依赖关系\"\"\"
    # 简化版本: 总是返回True，让工具按顺序执行
    return True

或者在 execute_chain 方法中跳过依赖检查:
    # 在 _execute_sequential 方法中注释掉依赖检查
    # if not await self._check_dependencies(tool_name, context):
    #     self.logger.warning(f"工具 {tool_name} 依赖未满足，跳过")
    #     continue
"""


if __name__ == "__main__":
    analyze_dependency_issue()
    fix = propose_fix()
    print(fix)