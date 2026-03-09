#!/usr/bin/env python3
"""
CTF Agent API服务器
提供RESTful API接口，允许用户通过API请求调用CTF Agent进行自动解题
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import uvicorn

from src.agents.react_agent import ReActAgent, CTFChallenge
from src.utils.logger import setup_logger
from src.utils.config_manager import config

# 设置日志
logger = setup_logger("api_server", log_level="INFO")

# 创建FastAPI应用
app = FastAPI(
    title="CTF Agent API",
    description="智能CTF攻击模拟系统API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局Agent实例
agent: Optional[ReActAgent] = None
agent_lock = asyncio.Lock()

# 任务存储
tasks: Dict[str, Dict[str, Any]] = {}


# 数据模型
class ChallengeRequest(BaseModel):
    """挑战请求模型"""
    title: str = Field(..., description="挑战标题")
    description: str = Field(..., description="挑战描述")
    target_url: str = Field(..., description="目标URL")
    category: str = Field("web", description="挑战类别 (web, crypto, pwn等)")
    difficulty: str = Field("medium", description="难度级别 (easy, medium, hard)")
    hints: List[str] = Field(default_factory=list, description="提示信息")
    expected_flag: Optional[str] = Field(None, description="预期的flag（可选）")
    
    @validator('category')
    def validate_category(cls, v):
        valid_categories = ['web', 'crypto', 'pwn', 'reverse', 'misc', 'forensics']
        if v.lower() not in valid_categories:
            raise ValueError(f'类别必须是以下之一: {", ".join(valid_categories)}')
        return v.lower()
    
    @validator('difficulty')
    def validate_difficulty(cls, v):
        valid_difficulties = ['easy', 'medium', 'hard']
        if v.lower() not in valid_difficulties:
            raise ValueError(f'难度必须是以下之一: {", ".join(valid_difficulties)}')
        return v.lower()


class TaskResponse(BaseModel):
    """任务响应模型"""
    task_id: str
    status: str
    message: str
    created_at: str
    challenge: Dict[str, Any]


class TaskStatusResponse(BaseModel):
    """任务状态响应模型"""
    task_id: str
    status: str
    progress: float
    current_step: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str
    updated_at: str


class AgentStatusResponse(BaseModel):
    """Agent状态响应模型"""
    status: str
    state: str
    initialized: bool
    tools_available: List[str]
    active_tasks: int


# 工具调用模型
class ToolRequest(BaseModel):
    """工具调用请求模型"""
    tool_name: str = Field(..., description="工具名称")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="工具参数")


class ToolResponse(BaseModel):
    """工具调用响应模型"""
    success: bool
    result: Dict[str, Any]
    execution_time: float
    error: Optional[str] = None


# 初始化Agent
async def initialize_agent():
    """初始化全局Agent实例"""
    global agent
    
    async with agent_lock:
        if agent is None:
            try:
                logger.info("正在初始化CTF Agent...")
                
                # 创建Agent配置
                agent_config = {
                    "ai": config.get("ai", {}),
                    "mcp": config.get("mcp", {}),
                    "api": config.get("api", {})
                }
                
                # 创建Agent实例
                agent = ReActAgent(agent_config)
                
                # 初始化Agent
                success = await agent.initialize()
                if not success:
                    logger.error("Agent初始化失败")
                    agent = None
                    return False
                
                logger.info("CTF Agent初始化成功")
                return True
                
            except Exception as e:
                logger.error(f"Agent初始化异常: {e}")
                agent = None
                return False
        else:
            return True


# 生成任务ID
def generate_task_id() -> str:
    """生成唯一的任务ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    import random
    random_str = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=6))
    return f"task_{timestamp}_{random_str}"


# 后台任务执行函数
async def execute_attack_task(task_id: str, challenge_data: Dict[str, Any]):
    """在后台执行攻击任务"""
    global agent, tasks
    
    try:
        # 确保Agent已初始化
        if not await initialize_agent():
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["error"] = "Agent初始化失败"
            tasks[task_id]["updated_at"] = datetime.now().isoformat()
            return
        
        # 创建挑战对象
        challenge = CTFChallenge(
            id=task_id,
            title=challenge_data["title"],
            description=challenge_data["description"],
            target_url=challenge_data["target_url"],
            category=challenge_data["category"],
            difficulty=challenge_data["difficulty"],
            hints=challenge_data.get("hints", []),
            expected_flag=challenge_data.get("expected_flag")
        )
        
        # 更新任务状态
        tasks[task_id]["status"] = "analyzing"
        tasks[task_id]["current_step"] = "分析挑战"
        tasks[task_id]["updated_at"] = datetime.now().isoformat()
        
        # 运行完整攻击流程
        logger.info(f"开始执行任务 {task_id}: {challenge.title}")
        
        result = await agent.run_full_attack(challenge)
        
        # 更新任务结果
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["result"] = result
        tasks[task_id]["updated_at"] = datetime.now().isoformat()
        
        logger.info(f"任务 {task_id} 完成")
        
    except Exception as e:
        logger.error(f"任务 {task_id} 执行失败: {e}")
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)
        tasks[task_id]["updated_at"] = datetime.now().isoformat()


# API端点
@app.get("/")
async def root():
    """根端点，返回API信息"""
    return {
        "name": "CTF Agent API",
        "version": "1.0.0",
        "description": "智能CTF攻击模拟系统",
        "endpoints": {
            "/status": "获取系统状态",
            "/challenge": "提交CTF挑战",
            "/tasks/{task_id}": "获取任务状态",
            "/tools": "获取可用工具列表",
            "/tools/execute": "直接执行工具"
        }
    }


@app.get("/status", response_model=AgentStatusResponse)
async def get_status():
    """获取Agent状态"""
    global agent
    
    try:
        initialized = agent is not None
        state = agent.state.value if agent else "not_initialized"
        tools = list(agent.tool_mapping.keys()) if agent else []
        
        active_tasks = sum(1 for task in tasks.values() if task["status"] in ["pending", "analyzing", "planning", "executing"])
        
        return AgentStatusResponse(
            status="running",
            state=state,
            initialized=initialized,
            tools_available=tools,
            active_tasks=active_tasks
        )
    except Exception as e:
        logger.error(f"获取状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/challenge", response_model=TaskResponse)
async def submit_challenge(
    challenge: ChallengeRequest,
    background_tasks: BackgroundTasks
):
    """提交CTF挑战，创建攻击任务"""
    global tasks
    
    try:
        # 生成任务ID
        task_id = generate_task_id()
        
        # 创建任务记录
        tasks[task_id] = {
            "status": "pending",
            "challenge": challenge.dict(),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "current_step": None,
            "result": None,
            "error": None
        }
        
        # 在后台执行任务
        background_tasks.add_task(execute_attack_task, task_id, challenge.dict())
        
        logger.info(f"创建新任务 {task_id}: {challenge.title}")
        
        return TaskResponse(
            task_id=task_id,
            status="pending",
            message="挑战已接收，正在处理",
            created_at=tasks[task_id]["created_at"],
            challenge=challenge.dict()
        )
        
    except Exception as e:
        logger.error(f"提交挑战失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """获取任务状态"""
    global tasks
    
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = tasks[task_id]
    
    # 计算进度
    progress = 0.0
    if task["status"] == "pending":
        progress = 0.1
    elif task["status"] == "analyzing":
        progress = 0.3
    elif task["status"] == "planning":
        progress = 0.5
    elif task["status"] == "executing":
        progress = 0.7
    elif task["status"] == "completed":
        progress = 1.0
    elif task["status"] == "failed":
        progress = 0.0
    
    return TaskStatusResponse(
        task_id=task_id,
        status=task["status"],
        progress=progress,
        current_step=task.get("current_step"),
        result=task.get("result"),
        error=task.get("error"),
        created_at=task["created_at"],
        updated_at=task["updated_at"]
    )


@app.get("/tasks")
async def list_tasks(
    status: Optional[str] = Query(None, description="过滤任务状态"),
    limit: int = Query(50, description="返回的任务数量限制"),
    offset: int = Query(0, description="偏移量")
):
    """列出所有任务"""
    global tasks
    
    try:
        filtered_tasks = tasks.values()
        
        if status:
            filtered_tasks = [t for t in filtered_tasks if t["status"] == status]
        
        # 按创建时间排序（最新的在前）
        sorted_tasks = sorted(filtered_tasks, key=lambda x: x["created_at"], reverse=True)
        
        # 分页
        paginated_tasks = sorted_tasks[offset:offset + limit]
        
        return {
            "total": len(filtered_tasks),
            "limit": limit,
            "offset": offset,
            "tasks": paginated_tasks
        }
        
    except Exception as e:
        logger.error(f"列出任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tools")
async def list_tools():
    """获取可用工具列表"""
    global agent
    
    try:
        if not await initialize_agent():
            raise HTTPException(status_code=500, detail="Agent未初始化")
        
        # 从MCP服务器获取工具列表
        tools = await agent.mcp_server.handle_list_tools()
        
        return {
            "tools": tools,
            "count": len(tools)
        }
        
    except Exception as e:
        logger.error(f"获取工具列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/execute", response_model=ToolResponse)
async def execute_tool(tool_request: ToolRequest):
    """直接执行工具"""
    global agent
    
    try:
        if not await initialize_agent():
            raise HTTPException(status_code=500, detail="Agent未初始化")
        
        logger.info(f"执行工具: {tool_request.tool_name}, 参数: {tool_request.parameters}")
        
        start_time = asyncio.get_event_loop().time()
        
        # 调用工具
        result = await agent.mcp_server.handle_call_tool(
            tool_request.tool_name,
            tool_request.parameters
        )
        
        execution_time = asyncio.get_event_loop().time() - start_time
        
        success = result.get("success", False)
        
        return ToolResponse(
            success=success,
            result=result,
            execution_time=execution_time,
            error=None if success else result.get("error", "工具执行失败")
        )
        
    except Exception as e:
        logger.error(f"执行工具失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/initialize")
async def initialize_agent_endpoint():
    """手动初始化Agent"""
    try:
        success = await initialize_agent()
        
        if success:
            return {"success": True, "message": "Agent初始化成功"}
        else:
            return {"success": False, "message": "Agent初始化失败"}
            
    except Exception as e:
        logger.error(f"手动初始化Agent失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/reset")
async def reset_agent():
    """重置Agent状态"""
    global agent
    
    try:
        async with agent_lock:
            agent = None
            logger.info("Agent已重置")
            
        return {"success": True, "message": "Agent已重置"}
        
    except Exception as e:
        logger.error(f"重置Agent失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 启动服务器
def start_server(host: str = "0.0.0.0", port: int = 8000):
    """启动API服务器"""
    logger.info(f"启动CTF Agent API服务器: http://{host}:{port}")
    logger.info(f"API文档: http://{host}:{port}/docs")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    # 从配置读取服务器设置
    server_config = config.get("api", {}).get("server", {})
    host = server_config.get("host", "0.0.0.0")
    port = server_config.get("port", 8000)
    
    start_server(host, port)