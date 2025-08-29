import re
from typing import Callable, Optional, Tuple, List, Dict
from anthropic import Anthropic
from config.settings import AI_MODEL, ANTHROPIC_API_KEY, CHAT_CONFIG, MAX_CONVERSATION_DEPTH
from core.function_registry import function_registry, FunctionResult
from core.prompt_manager import prompt_manager
from core.session_manager import session_manager
from core.log_manager import log_manager
from utils.error_handler import error_handler


class StreamFunctionDetector:
    """流式函数调用检测器 - 隐藏函数调用详情的优化版本"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """重置检测器状态"""
        self.buffer = ""
        self.in_function_block = False
        self.start_tag_found = False
        self.clean_content = ""  # 存储清理后的内容
        self.function_hint_shown = False  # 是否已显示函数提示
        
    def feed_chunk(self, chunk: str) -> Tuple[bool, Optional[str], str]:
        """
        处理流式文本块，隐藏函数调用详情
        返回: (should_stop_generation, extracted_function_call, clean_chunk_for_display)
        """
        self.buffer += chunk
        clean_chunk = chunk  # 默认原样输出
        
        # 快速检测：只有看到开始标签才进入解析模式
        if not self.start_tag_found:
            if '<function_calls>' in self.buffer:
                self.start_tag_found = True
                self.in_function_block = True
                
                # 计算应该隐藏的部分
                tag_start = self.buffer.find('<function_calls>')
                if tag_start >= 0:
                    # 只返回标签之前的内容
                    clean_chunk = chunk[:chunk.find('<function_calls>')] if '<function_calls>' in chunk else ""
                    
                    # 显示简化提示
                    if not self.function_hint_shown:
                        clean_chunk += "\n🔧 执行中..."
                        self.function_hint_shown = True
                
            else:
                # 保留最近的一些字符，防止标签被分割
                if len(self.buffer) > 20:
                    self.buffer = self.buffer[-20:]
                return False, None, clean_chunk
        else:
            # 在函数块内，隐藏所有内容
            clean_chunk = ""
        
        # 已经在函数块内，检查结束标签
        if self.in_function_block and '</function_calls>' in self.buffer:
            # 提取完整的函数调用块
            pattern = r'<function_calls>(.*?)</function_calls>'
            match = re.search(pattern, self.buffer, re.DOTALL)
            if match:
                function_call = match.group(0)
                return True, function_call, ""  # 结束时不输出任何内容
                
        return False, None, clean_chunk


class AIGirlfriendChatHandler:
    """AI女友聊天处理器 - 整合所有模块的核心处理器"""
    
    def __init__(self, api_key: str = None):
        self.client = Anthropic(api_key=api_key or ANTHROPIC_API_KEY)
        self.detector = StreamFunctionDetector()
        self.max_depth = MAX_CONVERSATION_DEPTH
        
        # 确保函数已注册
        import functions  # 这会触发函数注册
        
        # 记录系统启动
        log_manager.log_system_start()
        
        # 尝试加载最新会话
        self.initialize_session()
    
    def get_response_stream(self, system_prompt: str, 
                          on_text_chunk: Callable[[str], None] = None,
                          on_function_detected: Callable[[str], None] = None) -> Tuple[str, bool]:
        """
        获取流式响应
        返回: (full_content, has_function_calls)
        """
        self.detector.reset()
        full_content = ""
        
        try:
            with self.client.messages.stream(
                model=AI_MODEL,
                system=system_prompt,
                messages=self.context,
                max_tokens=CHAT_CONFIG["max_tokens"],
                temperature=CHAT_CONFIG["temperature"],
            ) as stream:
                
                for event in stream:
                    if event.type == "content_block_delta" and hasattr(event.delta, 'text'):
                        chunk = event.delta.text
                        full_content += chunk
                        
                        # 检测函数调用（新版本返回clean_chunk）
                        should_stop, function_call, clean_chunk = self.detector.feed_chunk(chunk)
                        
                        if should_stop and function_call:
                            # 检测到完整函数调用，截断生成
                            if on_function_detected:
                                on_function_detected(function_call)
                            return full_content, True
                        
                        # 输出清理后的文本（隐藏函数调用内容）
                        if on_text_chunk and clean_chunk:
                            on_text_chunk(clean_chunk)
                        
                
        except Exception as e:
            error_msg = error_handler.handle_api_error(e)
            print(error_msg)
            return full_content, False
            
        return full_content, False
    
    def initialize_session(self):
        """初始化会话 - 尝试加载最新会话或创建新会话"""
        if session_manager.load_latest_session():
            log_manager.log_session_loaded(session_manager.current_session_id)
            print(f"🔄 已加载会话: {session_manager.current_session_id}")
        else:
            session_id = session_manager.create_new_session()
            log_manager.log_session_created(session_id)
            print(f"🆕 创建新会话: {session_id}")
    
    def check_session_timeout(self):
        """检查会话超时并处理"""
        if session_manager.check_timeout():
            old_session = session_manager.current_session_id
            new_session = session_manager.create_new_session()
            log_manager.log_session_timeout(old_session, new_session)
            print(f"\n⏰ 会话超时，创建新会话: {new_session}")
            return True
        return False
    
    def load_session_by_id(self, session_id: str) -> bool:
        """加载指定ID的会话"""
        if session_manager.load_session(session_id):
            log_manager.log_session_loaded(session_id)
            print(f"✅ 已切换到会话: {session_id}")
            return True
        else:
            log_manager.log_session_loaded(session_id, success=False)
            print(f"❌ 会话加载失败: {session_id}")
            return False
    
    def get_current_context(self) -> List[Dict]:
        """获取当前对话上下文"""
        return session_manager.get_current_context()
    
    def add_user_message(self, message: str):
        """添加用户消息"""
        # 检查会话超时
        self.check_session_timeout()
        
        session_manager.add_message("user", message)
        log_manager.log_user_message(message)
    
    def add_assistant_message(self, message: str):
        """添加助手消息"""
        session_manager.add_message("assistant", message)
        log_manager.log_assistant_message(message)
    
    def clear_context(self):
        """清空对话上下文"""
        session_manager.clear_current_session()
        log_manager.log_context_cleared()
    
    def process_conversation_turn(self, depth: int = 0,
                                on_text_chunk: Callable[[str], None] = None,
                                on_function_call: Callable[[List[FunctionResult]], None] = None) -> str:
        """
        处理一轮对话
        
        Args:
            depth: 当前递归深度
            on_text_chunk: 文本块回调
            on_function_call: 函数调用结果回调
        
        Returns:
            最终响应内容
        """
        if depth >= self.max_depth:
            return "错误: 达到最大对话深度限制"
        
        # 生成动态系统提示
        functions_xml = function_registry.generate_xml()
        system_prompt = prompt_manager.update_system_prompt(functions_xml)
        
        # 使用会话管理器的上下文
        self.context = session_manager.get_current_context()
        
        # 获取流式响应
        response_content, has_function_calls = self.get_response_stream(
            system_prompt, 
            on_text_chunk=on_text_chunk
        )
        
        # 记录API调用
        log_manager.log_api_call(AI_MODEL)
        
        # 添加助手响应到会话
        self.add_assistant_message(response_content)
        
        if has_function_calls:
            # 记录函数调用检测
            log_manager.log_function_detection(response_content)
            
            # 执行函数调用
            results = function_registry.parse_and_execute(response_content)
            
            # 记录所有函数调用结果
            for result in results:
                log_manager.log_function_call(
                    result.function_name,
                    result.parameters or {},
                    result.success,
                    result.content if result.success else result.error
                )
            
            # 回调通知函数调用结果
            if on_function_call:
                on_function_call(results)
            
            # 检查是否有需要确认的函数
            needs_confirmation = any(r.needs_confirmation for r in results)
            if needs_confirmation:
                # 如果有函数需要确认，暂停递归，等待用户确认
                function_response = function_registry.format_results(results)
                session_manager.add_message("assistant", function_response)
                return response_content
            
            # 格式化结果并添加到会话
            function_response = function_registry.format_results(results)
            session_manager.add_message("assistant", function_response)
            
            # 递归继续对话
            return self.process_conversation_turn(
                depth + 1, 
                on_text_chunk,
                on_function_call
            )
        
        return response_content
    
    def handle_confirmation(self, user_input: str) -> bool:
        """
        处理用户确认输入
        
        Args:
            user_input: 用户输入
            
        Returns:
            是否确认执行
        """
        return user_input.strip().lower() in ['y', 'yes', '是', '确认']


# 创建全局实例
chat_handler = AIGirlfriendChatHandler()