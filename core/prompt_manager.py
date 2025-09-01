import re
import time
from pathlib import Path
from typing import Optional
from config.settings import SYSTEM_PROMPT_PATH
from utils.time_utils import get_current_time_string
from utils.error_handler import error_handler


class SystemPromptManager:
    """系统提示管理器 - 负责动态更新系统提示内容"""
    
    def __init__(self, prompt_path: Optional[Path] = None):
        self.prompt_path = prompt_path or SYSTEM_PROMPT_PATH
        self._cached_prompt: Optional[str] = None
        self._cache_timestamp: Optional[float] = None
        
    def _should_refresh_cache(self) -> bool:
        """检查是否需要刷新缓存"""
        if self._cached_prompt is None:
            return True
            
        try:
            file_mtime = self.prompt_path.stat().st_mtime
            return file_mtime > self._cache_timestamp
        except (OSError, AttributeError):
            return True
    
    def read_system_prompt(self, use_cache: bool = True) -> str:
        """
        读取系统提示文件
        
        Args:
            use_cache: 是否使用缓存
            
        Returns:
            系统提示内容，如果读取失败则返回默认提示
        """
        if use_cache and not self._should_refresh_cache():
            return self._cached_prompt
            
        try:
            with open(self.prompt_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            # 更新缓存
            self._cached_prompt = content
            self._cache_timestamp = time.time()
            
            return content
            
        except Exception as e:
            # 使用错误处理器处理异常，返回备用提示
            fallback_prompt = error_handler.handle_system_prompt_error(e)
            
            # 更新缓存为备用提示
            self._cached_prompt = fallback_prompt
            self._cache_timestamp = time.time()
            
            return fallback_prompt
    
    def update_functions(self, system_prompt: str, functions_xml: str) -> str:
        """
        更新系统提示中的functions部分
        
        Args:
            system_prompt: 原始系统提示
            functions_xml: 新的函数XML内容
            
        Returns:
            更新后的系统提示
        """
        function_system_content = f"""<function_system>
      <rule>请在请求函数调用后立即停止回复，等待函数调用</rule>
{functions_xml}
    <function_rules>
      <rule>使用XML格式调用函数</rule>
      <rule>等待函数响应后继续</rule>
      <example>
        <function_calls>
          <invoke name="function_name">
            <parameter name="param_name">param_value</parameter>
          </invoke>
        </function_calls>
      </example>
    </function_rules>
</function_system>"""
        
        updated_prompt = re.sub(
            r'<function_system>.*?</function_system>',
            function_system_content,
            system_prompt,
            flags=re.DOTALL
        )
        
        return updated_prompt
    
    def update_time(self, system_prompt: str) -> str:
        """
        更新系统提示中的当前时间
        
        Args:
            system_prompt: 原始系统提示
            
        Returns:
            更新后的系统提示
        """
        current_time = get_current_time_string()
        
        updated_prompt = re.sub(
            r'<current_time>.*?</current_time>',
            f'<current_time>{current_time}</current_time>',
            system_prompt,
            flags=re.DOTALL
        )
        
        return updated_prompt
    
    def update_active_todos(self, system_prompt: str) -> str:
        """
        更新系统提示中的活跃任务信息
        
        Args:
            system_prompt: 原始系统提示
            
        Returns:
            更新后的系统提示
        """
        # 导入林晚晴的AI任务系统
        from functions.ai_task_functions import ai_task_list
        
        active_todos = ai_task_list.get_active_todos()
        
        if active_todos:
            # 构建活跃任务的XML内容  
            active_todos_content = "<my_current_tasks>\n"
            active_todos_content += "执行中的任务:\n"
            
            for todo in active_todos:
                status_text = "[进行中]" if todo['status'] == 'in_progress' else f"[{todo['status']}]"
                active_todos_content += f"• {status_text} {todo['content']}\n"
                active_todos_content += f"  进度: {todo['progress']}%\n"
                
                # 添加未完成的子任务
                if todo['subtasks']:
                    pending_subtasks = [st for st in todo['subtasks'] if not st['completed']]
                    if pending_subtasks:
                        active_todos_content += f"  待完成步骤:\n"
                        for subtask in pending_subtasks[:3]:  # 只显示前3个
                            active_todos_content += f"    - {subtask['content']}\n"
                        if len(pending_subtasks) > 3:
                            active_todos_content += f"    - ... 还有{len(pending_subtasks)-3}个\n"
            
            active_todos_content += "\n使用todo系统管理任务进度。\n"
            active_todos_content += "</my_current_tasks>"
        else:
            # 没有活跃任务
            active_todos_content = "<my_current_tasks>\n当前无执行中的任务。\n</my_current_tasks>"
        
        # 替换或插入活跃任务内容
        if '<current_active_tasks>' in system_prompt or '<my_current_tasks>' in system_prompt:
            # 如果已存在，则替换（兼容旧标签和新标签）
            updated_prompt = re.sub(
                r'<(current_active_tasks|my_current_tasks)>.*?</(current_active_tasks|my_current_tasks)>',
                active_todos_content,
                system_prompt,
                flags=re.DOTALL
            )
        else:
            # 如果不存在，在function_system之前插入
            if '<function_system>' in system_prompt:
                updated_prompt = system_prompt.replace(
                    '<function_system>',
                    f'{active_todos_content}\n\n<function_system>'
                )
            else:
                # 如果都没有，就添加在末尾
                updated_prompt = system_prompt + "\n\n" + active_todos_content
        
        return updated_prompt
    
    def update_system_prompt(self, functions_xml: str) -> str:
        """
        完整更新系统提示 - 包含函数、时间和活跃任务
        
        Args:
            functions_xml: 函数XML内容
            
        Returns:
            完整更新后的系统提示
        """
        # 读取原始系统提示
        system_prompt = self.read_system_prompt()
        
        # 更新活跃任务信息
        updated_prompt = self.update_active_todos(system_prompt)
        
        # 更新函数列表
        updated_prompt = self.update_functions(updated_prompt, functions_xml)
        
        # 更新时间
        updated_prompt = self.update_time(updated_prompt)
        
        return updated_prompt
    
    def clear_cache(self):
        """清除缓存，强制重新读取文件"""
        self._cached_prompt = None
        self._cache_timestamp = None


# 创建全局实例
prompt_manager = SystemPromptManager()