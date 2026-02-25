#!/bin/bash
# Kali Linux虚拟环境设置脚本
# 解决Python外部管理环境问题

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否在项目目录
check_project_dir() {
    if [ ! -f "requirements.txt" ] || [ ! -d "src" ]; then
        print_error "请在项目根目录运行此脚本"
        echo "项目根目录应包含: requirements.txt 和 src/ 目录"
        exit 1
    fi
    print_info "项目目录检查通过"
}

# 安装必要系统包
install_system_packages() {
    print_info "安装系统必要包..."
    sudo apt update
    sudo apt install python3-venv python3-pip git -y
    print_info "系统包安装完成"
}

# 创建虚拟环境
create_venv() {
    print_info "创建Python虚拟环境..."
    
    if [ -d "venv" ]; then
        print_warning "虚拟环境已存在，是否重新创建？"
        read -p "重新创建将删除现有环境 (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf venv
            python3 -m venv venv
            print_info "虚拟环境已重新创建"
        else
            print_info "使用现有虚拟环境"
        fi
    else
        python3 -m venv venv
        print_info "虚拟环境创建完成"
    fi
}

# 激活虚拟环境
activate_venv() {
    print_info "激活虚拟环境..."
    source venv/bin/activate
    
    # 验证激活
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        print_info "虚拟环境激活成功: $VIRTUAL_ENV"
        echo "Python路径: $(which python)"
        echo "Pip路径: $(which pip)"
    else
        print_error "虚拟环境激活失败"
        exit 1
    fi
}

# 安装Python依赖
install_dependencies() {
    print_info "安装Python依赖..."
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装依赖
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_info "依赖安装完成"
    else
        print_error "requirements.txt 文件不存在"
        exit 1
    fi
}

# 配置环境变量
setup_environment() {
    print_info "配置环境变量..."
    
    if [ ! -f ".env" ] && [ -f ".env.example" ]; then
        cp .env.example .env
        print_info "已创建 .env 文件，请编辑以添加API密钥"
        echo "编辑命令: nano .env"
    elif [ -f ".env" ]; then
        print_info ".env 文件已存在"
    else
        print_warning ".env.example 文件不存在，跳过环境变量配置"
    fi
}

# 验证安装
verify_installation() {
    print_info "验证安装..."
    
    # 检查Python包
    echo "已安装包:"
    pip list | grep -E "(flask|langchain|mcp|openai)" || true
    
    # 测试导入
    echo -e "\n测试导入..."
    python3 -c "
try:
    import flask
    print('✅ flask 导入成功')
except ImportError as e:
    print(f'❌ flask 导入失败: {e}')

try:
    import openai
    print('✅ openai 导入成功')
except ImportError as e:
    print(f'❌ openai 导入失败: {e}')
    
try:
    from src.utils.logger import logger
    print('✅ 项目模块导入成功')
except ImportError as e:
    print(f'❌ 项目模块导入失败: {e}')
"
}

# 创建激活脚本
create_activation_script() {
    print_info "创建快速激活脚本..."
    
    cat > activate_project.sh << 'EOF'
#!/bin/bash
# 快速激活项目虚拟环境脚本

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -d "$PROJECT_DIR/venv" ]; then
    source "$PROJECT_DIR/venv/bin/activate"
    echo "✅ 虚拟环境已激活"
    echo "项目目录: $PROJECT_DIR"
    echo "虚拟环境: $VIRTUAL_ENV"
else
    echo "❌ 虚拟环境不存在，请先运行 setup_kali_venv.sh"
    exit 1
fi
EOF
    
    chmod +x activate_project.sh
    print_info "快速激活脚本已创建: ./activate_project.sh"
}

# 显示使用说明
show_instructions() {
    echo ""
    echo "========================================"
    echo "  Kali虚拟环境设置完成"
    echo "========================================"
    echo ""
    echo "✅ 虚拟环境已设置完成"
    echo ""
    echo "📋 使用说明:"
    echo ""
    echo "1. 激活虚拟环境:"
    echo "   source venv/bin/activate"
    echo "   或使用快速脚本: ./activate_project.sh"
    echo ""
    echo "2. 验证激活（命令行前应有(venv)）:"
    echo "   which python  # 应该显示项目目录下的python"
    echo ""
    echo "3. 运行项目:"
    echo "   python scripts/validate_config.py"
    echo "   python scripts/test_mcp_server.py"
    echo ""
    echo "4. 退出虚拟环境:"
    echo "   deactivate"
    echo ""
    echo "5. 下次使用时:"
    echo "   cd ~/ctf-ai-system"
    echo "   source venv/bin/activate"
    echo ""
    echo "========================================"
}

# 主函数
main() {
    echo "========================================"
    echo "  Kali Linux虚拟环境设置工具"
    echo "========================================"
    echo ""
    
    # 检查项目目录
    check_project_dir
    
    # 安装系统包
    install_system_packages
    
    # 创建虚拟环境
    create_venv
    
    # 激活虚拟环境
    activate_venv
    
    # 安装依赖
    install_dependencies
    
    # 配置环境
    setup_environment
    
    # 验证安装
    verify_installation
    
    # 创建激活脚本
    create_activation_script
    
    # 显示说明
    show_instructions
}

# 运行主函数
main "$@"