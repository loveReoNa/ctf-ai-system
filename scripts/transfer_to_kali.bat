@echo off
REM CTF AI项目传输脚本 (Windows批处理版本)
REM 将项目从Windows传输到Kali Linux

setlocal enabledelayedexpansion

REM 配置变量
set KALI_USER=kali
set KALI_IP=192.168.1.100
set PROJECT_DIR=.ctfagent
set LOCAL_PATH=.
set REMOTE_PATH=/home/%KALI_USER%/

echo ========================================
echo   CTF AI 项目传输工具 (Windows → Kali)
echo ========================================
echo.

REM 检查必要命令
where scp >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] scp命令未找到，请安装OpenSSH或Git Bash
    pause
    exit /b 1
)

where ssh >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] ssh命令未找到，请安装OpenSSH或Git Bash
    pause
    exit /b 1
)

echo [INFO] 必要命令检查通过
echo.

REM 获取Kali IP
if "%KALI_IP%"=="192.168.1.100" (
    echo [WARNING] 使用默认IP地址，请确认是否正确
    echo 当前Kali IP: %KALI_IP%
    set /p USER_IP="请输入正确的Kali IP地址（直接回车使用当前）: "
    if not "!USER_IP!"=="" (
        set KALI_IP=!USER_IP!
        echo [INFO] 已更新Kali IP为: !KALI_IP!
    )
)

echo.
echo [INFO] 测试连接到Kali (%KALI_USER%@%KALI_IP%)...
ssh -o ConnectTimeout=5 %KALI_USER%@%KALI_IP% "echo 连接成功" >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] 无法连接到Kali，请检查：
    echo   1. Kali IP地址是否正确（当前: %KALI_IP%）
    echo   2. Kali SSH服务是否运行（sudo systemctl status ssh）
    echo   3. 网络是否连通（ping %KALI_IP%）
    echo   4. 防火墙设置
    pause
    exit /b 1
)

echo [INFO] Kali连接测试成功
echo.

REM 显示传输信息
echo [WARNING] 即将传输项目到Kali:
echo   源目录: %LOCAL_PATH%
echo   目标: %KALI_USER%@%KALI_IP%:%REMOTE_PATH%%PROJECT_DIR%
echo.
set /p CONFIRM="是否继续？(y/n): "
if /i not "!CONFIRM!"=="y" (
    echo [INFO] 用户取消操作
    pause
    exit /b 0
)

echo.
echo [INFO] 开始传输项目到Kali...

REM 创建远程目录
ssh %KALI_USER%@%KALI_IP% "mkdir -p %REMOTE_PATH%%PROJECT_DIR%"

REM 传输文件
echo [INFO] 传输文件中（这可能需要几分钟）...
scp -r ^
    --exclude=.git/ ^
    --exclude=__pycache__/ ^
    --exclude=*.pyc ^
    --exclude=*.log ^
    --exclude=venv/ ^
    --exclude=.env ^
    "%LOCAL_PATH%\*" ^
    "%KALI_USER%@%KALI_IP%:%REMOTE_PATH%%PROJECT_DIR%/"

if %errorlevel% neq 0 (
    echo [ERROR] 文件传输失败
    pause
    exit /b 1
)

echo [INFO] 文件传输完成
echo.

REM 在Kali中执行初始设置
echo [INFO] 在Kali中执行初始设置...
echo.

REM 创建临时脚本文件
set TEMP_SCRIPT=%TEMP%\kali_setup.sh
(
echo #!/bin/bash
echo echo "=== Kali Linux 初始设置 ==="
echo.
echo # 进入项目目录
echo cd .ctfagent || { echo "项目目录不存在"; exit 1; }
echo.
echo # 1. 验证Kali环境
echo echo "1. 验证Kali环境..."
echo python3 scripts/verify_kali_environment.py
echo.
echo # 2. 安装Python依赖
echo echo -e "\n2. 安装Python依赖..."
echo pip3 install -r requirements.txt
echo.
echo # 3. 创建环境变量文件
echo echo -e "\n3. 配置环境变量..."
echo if [ ! -f .env ]; then
echo     cp .env.example .env
echo     echo "已创建 .env 文件，请编辑以添加API密钥"
echo fi
echo.
echo # 4. 设置执行权限
echo echo -e "\n4. 设置执行权限..."
echo chmod +x scripts/*.py
echo chmod +x src/mcp_server/server.py
echo.
echo echo -e "\n=== 初始设置完成 ==="
echo echo "下一步:"
echo echo "1. 编辑 .env 文件添加DeepSeek API密钥"
echo echo "2. 运行测试: python3 scripts/test_mcp_server.py"
echo echo "3. 启动服务器: python3 scripts/start_mcp_server.py"
) > "%TEMP_SCRIPT%"

REM 传输并执行设置脚本
scp "%TEMP_SCRIPT%" "%KALI_USER%@%KALI_IP%:/tmp/kali_setup.sh"
ssh "%KALI_USER%@%KALI_IP%" "chmod +x /tmp/kali_setup.sh && /tmp/kali_setup.sh"

REM 清理临时文件
del "%TEMP_SCRIPT%" >nul 2>nul

echo.
echo ========================================
echo [INFO] 连接信息汇总:
echo   Kali用户名: %KALI_USER%
echo   Kali IP地址: %KALI_IP%
echo   项目目录: %REMOTE_PATH%%PROJECT_DIR%
echo.
echo 手动连接命令:
echo   ssh %KALI_USER%@%KALI_IP%
echo   cd %REMOTE_PATH%%PROJECT_DIR%
echo ========================================
echo.
echo [INFO] 传输和设置完成！
echo.
pause