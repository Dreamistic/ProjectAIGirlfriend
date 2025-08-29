import re
import requests
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from typing import Dict, List, Callable, Tuple
from dataclasses import dataclass
import time
from asyncio import Semaphore
from anthropic import Anthropic
from function_core import StreamingChatHandler, ModernFunctionRegistry, FunctionResult


class Agent:
    def __init__(self):
        # 初始化处理器
        self.handler = StreamingChatHandler()
        
        # 修改模型为用户指定的版本
        self.handler.client.model = "claude-sonnet-4-20250514"
        
        self.setup_functions()
        self.setup_system_prompt()
        self.system_prompt = self.read_system_prompt()

    
    def setup_functions(self):
        """注册测试函数"""
        registry = self.handler.registry
        
    def update_system_prompt(self, system_prompt: str) -> str:
            """更新system_prompt中的functions部分"""
        
            # 生成新的functions内容
        new_functions = self.generate_xml()
            #print(new_functions)
        # 替换system_prompt中的functions部分
        system_prompt = re.sub(r'<function_system>.*?</function_system>', f"""<function_system>\n      <rule>请在请求函数调用后立即停止回复，等待函数调用</rule>\n{new_functions}\n    <function_rules>
        <rule>使用XML格式调用函数</rule>
        <rule>等待函数响应后继续</rule>
        <example>
            <function_calls>
            <invoke name="function_name">
                <parameter name="param_name">param_value</parameter>
            </invoke>
            </function_calls>
        </example>
        </function_rules>\n</function_system>""", system_prompt, flags=re.DOTALL)
        #    return new_functions
        weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        current_time = time.strftime("%Y-%m-%d %H:%M") + f" {weekday_names[time.localtime().tm_wday]}"
        updated_prompt = re.sub(r'<current_time>.*?</current_time>', f'<current_time>{current_time}</current_time>', updated_prompt, flags=re.DOTALL)
        return updated_prompt    

    def read_system_prompt():
        try:
            with open('D:\ProjectAIGirlfriend\system_prompt2.xml', 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"读取system_prompt.xml时出错: {str(e)}")
        return None
    
    def setup_system_prompt(self):
        """设置系统提示"""
        self.system_prompt = self.read_system_prompt()
        self.system_prompt = self.update_system_prompt(self.system_prompt)


    def stream_text_handler(self, chunk: str):
        """处理流式文本输出"""
        print(chunk, end='', flush=True)
    
    def function_detected_handler(self, function_call: str):
        """函数调用检测回调"""
        print(f"\n🔧 检测到函数调用:\n{function_call}")
    
    def run_conversation(self):
        while True:
            try:
                user_input = input("\n👤 用户: ").strip()
                
                if user_input.lower() == 'quit':
                    break
                elif user_input.lower() == 'clear':
                    self.handler.context.clear()
                    print("✅ 上下文已清空")
                    continue
                elif user_input.lower() == 'context':
                    print("📋 当前上下文:")
                    for i, msg in enumerate(self.handler.context):
                        print(f"  {i+1}. {msg['role']}: {msg['content'][:100]}...")
                    continue
                
                if not user_input:
                    continue
                
                # 添加用户消息到上下文
                self.handler.context.append({
                    "role": "user", 
                    "content": user_input
                })
                
                print("🤖 助手: ", end='', flush=True)
                
                # 处理对话轮次 - 这里会自动处理流式输出和函数调用
                response = self.handler.process_conversation_turn(
                    self.system_prompt,
                    on_text_chunk=self.stream_text_handler
                )
                
                print()  # 换行
                
            except KeyboardInterrupt:
                print("\n\n👋 程序被中断")
                break
            except Exception as e:
                print(f"\n❌ 错误: {str(e)}")


if __name__ == "__main__":
    agent = Agent()
    agent.run_conversation()