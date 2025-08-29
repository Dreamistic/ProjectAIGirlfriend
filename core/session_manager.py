import json
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from config.settings import BASE_DIR


class SessionManager:
    """会话管理器 - 负责会话的创建、保存、加载和超时管理"""
    
    def __init__(self, logs_dir: Path = None):
        self.logs_dir = logs_dir or BASE_DIR / "logs"
        self.current_session_id = None
        self.current_context = []
        self.last_activity_time = time.time()
        self.session_timeout = 30 * 60  # 30分钟超时
        
        # 确保日志目录存在
        self.logs_dir.mkdir(exist_ok=True)
        
    def _get_today_dir(self) -> Path:
        """获取今天的日志目录"""
        today = datetime.now().strftime("%Y-%m-%d")
        today_dir = self.logs_dir / today
        today_dir.mkdir(exist_ok=True)
        return today_dir
        
    def _generate_session_id(self) -> str:
        """生成新的会话ID"""
        today_dir = self._get_today_dir()
        
        # 查找今天已有的会话数量
        session_files = list(today_dir.glob("session_*.json"))
        session_count = len(session_files) + 1
        
        return f"session_{session_count:03d}"
    
    def _get_session_file_path(self, session_id: str) -> Path:
        """获取会话文件路径"""
        today_dir = self._get_today_dir()
        return today_dir / f"{session_id}.json"
    
    def create_new_session(self) -> str:
        """创建新会话"""
        self.current_session_id = self._generate_session_id()
        self.current_context = []
        self.last_activity_time = time.time()
        
        # 创建会话文件
        session_data = {
            "session_id": self.current_session_id,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "messages": []
        }
        
        session_file = self._get_session_file_path(self.current_session_id)
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
        
        return self.current_session_id
    
    def save_current_session(self):
        """保存当前会话"""
        if not self.current_session_id:
            return
            
        session_data = {
            "session_id": self.current_session_id,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "messages": self.current_context
        }
        
        session_file = self._get_session_file_path(self.current_session_id)
        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  会话保存失败: {e}")
    
    def load_session(self, session_id: str) -> bool:
        """加载指定会话"""
        # 先尝试今天的目录
        session_file = self._get_session_file_path(session_id)
        
        # 如果今天没有，搜索历史目录
        if not session_file.exists():
            session_file = self._find_session_in_history(session_id)
            
        if not session_file or not session_file.exists():
            return False
            
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
                
            self.current_session_id = session_data["session_id"]
            self.current_context = session_data.get("messages", [])
            self.last_activity_time = time.time()
            
            return True
            
        except Exception as e:
            print(f"⚠️  会话加载失败: {e}")
            return False
    
    def _find_session_in_history(self, session_id: str) -> Optional[Path]:
        """在历史日志中查找会话文件"""
        for date_dir in self.logs_dir.iterdir():
            if date_dir.is_dir() and re.match(r'\d{4}-\d{2}-\d{2}', date_dir.name):
                session_file = date_dir / f"{session_id}.json"
                if session_file.exists():
                    return session_file
        return None
    
    def load_latest_session(self) -> bool:
        """加载最新会话"""
        latest_session = self.get_latest_session_id()
        if latest_session:
            return self.load_session(latest_session)
        return False
    
    def get_latest_session_id(self) -> Optional[str]:
        """获取最新会话ID"""
        # 按日期降序查找最新会话
        date_dirs = sorted([d for d in self.logs_dir.iterdir() if d.is_dir() and re.match(r'\d{4}-\d{2}-\d{2}', d.name)], reverse=True)
        
        for date_dir in date_dirs:
            session_files = sorted(date_dir.glob("session_*.json"), reverse=True)
            if session_files:
                session_file = session_files[0]
                return session_file.stem
        
        return None
    
    def get_session_list(self, days: int = 7) -> List[Dict]:
        """获取最近几天的会话列表"""
        sessions = []
        
        # 获取最近N天的日期目录
        date_dirs = sorted([d for d in self.logs_dir.iterdir() if d.is_dir() and re.match(r'\d{4}-\d{2}-\d{2}', d.name)], reverse=True)
        
        count = 0
        for date_dir in date_dirs:
            if count >= days:
                break
                
            session_files = sorted(date_dir.glob("session_*.json"))
            for session_file in session_files:
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                        
                    # 计算消息数量
                    message_count = len(session_data.get("messages", []))
                    
                    sessions.append({
                        "session_id": session_data["session_id"],
                        "date": date_dir.name,
                        "created_at": session_data.get("created_at", ""),
                        "message_count": message_count,
                        "preview": self._get_session_preview(session_data.get("messages", []))
                    })
                    
                except Exception:
                    continue
            
            count += 1
        
        return sessions
    
    def _get_session_preview(self, messages: List[Dict]) -> str:
        """获取会话预览（第一条用户消息）"""
        for msg in messages:
            if msg.get("role") == "user":
                content = msg.get("content", "")
                return content[:50] + "..." if len(content) > 50 else content
        return "无对话内容"
    
    def check_timeout(self) -> bool:
        """检查会话是否超时"""
        return time.time() - self.last_activity_time > self.session_timeout
    
    def update_activity(self):
        """更新最后活动时间"""
        self.last_activity_time = time.time()
    
    def add_message(self, role: str, content: str):
        """添加消息到当前会话"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        self.current_context.append(message)
        self.update_activity()
        
        # 自动保存（频率可以优化）
        self.save_current_session()
    
    def get_current_context(self) -> List[Dict]:
        """获取当前上下文（去掉timestamp）"""
        return [{"role": msg["role"], "content": msg["content"]} for msg in self.current_context]
    
    def clear_current_session(self):
        """清空当前会话"""
        self.current_context = []
        if self.current_session_id:
            self.save_current_session()


# 创建全局会话管理器实例
session_manager = SessionManager()