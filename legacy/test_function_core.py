#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
function_core.py 流式函数调用测试脚本
"""

import os
import time
import json
from function_core import StreamingChatHandler, ModernFunctionRegistry, FunctionResult

def test_get_weather(city: str) -> str:
    """获取天气信息的测试函数"""
    weather_data = {
        "北京": "晴天 15°C",
        "上海": "多云 18°C", 
        "广州": "小雨 22°C",
        "深圳": "阴天 20°C"
    }
    return weather_data.get(city, f"{city}的天气信息暂时无法获取")

def test_create_memory(content: str, priority: str = "short") -> str:
    """创建记忆的测试函数"""
    print(f"📝 创建记忆: {content} (优先级: {priority})")
    return f"成功创建{priority}级记忆: {content}"

def test_send_message(recipient: str, message: str) -> str:
    """发送消息的测试函数"""
    print(f"📤 发送消息给 {recipient}: {message}")
    return f"消息已发送给{recipient}"

def test_calculate(expression: str) -> str:
    """安全的计算器函数"""
    try:
        # 简单的安全检查
        allowed_chars = set('0123456789+-*/.() ')
        if not all(c in allowed_chars for c in expression):
            return "错误: 包含非法字符"
        
        result = eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"

class FunctionCoreTester:
    def __init__(self):
        # 初始化处理器
        self.handler = StreamingChatHandler()
        
        # 修改模型为用户指定的版本
        self.handler.client.model = "claude-sonnet-4-20250514"
        
        self.setup_functions()
        self.setup_system_prompt()
    
    def setup_functions(self):
        """注册测试函数"""
        registry = self.handler.registry
        
        # 注册天气查询函数
        registry.register(
            "get_weather",
            test_get_weather,
            "获取指定城市的天气信息",
            {
                "city": {
                    "type": "string",
                    "description": "要查询天气的城市名称"
                }
            },
            ["city"]
        )
        
        # 注册记忆创建函数
        registry.register(
            "create_memory", 
            test_create_memory,
            "创建新的记忆条目",
            {
                "content": {
                    "type": "string", 
                    "description": "记忆内容"
                },
                "priority": {
                    "type": "string",
                    "description": "优先级: core/long/short"
                }
            },
            ["content"]
        )
        
        # 注册消息发送函数
        registry.register(
            "send_message",
            test_send_message, 
            "发送消息给指定收件人",
            {
                "recipient": {
                    "type": "string",
                    "description": "消息接收者"
                },
                "message": {
                    "type": "string", 
                    "description": "消息内容"
                }
            },
            ["recipient", "message"]
        )
        
        # 注册计算器函数
        registry.register(
            "calculate",
            test_calculate,
            "执行数学计算",
            {
                "expression": {
                    "type": "string",
                    "description": "数学表达式"
                }
            },
            ["expression"]
        )

    def setup_system_prompt(self):
        """设置系统提示"""
        self.system_prompt = """你是一个智能助手，可以调用函数来帮助用户。

可用函数:
- get_weather: 查询天气信息
- create_memory: 创建记忆 
- send_message: 发送消息
- calculate: 数学计算

调用函数时使用以下XML格式:
<function_calls>
  <invoke name="function_name">
    <parameter name="param_name">param_value</parameter>
  </invoke>
</function_calls>

请根据用户需求智能选择和调用函数。
"""

    def stream_text_handler(self, chunk: str):
        """处理流式文本输出"""
        print(chunk, end='', flush=True)
    
    def function_detected_handler(self, function_call: str):
        """函数调用检测回调"""
        print(f"\n🔧 检测到函数调用:\n{function_call}")
    
    def run_test_conversation(self):
        """运行测试对话"""
        print("=== Function Core 流式测试 ===")
        print("输入 'quit' 退出，'clear' 清空上下文")
        print("支持的测试命令:")
        print("- 查询北京天气")
        print("- 计算 2+3*4") 
        print("- 记住我喜欢喝咖啡")
        print("- 给小明发消息说你好")
        print("-" * 40)
        
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

    def run_single_test(self, message: str):
        """运行单个测试"""
        print(f"\n🧪 测试消息: {message}")
        print("-" * 40)
        
        self.handler.context = [{
            "role": "user",
            "content": message  
        }]
        
        print("🤖 助手: ", end='', flush=True)
        response = self.handler.process_conversation_turn(
            self.system_prompt,
            on_text_chunk=self.stream_text_handler
        )
        print("\n")
        return response

def main():
    # 检查API密钥
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("❌ 请设置 ANTHROPIC_API_KEY 环境变量")
        return
    
    tester = FunctionCoreTester()
    
    # 选择测试模式
    print("选择测试模式:")
    print("1. 交互式对话测试")
    print("2. 预设测试案例")
    
    choice = input("请选择 (1-2): ").strip()
    
    if choice == "1":
        tester.run_test_conversation()
    elif choice == "2":
        # 运行预设测试案例
        test_cases = [
            "查询一下北京的天气",
            "帮我计算 25 * 4 + 10",  
            "记住我今天学了Python函数调用",
            "给张三发个消息，告诉他会议时间改到下午3点"
        ]
        
        for test_case in test_cases:
            tester.run_single_test(test_case)
            time.sleep(2)  # 稍作停顿
    else:
        print("无效选择")

if __name__ == "__main__":
    main()