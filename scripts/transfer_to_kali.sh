#!/bin/bash
# 项目传输脚本：从Windows传输到Kali Linux
# 使用方法：在Windows的Git Bash或WSL中运行

set -e

# 配置变量
KALI_USER="kali"                    # Kali用户名
KALI_IP="192.168.1.100"             # Kali IP地址，请修改为实际IP
PROJECT_DIR=".ctfagent"             # 项目目录名
LOCAL_PATH="./"                     # 本地项目路径
REMOTE_PATH="/home/$KALI_USER/"     # 远程目标路径

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

# 检查必要命令
check_commands() {
    local commands=("scp" "ssh")
    for cmd in "${commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            print_error "命令 $cmd 未找到，请安装后重试"
            exit 1
        fi
    done
    print_info "必要命令检查通过"
}

# 测试Kali连接
test_connection() {
    print_info "测试连接到Kali ($KALI_USER@$KALI_IP)..."
    if ssh -o ConnectTimeout=5 "$KALI_USER@$KALI_IP" "echo '连接成功'" &> /dev/null; then
        print_info "Kali连接测试成功"
        return 0
    else
        print_error "无法连接到Kali，请检查："
        echo "1. Kali IP地址是否正确（当前: $KALI_IP）"
        echo "2. Kali SSH服务是否运行（sudo systemctl status ssh）"
        echo "3. 网络是否连通（ping $KALI_IP）"
        echo "4. 防火墙设置"
        return 1
    fi
}

# 获取Kali IP（如果未设置）
get_kali_ip() {
    if [ "$KALI_IP" = "192.168.1.100" ]; then
        print_warning "使用默认IP地址，请确认是否正确"
        echo "当前Kali IP: $KALI_IP"
        read -p "请输入正确的Kali IP地址（直接回车使用当前）: " user_ip
        if [ -n "$user_ip" ]; then
            KALI_IP="$user_ip"
            print_info "已更新Kali IP为: $KALI_IP"
        fi
    fi
}

# 传输项目文件
transfer_project() {
    print_info "开始传输项目到Kali..."
    
    # 创建远程目录
    ssh "$KALI_USER@$KALI_IP" "mkdir -p $REMOTE_PATH$PROJECT_DIR"
    
    # 传输文件（排除不必要的文件）
    print_info "传输文件中（这可能需要几分钟）..."
    scp -r \
        --exclude='.git/' \
        --exclude='__pycache__/' \
        --exclude='*.pyc' \
        --exclude='*.log' \
        --exclude='venv/' \
        --exclude='.env' \
        "$LOCAL_PATH"* \
        "$KALI_USER@$KALI_IP:$REMOTE_PATH$PROJECT_DIR/"
    
    print_info "文件传输完成"
}

# 在Kali中执行初始设置
setup_kali() {
    print_info "在Kali中执行初始设置..."
    
    ssh "$KALI_USER@$KALI_IP" << 'EOF'
        echo "=== Kali Linux 初始设置 ==="
        
        # 进入项目目录
        cd .ctfagent || { echo "项目目录不存在"; exit 1; }
        
        # 1. 验证Kali环境
        echo "1. 验证Kali环境..."
        python3 scripts/verify_kali_environment.py
        
        # 2. 安装Python依赖
        echo -e "\n2. 安装Python依赖..."
        pip3 install -r requirements.txt
        
        # 3. 创建环境变量文件
        echo -e "\n3. 配置环境变量..."
        if [ ! -f .env ]; then
            cp .env.example .env
            echo "已创建 .env 文件，请编辑以添加API密钥"
        fi
        
        # 4. 设置执行权限
        echo -e "\n4. 设置执行权限..."
        chmod +x scripts/*.py
        chmod +x src/mcp_server/server.py
        
        echo -e "\n=== 初始设置完成 ==="
        echo "下一步:"
        echo "1. 编辑 .env 文件添加DeepSeek API密钥"
        echo "2. 运行测试: python3 scripts/test_mcp_server.py"
        echo "3. 启动服务器: python3 scripts/start_mcp_server.py"
EOF
}

# 显示连接信息
show_connection_info() {
    echo ""
    print_info "连接信息汇总:"
    echo "Kali用户名: $KALI_USER"
    echo "Kali IP地址: $KALI_IP"
    echo "项目目录: $REMOTE_PATH$PROJECT_DIR"
    echo ""
    echo "手动连接命令:"
    echo "  ssh $KALI_USER@$KALI_IP"
    echo "  cd $REMOTE_PATH$PROJECT_DIR"
    echo ""
}

# 主函数
main() {
    echo "========================================"
    echo "  CTF AI 项目传输工具 (Windows → Kali)"
    echo "========================================"
    
    # 检查命令
    check_commands
    
    # 获取Kali IP
    get_kali_ip
    
    # 测试连接
    if ! test_connection; then
        print_error "连接测试失败，请检查配置后重试"
        exit 1
    fi
    
    # 确认传输
    echo ""
    print_warning "即将传输项目到Kali:"
    echo "源目录: $LOCAL_PATH"
    echo "目标: $KALI_USER@$KALI_IP:$REMOTE_PATH$PROJECT_DIR"
    echo ""
    read -p "是否继续？(y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "用户取消操作"
        exit 0
    fi
    
    # 执行传输和设置
    transfer_project
    setup_kali
    show_connection_info
    
    print_info "传输和设置完成！"
    echo ""
}

# 运行主函数
main "$@"