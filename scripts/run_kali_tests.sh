#!/bin/bash
# Kali Linux完整测试脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# 检查是否在项目目录
check_project_dir() {
    if [ ! -f "requirements.txt" ] || [ ! -d "src" ]; then
        print_error "请在项目根目录运行此脚本"
        echo "项目根目录应包含: requirements.txt 和 src/ 目录"
        exit 1
    fi
    print_success "项目目录检查通过"
}

# 检查虚拟环境
check_venv() {
    if [ -d "venv" ]; then
        source venv/bin/activate
        if [[ "$VIRTUAL_ENV" != "" ]]; then
            print_success "虚拟环境已激活: $VIRTUAL_ENV"
        else
            print_error "虚拟环境激活失败"
            exit 1
        fi
    else
        print_error "虚拟环境不存在，请先运行 setup_kali_venv.sh"
        exit 1
    fi
}

# 运行测试函数
run_test() {
    local test_name=$1
    local test_command=$2
    local test_file=$3
    
    echo ""
    print_header "测试: $test_name"
    
    if [ -n "$test_file" ] && [ ! -f "$test_file" ]; then
        print_error "测试文件不存在: $test_file"
        return 1
    fi
    
    if eval "$test_command"; then
        print_success "$test_name 通过"
        return 0
    else
        print_error "$test_name 失败"
        return 1
    fi
}

# 主函数
main() {
    echo ""
    print_header "Kali Linux完整测试套件"
    echo "开始时间: $(date)"
    echo ""
    
    # 检查环境
    check_project_dir
    check_venv
    
    # 测试结果计数器
    local passed=0
    local failed=0
    local total=0
    
    # 测试1: 环境验证
    if run_test "环境验证" "python3 scripts/verify_kali_environment.py" "scripts/verify_kali_environment.py"; then
        ((passed++))
    else
        ((failed++))
    fi
    ((total++))
    
    # 测试2: 配置验证
    if run_test "配置验证" "python3 scripts/validate_config.py" "scripts/validate_config.py"; then
        ((passed++))
    else
        ((failed++))
    fi
    ((total++))
    
    # 测试3: Kali准备测试
    if run_test "Kali准备测试" "python3 scripts/test_kali_preparedness.py" "scripts/test_kali_preparedness.py"; then
        ((passed++))
    else
        ((failed++))
    fi
    ((total++))
    
    # 测试4: MCP服务器测试
    if run_test "MCP服务器测试" "python3 scripts/test_mcp_server.py" "scripts/test_mcp_server.py"; then
        ((passed++))
    else
        ((failed++))
    fi
    ((total++))
    
    # 测试5: AI代理测试
    if run_test "AI代理测试" "python3 scripts/test_react_agent.py" "scripts/test_react_agent.py"; then
        ((passed++))
    else
        ((failed++))
    fi
    ((total++))
    
    # 测试6: 安全工具验证
    if run_test "安全工具验证" "python3 -c \"
import asyncio
import sys
sys.path.insert(0, '.')
from src.mcp_server.tools.sqlmap_wrapper import SQLMapWrapper

async def test():
    wrapper = SQLMapWrapper()
    connected = await wrapper.test_connection()
    if connected:
        print('✅ SQLMap连接成功')
        return True
    else:
        print('❌ SQLMap连接失败')
        return False

result = asyncio.run(test())
exit(0 if result else 1)
\"" ""; then
        ((passed++))
    else
        ((failed++))
    fi
    ((total++))
    
    # 显示总结
    echo ""
    print_header "测试结果总结"
    echo "结束时间: $(date)"
    echo ""
    echo "测试统计:"
    echo "  总测试数: $total"
    echo "  通过: $passed"
    echo "  失败: $failed"
    echo ""
    
    # 计算通过率
    local percentage=0
    if [ $total -gt 0 ]; then
        percentage=$((passed * 100 / total))
    fi
    
    echo "通过率: $percentage%"
    echo ""
    
    if [ $failed -eq 0 ]; then
        print_success "🎉 所有测试通过！系统准备就绪。"
        echo ""
        echo "下一步建议:"
        echo "  1. 运行演示: python scripts/demo_mcp_server.py"
        echo "  2. 启动服务器: python scripts/start_mcp_server.py"
        echo "  3. 开始实际CTF挑战测试"
    elif [ $percentage -ge 80 ]; then
        print_info "⚠️  大部分测试通过 ($percentage%)，系统基本可用。"
        echo ""
        echo "需要关注的失败测试:"
        if [ $failed -gt 0 ]; then
            echo "  - 请检查上述失败的测试"
        fi
    else
        print_error "❌ 测试通过率较低 ($percentage%)，需要修复问题。"
        echo ""
        echo "建议操作:"
        echo "  1. 检查错误日志: tail -f logs/ctf_ai.log"
        echo "  2. 验证配置文件: python scripts/validate_config.py --verbose"
        echo "  3. 重新安装依赖: pip install -r requirements.txt"
    fi
    
    echo ""
    print_header "测试完成"
    
    # 返回适当的退出码
    if [ $failed -eq 0 ]; then
        return 0
    else
        return 1
    fi
}

# 运行主函数
main "$@"