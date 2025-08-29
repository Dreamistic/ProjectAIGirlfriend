#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI女友项目 - 重构版主程序
简单的调试对话界面
"""

import os
import sys
from typing import List
from config.settings import ANTHROPIC_API_KEY, AI_MODEL
from core.chat_handler import chat_handler
from core.function_registry import FunctionResult, function_registry


class DebugChatInterface:
    """简单的调试聊天界面"""
    
    def __init__(self):
        self.handler = chat_handler
        self.pending_confirmation = False
        self.pending_results = []
        
    def print_header(self):
        """打印程序头部信息"""
        print("=" * 50)
        print("林晚晴")
        print(f"📱 模型: {AI_MODEL}")
        print(f"⚡ 流式输出: 启用")
        print(f"🔧 函数调用: 启用")
        print("=" * 50)
        print("命令帮助:")
        print("  exit/quit  - 退出程序")
        print("  clear      - 清空对话历史")
        print("  context    - 查看对话历史")
        print("  functions  - 查看可用函数")
        print("  sessions   - 查看所有会话")
        print("  newsession - 创建新会话")
        print("  sysprompt  - 导出当前系统提示词")
        print("-" * 50)
    
    def print_functions(self):
        """显示可用函数列表"""
        functions = function_registry.get_function_list()
        print(f"📋 可用函数 ({len(functions)}个):")
        for func_name in functions:
            info = function_registry.get_function_info(func_name)
            if info:
                print(f"  • {func_name} - {info['description']}")
        print()
    
    def stream_text_handler(self, chunk: str):
        """处理流式文本输出"""
        print(chunk, end='', flush=True)
    
    def function_call_handler(self, results: List[FunctionResult]):
        """处理函数调用结果"""
        print("\n🔧 函数调用:")
        for result in results:
            status = "✅" if result.success else "❌"
            print(f"  {status} {result.function_name}")
            if result.needs_confirmation:
                print(f"     ⚠️  需要确认: {result.content}")
                self.pending_confirmation = True
                self.pending_results = results
            elif result.success:
                print(f"     ✓ {result.content}")
            else:
                print(f"     ✗ {result.error}")
        print()
    
    def handle_command(self, user_input: str) -> bool:
        """
        处理用户命令
        
        Returns:
            True: 继续程序, False: 退出程序
        """
        command = user_input.strip().lower()
        
        if command in ['exit', 'quit']:
            print("👋 再见!")
            return False
        elif command == 'clear':
            self.handler.clear_context()
            print("✅ 对话历史已清空")
            return True
        elif command == 'context':
            context = self.handler.get_current_context()
            from core.session_manager import session_manager
            session_id = session_manager.current_session_id or "未知"
            print(f"📝 对话历史 ({len(context)}条) - 会话: {session_id}")
            for i, msg in enumerate(context, 1):
                role_icon = "👤" if msg['role'] == 'user' else "🤖"
                content_preview = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
                print(f"  {i}. {role_icon} {content_preview}")
            print()
            return True
        elif command == 'functions':
            self.print_functions()
            return True
        elif command == 'sessions':
            # 导入会话管理器来访问会话信息
            from core.session_manager import session_manager
            print("📋 会话管理:")
            print(f"  当前会话: {session_manager.current_session_id}")
            # 这里可以添加更多会话管理功能
            return True
        elif command == 'newsession':
            from core.session_manager import session_manager
            from core.log_manager import log_manager
            old_session = session_manager.current_session_id
            new_session = session_manager.create_new_session()
            log_manager.log_session_created(new_session)
            print(f"🆕 创建新会话: {new_session}")
            if old_session:
                print(f"   原会话: {old_session}")
            return True
        elif command == 'sysprompt':
            from core.function_registry import function_registry
            from core.prompt_manager import prompt_manager
            
            # 生成完整的系统提示词
            functions_xml = function_registry.generate_xml()
            system_prompt = prompt_manager.update_system_prompt(functions_xml)
            
            print("📋 当前系统提示词:")
            print("=" * 60)
            print(system_prompt)
            print("=" * 60)
            return True
        else:
            return True
    
    def run(self):
        """运行聊天界面"""
        # 检查API密钥
        if not ANTHROPIC_API_KEY:
            print("❌ 请设置 ANTHROPIC_API_KEY 环境变量")
            return
        
        self.print_header()
        
        while True:
            try:
                # 获取用户输入
                if self.pending_confirmation:
                    user_input = input("⚠️  请确认 (Y/N): ").strip()
                    
                    if self.handler.handle_confirmation(user_input):
                        print("✅ 已确认执行")
                        # 这里可以继续处理确认后的逻辑
                    else:
                        print("❌ 已取消操作")
                    
                    self.pending_confirmation = False
                    self.pending_results = []
                    continue
                else:
                    user_input = input("\n👤 用户: ").strip()
                
                if not user_input:
                    continue
                
                # 处理命令
                if user_input.startswith('/') or user_input.lower() in ['exit', 'quit', 'clear', 'context', 'functions', 'sessions', 'newsession', 'sysprompt']:
                    if not self.handle_command(user_input.lstrip('/')):
                        break
                    continue
                
                # 添加用户消息
                self.handler.add_user_message(user_input)
                
                print("林晚晴: ", end='', flush=True)
                
                # 处理对话
                response = self.handler.process_conversation_turn(
                    on_text_chunk=self.stream_text_handler,
                    on_function_call=self.function_call_handler
                )
                
                if not self.pending_confirmation:
                    print()  # 换行
                
            except KeyboardInterrupt:
                print("\n\n👋 程序被中断，再见!")
                break
            except Exception as e:
                print(f"\n❌ 程序出错: {str(e)}")
                continue


def main():
    """主程序入口"""
    interface = DebugChatInterface()
    interface.run()


if __name__ == "__main__":
    main()