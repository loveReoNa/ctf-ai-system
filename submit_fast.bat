@echo off
REM CTF Agent 快速提交批处理脚本
REM 用法: submit_fast.bat <靶机URL>

setlocal enabledelayedexpansion

if "%1"=="" (
    echo 用法: submit_fast.bat ^<靶机URL^>
    echo 示例: submit_fast.bat http://example.com/vuln.php
    exit /b 1
)

set TARGET_URL=%1
set API_URL=http://localhost:8000

echo 正在提交靶机URL: %TARGET_URL%

REM 使用curl提交挑战
curl -X POST "%API_URL%/challenge" ^
  -H "Content-Type: application/json" ^
  -d "{\"title\":\"快速挑战\",\"description\":\"靶机URL: %TARGET_URL%\",\"target_url\":\"%TARGET_URL%\",\"category\":\"web\",\"difficulty\":\"medium\"}"

echo.
echo 提示: 任务提交后，您可以使用以下命令检查状态:
echo curl %API_URL%/tasks/^<task_id^>
echo 或访问 %API_URL%/docs 查看API文档