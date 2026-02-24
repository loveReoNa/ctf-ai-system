"""
配置管理模块
负责加载和管理项目配置，支持YAML配置文件和环境变量
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
import json
from dotenv import load_dotenv

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，默认为 config/development.yaml
        """
        if config_path is None:
            # 默认配置文件路径
            self.config_path = Path("config/development.yaml")
        else:
            self.config_path = Path(config_path)
        
        self._config: Dict[str, Any] = {}
        self._env_loaded = False
        
        # 加载配置
        self._load_config()
        self._load_env()
    
    def _load_config(self) -> None:
        """加载YAML配置文件"""
        try:
            if not self.config_path.exists():
                # 如果配置文件不存在，创建默认配置
                self._create_default_config()
                print(f"⚠ 配置文件不存在，已创建默认配置: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
                
            print(f"✅ 配置文件加载成功: {self.config_path}")
            
        except yaml.YAMLError as e:
            print(f"❌ YAML解析错误: {e}")
            self._config = {}
        except Exception as e:
            print(f"❌ 配置文件加载失败: {e}")
            self._config = {}
    
    def _create_default_config(self) -> None:
        """创建默认配置文件"""
        default_config = {
            "project": {
                "name": "CTF AI Attack Simulation System",
                "version": "0.1.0",
                "description": "Intelligent attack simulation for CTF challenges"
            },
            "environment": "development",
            "server": {
                "host": "127.0.0.1",
                "port": 8000,
                "debug": True,
                "workers": 1
            },
            "database": {
                "type": "sqlite",
                "path": "data/ctf_ai.db",
                "echo": True
            },
            "ai": {
                "provider": "deepseek",
                "model": "deepseek-chat",
                "api_key": "${DEEPSEEK_API_KEY}",
                "base_url": "https://api.deepseek.com",
                "temperature": 0.7,
                "max_tokens": 2000,
                "timeout": 30,
                "deepseek": {
                    "api_version": "v1",
                    "stream": False,
                    "max_retries": 3
                }
            },
            "mcp": {
                "tools_dir": "src/mcp_server/tools",
                "timeout": 30,
                "max_retries": 3
            },
            "tools": {
                "sqlmap": {
                    "path": "/usr/bin/sqlmap",
                    "windows_path": "C:/Program Files/sqlmap/sqlmap.py"
                },
                "nmap": {
                    "path": "/usr/bin/nmap",
                    "windows_path": "C:/Program Files/Nmap/nmap.exe"
                },
                "burpsuite": {
                    "path": "/usr/bin/burpsuite"
                }
            },
            "logging": {
                "level": "DEBUG",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "logs/ctf_ai.log",
                "max_size": 10485760,
                "backup_count": 5
            },
            "security": {
                "secret_key": "${SECRET_KEY}",
                "allowed_hosts": ["127.0.0.1", "localhost"],
                "cors_origins": ["http://localhost:3000"]
            }
        }
        
        # 确保配置目录存在
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入默认配置
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
        
        self._config = default_config
    
    def _load_env(self) -> None:
        """加载环境变量"""
        try:
            # 从.env文件加载
            env_path = Path(".env")
            if env_path.exists():
                load_dotenv(env_path)
                print(f"✅ 环境变量文件加载成功: {env_path}")
            else:
                print(f"⚠ 环境变量文件不存在: {env_path}")
            
            # 替换配置中的环境变量引用
            self._replace_env_vars(self._config)
            self._env_loaded = True
            
        except Exception as e:
            print(f"❌ 环境变量加载失败: {e}")
    
    def _replace_env_vars(self, config: Dict[str, Any]) -> None:
        """
        递归替换配置中的环境变量引用
        
        Args:
            config: 配置字典
        """
        for key, value in config.items():
            if isinstance(value, dict):
                self._replace_env_vars(value)
            elif isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                env_value = os.getenv(env_var, "")
                
                # 特殊处理：如果环境变量为空，尝试其他可能的变量名
                if not env_value:
                    # DeepSeek API密钥备选
                    if env_var == "DEEPSEEK_API_KEY":
                        env_value = os.getenv("OPENAI_API_KEY", "")
                    # 通用密钥备选
                    elif "API_KEY" in env_var:
                        alternative = env_var.replace("DEEPSEEK", "OPENAI")
                        env_value = os.getenv(alternative, "")
                
                config[key] = env_value
                
                # 记录替换结果
                if env_value:
                    print(f"  🔧 替换环境变量: {env_var} -> {'*' * 8}{env_value[-4:] if len(env_value) > 4 else '****'}")
                else:
                    print(f"  ⚠ 环境变量未设置: {env_var}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，支持点分隔符（如 "ai.model"）
            default: 默认值
        
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            return value
        except (KeyError, TypeError, AttributeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        设置配置值
        
        Args:
            key: 配置键，支持点分隔符
            value: 配置值
        """
        keys = key.split('.')
        config = self._config
        
        # 遍历到最后一个键的父级
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            elif not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]
        
        # 设置值
        config[keys[-1]] = value
    
    def save(self, path: Optional[str] = None) -> None:
        """
        保存配置到文件
        
        Args:
            path: 保存路径，默认为原始配置文件路径
        """
        save_path = Path(path) if path else self.config_path
        
        try:
            # 确保目录存在
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
            
            print(f"✅ 配置保存成功: {save_path}")
            
        except Exception as e:
            print(f"❌ 配置保存失败: {e}")
            raise
    
    def reload(self) -> None:
        """重新加载配置"""
        print("🔄 重新加载配置...")
        self._load_config()
        self._load_env()
    
    def validate(self) -> bool:
        """
        验证配置完整性
        
        Returns:
            配置是否有效
        """
        required_keys = [
            "project.name",
            "project.version",
            "environment",
            "server.host",
            "server.port",
            "ai.provider",
            "ai.model"
        ]
        
        missing_keys = []
        for key in required_keys:
            if self.get(key) is None:
                missing_keys.append(key)
        
        if missing_keys:
            print(f"❌ 配置验证失败，缺少必要配置项: {missing_keys}")
            return False
        
        # 验证API密钥
        api_key = self.get("ai.api_key")
        if not api_key:
            print("⚠ AI API密钥未设置，某些功能可能无法使用")
        
        print("✅ 配置验证通过")
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """
        获取配置字典
        
        Returns:
            配置字典的深拷贝
        """
        import copy
        return copy.deepcopy(self._config)
    
    def to_json(self, indent: int = 2) -> str:
        """
        获取配置的JSON表示
        
        Args:
            indent: JSON缩进
        
        Returns:
            JSON字符串
        """
        return json.dumps(self._config, indent=indent, ensure_ascii=False)
    
    def print_summary(self) -> None:
        """打印配置摘要"""
        print("=" * 50)
        print("配置摘要")
        print("=" * 50)
        
        summary = {
            "项目": f"{self.get('project.name')} v{self.get('project.version')}",
            "环境": self.get("environment"),
            "服务器": f"{self.get('server.host')}:{self.get('server.port')}",
            "AI提供商": self.get("ai.provider"),
            "AI模型": self.get("ai.model"),
            "日志级别": self.get("logging.level"),
            "数据库": f"{self.get('database.type')} ({self.get('database.path')})"
        }
        
        for key, value in summary.items():
            print(f"{key:10}: {value}")
        
        print("=" * 50)

# 全局配置实例
config = ConfigManager()
