import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from config.settings import BASE_DIR


class LogManager:
    """日志管理器 - 负责记录所有操作到txt格式的日志文件"""
    
    def __init__(self, logs_dir: Path = None):
        self.logs_dir = logs_dir or BASE_DIR / "logs"
        
        # 确保日志目录存在
        self.logs_dir.mkdir(exist_ok=True)
    
    def _get_today_dir(self) -> Path:
        """获取今天的日志目录"""
        today = datetime.now().strftime("%Y-%m-%d")
        today_dir = self.logs_dir / today
        today_dir.mkdir(exist_ok=True)
        return today_dir
    
    def _get_log_file_path(self) -> Path:
        """获取今天的日志文件路径"""
        today_dir = self._get_today_dir()
        return today_dir / "full_operations.log"
    
    def _write_log(self, message: str):
        """写入日志条目"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        log_file = self._get_log_file_path()
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"⚠️  日志写入失败: {e}")
    
    def log_system_start(self):
        """记录系统启动"""
        self._write_log("📱 系统启动")
    
    def log_system_shutdown(self):
        """记录系统关闭"""
        self._write_log("📱 系统关闭")
    
    def log_session_created(self, session_id: str):
        """记录会话创建"""
        self._write_log(f"🆕 创建新会话: {session_id}")
    
    def log_session_loaded(self, session_id: str, success: bool = True):
        """记录会话加载"""
        if success:
            self._write_log(f"🔄 加载会话: {session_id}")
        else:
            self._write_log(f"❌ 会话加载失败: {session_id}")
    
    def log_session_timeout(self, old_session: str, new_session: str):
        """记录会话超时"""
        self._write_log(f"⏰ 会话超时 ({old_session}) -> 创建新会话: {new_session}")
    
    def log_user_message(self, content: str):
        """记录用户消息"""
        # 截断过长的消息
        preview = content[:100] + "..." if len(content) > 100 else content
        self._write_log(f"👤 用户: {preview}")
    
    def log_assistant_message(self, content: str):
        """记录助手消息"""
        # 截断过长的消息，且过滤掉函数调用部分
        clean_content = self._clean_function_calls(content)
        preview = clean_content[:100] + "..." if len(clean_content) > 100 else clean_content
        self._write_log(f"🤖 助手: {preview}")
    
    def log_function_call(self, function_name: str, parameters: Dict[str, Any], success: bool, result: str = ""):
        """记录函数调用"""
        params_str = ", ".join([f"{k}={repr(v)}" for k, v in parameters.items()])
        
        if success:
            result_preview = result[:50] + "..." if len(result) > 50 else result
            self._write_log(f"🔧 函数调用: {function_name}({params_str}) -> ✅ {result_preview}")
        else:
            self._write_log(f"🔧 函数调用: {function_name}({params_str}) -> ❌ {result}")
    
    def log_function_detection(self, function_calls_xml: str):
        """记录检测到的函数调用XML（完整记录）"""
        # 将XML格式化为单行记录
        xml_line = function_calls_xml.replace('\n', ' ').replace('  ', ' ').strip()
        self._write_log(f"🔍 检测到函数调用: {xml_line}")
    
    def log_error(self, error_type: str, error_message: str):
        """记录错误"""
        self._write_log(f"❌ 错误 [{error_type}]: {error_message}")
    
    def log_api_call(self, model: str, tokens_used: int = None):
        """记录API调用"""
        if tokens_used:
            self._write_log(f"🌐 API调用: {model} (tokens: {tokens_used})")
        else:
            self._write_log(f"🌐 API调用: {model}")
    
    def log_command(self, command: str):
        """记录用户命令"""
        self._write_log(f"⚙️  命令: {command}")
    
    def log_context_cleared(self):
        """记录上下文清空"""
        self._write_log("🗑️  上下文已清空")
    
    def log_custom(self, icon: str, message: str):
        """记录自定义消息"""
        self._write_log(f"{icon} {message}")
    
    def _clean_function_calls(self, content: str) -> str:
        """清理内容中的函数调用部分"""
        import re
        # 移除 function_calls 标签及其内容
        cleaned = re.sub(r'<function_calls>.*?</function_calls>', '', content, flags=re.DOTALL)
        # 移除 function_response 标签及其内容  
        cleaned = re.sub(r'<function_response>.*?</function_response>', '', cleaned, flags=re.DOTALL)
        return cleaned.strip()
    
    def get_today_log(self) -> Optional[str]:
        """获取今天的日志内容"""
        log_file = self._get_log_file_path()
        if not log_file.exists():
            return None
            
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return None
    
    def get_recent_logs(self, days: int = 3) -> Dict[str, str]:
        """获取最近几天的日志"""
        logs = {}
        
        # 按日期降序获取日志目录
        date_dirs = sorted([d for d in self.logs_dir.iterdir() if d.is_dir() and d.name.match(r'\d{4}-\d{2}-\d{2}')], reverse=True)
        
        count = 0
        for date_dir in date_dirs:
            if count >= days:
                break
                
            log_file = date_dir / "full_operations.log"
            if log_file.exists():
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        logs[date_dir.name] = f.read()
                except Exception:
                    logs[date_dir.name] = "读取失败"
                    
            count += 1
        
        return logs
    
    def search_logs(self, keyword: str, days: int = 7) -> List[str]:
        """在日志中搜索关键词"""
        results = []
        recent_logs = self.get_recent_logs(days)
        
        for date, log_content in recent_logs.items():
            lines = log_content.split('\n')
            for line_num, line in enumerate(lines, 1):
                if keyword.lower() in line.lower():
                    results.append(f"[{date}:{line_num}] {line}")
        
        return results


# 创建全局日志管理器实例
log_manager = LogManager()