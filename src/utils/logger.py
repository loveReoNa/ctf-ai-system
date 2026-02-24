"""
日志管理模块
提供统一的日志记录功能，支持控制台和文件输出
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional, Dict, Any, Union
import json
from datetime import datetime

from src.utils.config_manager import config

class JSONFormatter(logging.Formatter):
    """JSON格式日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为JSON"""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # 添加额外字段
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
        
        return json.dumps(log_data, ensure_ascii=False)

class ColoredFormatter(logging.Formatter):
    """彩色控制台日志格式化器"""
    
    # 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[41m',   # 红色背景
        'RESET': '\033[0m'        # 重置
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录，添加颜色"""
        levelname = record.levelname
        color = self.COLORS.get(levelname, self.COLORS['RESET'])
        
        # 创建带颜色的消息
        message = super().format(record)
        colored_message = f"{color}{message}{self.COLORS['RESET']}"
        
        return colored_message

def setup_logger(
    name: str = "ctf_ai",
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    json_format: bool = False,
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        log_level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        log_file: 日志文件路径，如果为None则不记录到文件
        json_format: 是否使用JSON格式
        max_bytes: 日志文件最大字节数
        backup_count: 备份文件数量
    
    Returns:
        配置好的日志记录器
    """
    # 从配置获取参数
    if log_level is None:
        log_level = config.get("logging.level", "INFO")
    if log_file is None:
        log_file = config.get("logging.file", "logs/ctf_ai.log")
    
    # 创建日志记录器
    logger = logging.getLogger(name)
    
    # 设置日志级别
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)
    
    # 清除现有处理器，避免重复
    logger.handlers.clear()
    
    # 创建格式化器
    if json_format:
        formatter = JSONFormatter()
    else:
        log_format = config.get("logging.format", 
                              "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        formatter = logging.Formatter(log_format)
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # 控制台使用彩色格式化器（非JSON格式时）
    if not json_format:
        console_formatter = ColoredFormatter(log_format)
        console_handler.setFormatter(console_formatter)
    else:
        console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    # 文件处理器（如果需要）
    if log_file:
        try:
            # 创建日志目录
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 创建轮转文件处理器
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            
            logger.debug(f"文件日志处理器已添加: {log_file}")
            
        except Exception as e:
            logger.error(f"创建文件日志处理器失败: {e}")
    
    # 设置传播（不传播到根记录器）
    logger.propagate = False
    
    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称，如果为None则返回根记录器
    
    Returns:
        日志记录器
    """
    if name is None:
        return logging.getLogger()
    return logging.getLogger(name)

class LoggerMixin:
    """日志混入类，为其他类添加日志功能"""
    
    @property
    def logger(self) -> logging.Logger:
        """获取类特定的日志记录器"""
        if not hasattr(self, '_logger'):
            class_name = self.__class__.__name__
            self._logger = setup_logger(f"ctf_ai.{class_name}")
        return self._logger
    
    def log_debug(self, message: str, **kwargs) -> None:
        """记录调试日志"""
        self.logger.debug(message, extra=kwargs)
    
    def log_info(self, message: str, **kwargs) -> None:
        """记录信息日志"""
        self.logger.info(message, extra=kwargs)
    
    def log_warning(self, message: str, **kwargs) -> None:
        """记录警告日志"""
        self.logger.warning(message, extra=kwargs)
    
    def log_error(self, message: str, **kwargs) -> None:
        """记录错误日志"""
        self.logger.error(message, extra=kwargs)
    
    def log_critical(self, message: str, **kwargs) -> None:
        """记录严重错误日志"""
        self.logger.critical(message, extra=kwargs)
    
    def log_exception(self, message: str, exc_info: bool = True, **kwargs) -> None:
        """记录异常日志"""
        self.logger.exception(message, exc_info=exc_info, extra=kwargs)

def log_function_call(logger: logging.Logger):
    """
    函数调用日志装饰器
    
    Args:
        logger: 日志记录器
    
    Returns:
        装饰器函数
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 记录函数调用
            logger.debug(f"调用函数: {func.__name__}")
            
            try:
                # 执行函数
                result = func(*args, **kwargs)
                
                # 记录成功
                logger.debug(f"函数完成: {func.__name__}")
                return result
                
            except Exception as e:
                # 记录异常
                logger.error(f"函数失败: {func.__name__}, 错误: {e}", exc_info=True)
                raise
                raise
        
        return wrapper
    return decorator

def log_async_function_call(logger: logging.Logger):
    """
    异步函数调用日志装饰器
    
    Args:
        logger: 日志记录器
    
    Returns:
        装饰器函数
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 记录函数调用
            logger.debug(f"调用异步函数: {func.__name__}")
            
            try:
                # 执行函数
                result = await func(*args, **kwargs)
                
                # 记录成功
                logger.debug(f"异步函数完成: {func.__name__}")
                return result
                
            except Exception as e:
                # 记录异常
                logger.error(f"异步函数失败: {func.__name__}, 错误: {e}", exc_info=True)
                raise
        
        return wrapper
    return decorator

def setup_global_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    json_format: bool = False
) -> None:
    """
    设置全局日志配置
    
    Args:
        level: 全局日志级别
        log_file: 全局日志文件路径
        json_format: 是否使用JSON格式
    """
    # 设置根记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # 清除现有处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 创建格式化器
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 文件处理器（如果需要）
    if log_file:
        try:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=10485760,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            root_logger.error(f"设置全局文件日志失败: {e}")

def test_logging() -> None:
    """测试日志功能"""
    print("=" * 50)
    print("测试日志功能")
    print("=" * 50)
    
    # 创建测试日志记录器
    test_logger = setup_logger("test_logger", "DEBUG")
    
    # 测试不同级别的日志
    test_logger.debug("这是一条调试消息")
    test_logger.info("这是一条信息消息")
    test_logger.warning("这是一条警告消息")
    test_logger.error("这是一条错误消息")
    
    # 测试额外字段
    test_logger.info("带额外字段的消息", extra={
        "user": "test_user",
        "action": "test_action",
        "duration": 123.45
    })
    
    # 测试异常日志
    try:
        raise ValueError("测试异常")
    except ValueError as e:
        test_logger.exception("捕获到异常")
    
    print("=" * 50)
    print("日志测试完成")
    print("=" * 50)

# 全局日志记录器实例
logger = setup_logger()

if __name__ == "__main__":
    # 直接运行此文件时测试日志功能
    test_logging()
