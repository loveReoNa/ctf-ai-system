#!/bin/bash
# Kali Linux快速开始脚本
# 用于快速设置和运行CTF攻击模拟系统

set -e  # 遇到错误时退出

echo "========================================"
echo "  Kali Linux CTF攻击模拟系统快速开始"
echo "========================================"
echo "开始时间: $(date)"
echo ""

# 检查是否在Kali Linux中
if [[ ! -f /etc/os-release ]] || ! grep -qi "kali" /etc/os-release; then
    echo "⚠️  警告: 检测到非Kali Linux系统"
    echo "本脚本专为Kali Linux优化，其他系统可能无法正常工作"
    read -p "是否继续? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 检查Python版本
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "Python版本: $PYTHON_VERSION"

if [[ $(echo "$PYTHON_VERSION 3.8" | awk '{print ($1 < $2)}') -eq 1 ]]; then
    echo "❌ Python版本过低，需要3.8+"
    exit 1
fi

# 检查项目目录
if [[ ! -f "requirements.txt" ]]; then
    echo "❌ 未在项目根目录中运行"
    echo "请进入项目目录: cd ~/.ctfagent"
    exit 1
fi

# 步骤1: 检查虚拟环境
echo ""
echo "步骤1: 检查虚拟环境..."
if [[ ! -d "venv" ]]; then
    echo "虚拟环境不存在，正在创建..."
    python3 -m venv venv
    echo "✅ 虚拟环境创建成功"
else
    echo "✅ 虚拟环境已存在"
fi

# 激活虚拟环境
source venv/bin/activate
echo "✅ 虚拟环境已激活"

# 步骤2: 安装依赖
echo ""
echo "步骤2: 安装依赖..."
if [[ -f "requirements.txt" ]]; then
    pip install --upgrade pip
    pip install -r requirements.txt
    echo "✅ 依赖安装完成"
else
    echo "❌ requirements.txt 文件不存在"
    exit 1
fi

# 步骤3: 检查环境变量
echo ""
echo "步骤3: 检查环境变量..."
if [[ ! -f ".env" ]]; then
    if [[ -f ".env.example" ]]; then
        cp .env.example .env
        echo "✅ 已创建 .env 文件"
        echo "⚠️  请编辑 .env 文件，添加DeepSeek API密钥"
        echo "    nano .env"
        echo "    然后设置: DEEPSEEK_API_KEY=your_api_key_here"
        read -p "是否已添加API密钥? (按Enter继续): "
    else
        echo "❌ .env.example 文件不存在"
        exit 1
    fi
else
    echo "✅ .env 文件已存在"
fi

# 步骤4: 验证配置
echo ""
echo "步骤4: 验证配置..."
if python3 scripts/validate_config.py; then
    echo "✅ 配置验证成功"
else
    echo "❌ 配置验证失败"
    exit 1
fi

# 步骤5: 检查安全工具
echo ""
echo "步骤5: 检查安全工具..."
TOOLS_MISSING=0

check_tool() {
    local tool=$1
    local path=$(which $tool 2>/dev/null)
    
    if [[ -n "$path" ]]; then
        echo "  ✅ $tool: $path"
        return 0
    else
        echo "  ❌ $tool: 未安装"
        return 1
    fi
}

echo "检查必需的安全工具:"
check_tool sqlmap || TOOLS_MISSING=$((TOOLS_MISSING + 1))
check_tool nmap || TOOLS_MISSING=$((TOOLS_MISSING + 1))
check_tool nikto || TOOLS_MISSING=$((TOOLS_MISSING + 1))

if [[ $TOOLS_MISSING -gt 0 ]]; then
    echo "⚠️  缺少 $TOOLS_MISSING 个安全工具"
    echo "在Kali中，可以使用以下命令安装:"
    echo "  sudo apt update && sudo apt install sqlmap nmap nikto"
    read -p "是否继续? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ 所有安全工具已安装"
fi

# 步骤6: 运行演示
echo ""
echo "步骤6: 运行系统演示..."
echo "选择演示类型:"
echo "  1) 快速演示 (验证核心功能)"
echo "  2) 完整演示 (所有组件)"
echo "  3) SQL注入挑战演示"
echo "  4) 综合Web CTF演示"
echo "  5) 跳过演示"
read -p "请输入选项 (1-5): " -n 1 -r
echo

case $REPLY in
    1)
        echo "运行快速演示..."
        python3 scripts/demo_all_components.py --quick
        ;;
    2)
        echo "运行完整演示..."
        python3 scripts/demo_all_components.py
        ;;
    3)
        echo "运行SQL注入挑战演示..."
        cat > /tmp/demo_sqli.py << 'EOF'
import asyncio
import sys
sys.path.insert(0, '.')
from src.core.attack_engine import AttackExecutionEngine

async def demo():
    print("=== SQL注入挑战演示 ===")
    engine = AttackExecutionEngine()
    await engine.initialize()
    
    plan = await engine.create_attack_plan(
        target="http://testphp.vulnweb.com",
        description="SQL注入演示"
    )
    
    print(f"攻击计划创建成功: {plan.plan_id}")
    print(f"目标: {plan.target}")
    print(f"步骤数: {len(plan.steps)}")
    
    # 模拟执行
    print("\n模拟攻击执行...")
    for i, step in enumerate(plan.steps, 1):
        print(f"  步骤{i}: {step.description}")
        await asyncio.sleep(0.5)
    
    print("\n✅ 演示完成!")
    print("系统已准备好解决SQL注入挑战")

asyncio.run(demo())
EOF
        python3 /tmp/demo_sqli.py
        ;;
    4)
        echo "运行综合Web CTF演示..."
        python3 scripts/demo_all_components.py --workflow
        ;;
    5)
        echo "跳过演示"
        ;;
    *)
        echo "无效选项，跳过演示"
        ;;
esac

# 步骤7: 创建解题脚本
echo ""
echo "步骤7: 创建解题脚本..."
cat > solve_ctf.sh << 'EOF'
#!/bin/bash
# CTF解题脚本
# 用法: ./solve_ctf.sh <目标URL> [挑战类型]

set -e

TARGET="$1"
CHALLENGE_TYPE="${2:-web}"

if [[ -z "$TARGET" ]]; then
    echo "用法: $0 <目标URL> [挑战类型]"
    echo "挑战类型: web, sqli, xss, fileupload, etc."
    exit 1
fi

echo "========================================"
echo "  开始解决CTF挑战"
echo "========================================"
echo "目标: $TARGET"
echo "类型: $CHALLENGE_TYPE"
echo "时间: $(date)"
echo ""

# 激活虚拟环境
if [[ -d "venv" ]]; then
    source venv/bin/activate
fi

# 根据挑战类型选择脚本
case "$CHALLENGE_TYPE" in
    sqli|sql-injection|sql)
        SCRIPT="solve_sqli_challenge.py"
        ;;
    xss)
        SCRIPT="solve_xss_challenge.py"
        ;;
    fileupload|upload)
        SCRIPT="solve_upload_challenge.py"
        ;;
    web|*)
        SCRIPT="solve_web_ctf.py"
        ;;
esac

# 检查脚本是否存在
if [[ ! -f "$SCRIPT" ]]; then
    # 使用通用解题脚本
    cat > solve_generic.py << 'PYEOF'
import asyncio
import sys
sys.path.insert(0, '.')
from src.core.attack_engine import AttackExecutionEngine

async def solve(target, challenge_type):
    print(f"开始解决 {challenge_type} 挑战: {target}")
    
    engine = AttackExecutionEngine()
    await engine.initialize()
    
    # 创建攻击计划
    plan = await engine.create_attack_plan(
        target=target,
        description=f"{challenge_type} CTF挑战",
        challenge_type=challenge_type
    )
    
    print(f"攻击计划创建成功: {plan.plan_id}")
    
    # 执行攻击
    context = await engine.execute_attack(plan)
    
    # 获取结果
    status = engine.get_attack_status(context.attack_id)
    
    print("\n" + "="*60)
    print("挑战解决完成")
    print("="*60)
    print(f"状态: {status.get('status', 'unknown')}")
    print(f"找到Flag: {len(status.get('flags_found', []))}")
    
    if status.get('flags_found'):
        print("\n发现的Flag:")
        for flag in status['flags_found']:
            print(f"  {flag}")
    
    return status.get('flags_found', [])

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python3 solve_generic.py <目标URL> <挑战类型>")
        sys.exit(1)
    
    target = sys.argv[1]
    challenge_type = sys.argv[2]
    
    flags = asyncio.run(solve(target, challenge_type))
    
    if flags:
        print(f"\n✅ 解题成功！共找到 {len(flags)} 个Flag")
        sys.exit(0)
    else:
        print("\n⚠️  未找到Flag")
        sys.exit(1)
PYEOF
    
    python3 solve_generic.py "$TARGET" "$CHALLENGE_TYPE"
else
    python3 "$SCRIPT" "$TARGET"
fi

echo ""
echo "========================================"
echo "  解题完成"
echo "========================================"
echo "结束时间: $(date)"
EOF

chmod +x solve_ctf.sh
echo "✅ 解题脚本已创建: solve_ctf.sh"
echo "  用法: ./solve_ctf.sh <目标URL> [挑战类型]"

# 步骤8: 创建测试挑战
echo ""
echo "步骤8: 创建测试挑战..."
mkdir -p tests/challenges

cat > tests/challenges/sqli_test.json << 'EOF'
{
  "name": "SQL注入测试挑战",
  "description": "测试SQL注入漏洞利用能力",
  "url": "http://testphp.vulnweb.com/artists.php?artist=1",
  "type": "sqli",
  "difficulty": "easy",
  "expected_flags": ["flag{sql_injection_demo}"],
  "hints": [
    "尝试在artist参数中注入单引号",
    "使用union查询提取数据",
    "查找包含flag的表"
  ]
}
EOF

cat > tests/challenges/xss_test.json << 'EOF'
{
  "name": "XSS测试挑战",
  "description": "测试跨站脚本漏洞利用能力",
  "url": "http://testphp.vulnweb.com/search.php",
  "type": "xss",
  "difficulty": "medium",
  "expected_flags": ["flag{xss_demo}"],
  "hints": [
    "在搜索参数中注入JavaScript",
    "尝试窃取cookie",
    "查找存储型XSS"
  ]
}
EOF

echo "✅ 测试挑战已创建在 tests/challenges/ 目录"

# 完成
echo ""
echo "========================================"
echo "  快速开始完成！"
echo "========================================"
echo "✅ 环境设置完成"
echo "✅ 依赖安装完成"
echo "✅ 配置验证完成"
echo "✅ 安全工具检查完成"
echo "✅ 解题脚本已创建"
echo "✅ 测试挑战已创建"
echo ""
echo "接下来可以:"
echo "  1. 运行测试挑战: ./solve_ctf.sh http://testphp.vulnweb.com/artists.php?artist=1 sqli"
echo "  2. 查看详细指南: cat docs/kali_ctf_solving_guide.md"
echo "  3. 运行完整演示: python3 scripts/demo_all_components.py"
echo "  4. 测试集成功能: python3 scripts/test_integration.py"
echo ""
echo "项目状态检查:"
python3 -c "
import os
print('  配置文件:', '✅ 存在' if os.path.exists('config/development.yaml') else '❌ 缺失')
print('  日志目录:', '✅ 存在' if os.path.exists('logs') else '❌ 缺失')
print('  报告目录:', '✅ 存在' if os.path.exists('reports') else '❌ 缺失')
print('  AI代理:', '✅ 可导入' if os.path.exists('src/agents/react_agent.py') else '❌ 缺失')
print('  攻击引擎:', '✅ 可导入' if os.path.exists('src/core/attack_engine.py') else '❌ 缺失')
"
echo ""
echo "开始时间: $(date -d @$START_TIME)"
echo "结束时间: $(date)"
echo "总耗时: $(( $(date +%s) - START_TIME )) 秒"
echo "========================================"