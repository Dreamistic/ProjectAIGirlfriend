#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
0827.py - 整合流式传输、现代函数调用和Todo系统的AI女友项目核心
结合了test_function_core的流式功能、function_core的现代调用方法和todo_system注册
"""

import re
import json
import time
import os
from typing import Dict, List, Callable, Any, Optional, Tuple
from dataclasses import dataclass
from anthropic import Anthropic

# ===== 核心数据结构 =====

@dataclass
class FunctionResult:
    """函数调用结果"""
    success: bool
    content: str
    function_name: str = ""
    parameters: Dict = None
    error: str = ""

# ===== Todo系统 =====

TODO_HIGH = "high"
TODO_MEDIUM = "medium"
TODO_LOW = "low"

class TodoList:
    """Todo管理系统"""
    def __init__(self):
        self.todos = []

    def add(self, content, priority="medium"):
        todo = {
            "id": len(self.todos) + 1,
            "content": content,
            "status": "pending",
            "priority": priority
        }
        self.todos.append(todo)
        return todo

    def modify(self, id, content, priority):
        for todo in self.todos:
            if todo["id"] == id:
                todo["content"] = content
                todo["priority"] = priority
                return todo
        return None

    def delete(self, id):
        for todo in self.todos:
            if todo["id"] == id:
                self.todos.remove(todo)
                return todo
        return None

    def update_all(self, todos_data):
        """批量更新todo列表"""
        self.todos.clear()
        
        for i, todo_data in enumerate(todos_data, 1):
            todo = {
                "id": i,
                "content": todo_data["content"],
                "status": todo_data.get("status", "pending"),
                "priority": todo_data.get("priority", "medium")
            }
            self.todos.append(todo)
        
        return self.todos
    
    def get_all(self):
        """获取所有todo"""
        return self.todos
    
    def update_status(self, id, status):
        """更新单个todo的状态"""
        for todo in self.todos:
            if todo["id"] == id:
                todo["status"] = status
                return todo
        return None
    
    def get_by_status(self, status):
        """根据状态筛选todo"""
        return [todo for todo in self.todos if todo["status"] == status]

# ===== 流式函数检测器 =====

class StreamFunctionDetector:
    """流式函数调用检测器 - 专注XML文本格式"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """重置检测器状态"""
        self.buffer = ""
        self.in_function_block = False
        self.start_tag_found = False
        
    def feed_chunk(self, chunk: str) -> Tuple[bool, Optional[str]]:
        """
        处理流式文本块，优化XML解析性能
        返回: (should_stop_generation, extracted_function_call)
        """
        self.buffer += chunk
        
        # 快速检测：只有看到开始标签才进入解析模式
        if not self.start_tag_found:
            if '<function_calls>' in self.buffer:
                self.start_tag_found = True
                self.in_function_block = True
            else:
                # 保留最近的一些字符，防止标签被分割
                if len(self.buffer) > 20:
                    self.buffer = self.buffer[-20:]
                return False, None
        
        # 已经在函数块内，检查结束标签
        if self.in_function_block and '</function_calls>' in self.buffer:
            # 提取完整的函数调用块
            pattern = r'<function_calls>(.*?)</function_calls>'
            match = re.search(pattern, self.buffer, re.DOTALL)
            if match:
                function_call = match.group(0)
                return True, function_call
                
        return False, None

# ===== 智能参数解析器 =====

class SmartParameterParser:
    """智能参数解析器"""
    
    @staticmethod
    def parse_value(value: str) -> Any:
        """智能解析参数值"""
        if not isinstance(value, str):
            return value
            
        value = value.strip()
        
        # 空值处理
        if not value:
            return ""
            
        # JSON对象/数组检测
        if (value.startswith('{') and value.endswith('}')) or \
           (value.startswith('[') and value.endswith(']')):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        
        # 布尔值检测
        if value.lower() in ['true', 'false']:
            return value.lower() == 'true'
        
        # 数字检测
        if value.replace('-', '').replace('.', '').isdigit():
            try:
                return int(value) if '.' not in value else float(value)
            except ValueError:
                pass
                
        # 默认返回字符串
        return value
    
    @staticmethod
    def parse_xml_parameters(xml_params: str) -> Dict[str, Any]:
        """解析XML格式的参数"""
        parameters = {}
        param_matches = re.findall(
            r'<parameter name="(.*?)">(.*?)</parameter>',
            xml_params,
            re.DOTALL
        )
        
        for param_name, param_value in param_matches:
            parameters[param_name] = SmartParameterParser.parse_value(param_value)
        
        return parameters

# ===== 现代化函数注册器 =====

class ModernFunctionRegistry:
    """现代化函数注册器"""
    
    def __init__(self):
        self._functions: Dict[str, Callable] = {}
        self._descriptions: Dict[str, dict] = {}
    
    def register(self, name: str, func: Callable, description: str = None, 
                parameters: Dict = None, required: List[str] = None):
        """注册函数"""
        self._functions[name] = func
        self._descriptions[name] = {
            "name": name,
            "description": description or func.__doc__ or "No description available",
            "parameters": parameters or {},
            "required": required or []
        }
    
    def call(self, name: str, **kwargs) -> FunctionResult:
        """调用函数并返回标准化结果"""
        if name not in self._functions:
            return FunctionResult(
                success=False,
                content="",
                function_name=name,
                error=f"Function '{name}' not found"
            )
        
        try:
            result = self._functions[name](**kwargs)
            return FunctionResult(
                success=True,
                content=str(result),
                function_name=name,
                parameters=kwargs
            )
        except Exception as e:
            return FunctionResult(
                success=False,
                content="",
                function_name=name,
                parameters=kwargs,
                error=str(e)
            )
    
    def parse_and_execute(self, xml_content: str) -> List[FunctionResult]:
        """解析XML并执行所有函数调用"""
        results = []
        
        # 提取所有function_calls块
        function_blocks = re.findall(
            r'<function_calls>(.*?)</function_calls>',
            xml_content,
            re.DOTALL
        )
        
        for block in function_blocks:
            # 提取所有invoke调用
            invokes = re.findall(
                r'<invoke name="(.*?)">(.*?)</invoke>',
                block,
                re.DOTALL
            )
            
            for func_name, params_xml in invokes:
                # 智能解析参数
                parameters = SmartParameterParser.parse_xml_parameters(params_xml)
                
                # 执行函数调用
                result = self.call(func_name, **parameters)
                results.append(result)
        
        return results
    
    def format_results(self, results: List[FunctionResult]) -> str:
        """格式化函数调用结果"""
        if not results:
            return ""
            
        formatted_responses = []
        for result in results:
            if result.success:
                formatted_responses.append(f"<success>{result.content}</success>")
            else:
                formatted_responses.append(f"<failed>{result.error}</failed>")
        
        return f"<function_response>{''.join(formatted_responses)}</function_response>"

# ===== 流式对话处理器 =====

class StreamingChatHandler:
    """流式对话处理器"""
    
    def __init__(self, api_key: str = None):
        self.client = Anthropic(api_key=api_key or os.getenv('ANTHROPIC_API_KEY'))
        self.registry = ModernFunctionRegistry()
        self.detector = StreamFunctionDetector()
        self.context = []
        self.max_depth = 5
        
        # 初始化Todo系统
        self.todo_list = TodoList()
        self.setup_todo_functions()
    
    def setup_todo_functions(self):
        """设置Todo相关的函数"""
        # 注册批量更新todo函数
        self.registry.register(
            "batch_update_todos",
            self.batch_update_todos,
            "批量更新todo列表",
            {
                "todos_data": {
                    "type": "array",
                    "description": "todo数据列表，包含content, status, priority字段"
                }
            },
            ["todos_data"]
        )
        
        # 注册添加todo函数
        self.registry.register(
            "add_todo",
            self.add_todo,
            "添加新的todo项目",
            {
                "content": {
                    "type": "string",
                    "description": "任务内容描述"
                },
                "priority": {
                    "type": "string",
                    "description": "优先级：high/medium/low",
                    "enum": ["high", "medium", "low"]
                }
            },
            ["content"]
        )
        
        # 注册获取todo函数
        self.registry.register(
            "get_todos",
            self.get_todos,
            "获取todo列表",
            {
                "status": {
                    "type": "string",
                    "description": "按状态筛选：pending/in_progress/completed，不填则返回全部",
                    "enum": ["pending", "in_progress", "completed"]
                }
            }
        )
        
        # 注册更新todo状态函数
        self.registry.register(
            "update_todo_status",
            self.update_todo_status,
            "更新todo的状态",
            {
                "id": {
                    "type": "integer",
                    "description": "todo的ID"
                },
                "status": {
                    "type": "string",
                    "description": "新状态：pending/in_progress/completed",
                    "enum": ["pending", "in_progress", "completed"]
                }
            },
            ["id", "status"]
        )
    
    def batch_update_todos(self, todos_data):
        """批量更新todo的实现函数"""
        # 如果是字符串（JSON），先解析
        if isinstance(todos_data, str):
            todos_data = json.loads(todos_data)
        
        result = self.todo_list.update_all(todos_data)
        return f"成功批量更新了{len(result)}个todo项目"
    
    def add_todo(self, content: str, priority: str = "medium"):
        """添加todo的实现函数"""
        todo = self.todo_list.add(content, priority)
        return f"成功添加todo：ID {todo['id']} - {content} (优先级：{priority})"
    
    def get_todos(self, status: str = None):
        """获取todo的实现函数"""
        if status:
            todos = self.todo_list.get_by_status(status)
            return f"状态为{status}的todo：{json.dumps(todos, ensure_ascii=False)}"
        else:
            todos = self.todo_list.get_all()
            return f"所有todo：{json.dumps(todos, ensure_ascii=False)}"
    
    def update_todo_status(self, id: int, status: str):
        """更新todo状态的实现函数"""
        todo = self.todo_list.update_status(id, status)
        if todo:
            return f"成功更新todo {id} 的状态为 {status}"
        else:
            return f"未找到ID为 {id} 的todo"
    
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
                model="claude-sonnet-4-20250514",
                system=system_prompt,
                messages=self.context,
                max_tokens=4086,
                temperature=0.7,
            ) as stream:
                
                for event in stream:
                    if event.type == "content_block_delta" and hasattr(event.delta, 'text'):
                        chunk = event.delta.text
                        full_content += chunk
                        
                        # 检测函数调用
                        should_stop, function_call = self.detector.feed_chunk(chunk)
                        
                        if should_stop and function_call:
                            # 检测到完整函数调用，截断生成
                            if on_function_detected:
                                on_function_detected(function_call)
                            return full_content, True
                        
                        # 继续流式输出文本
                        if on_text_chunk:
                            on_text_chunk(chunk)
                        
                
        except Exception as e:
            print(f"Stream error: {e}")
            return full_content, False
            
        return full_content, False
    
    def process_conversation_turn(self, system_prompt: str, depth: int = 0,
                                on_text_chunk: Callable[[str], None] = None) -> str:
        """处理一轮对话"""
        if depth >= self.max_depth:
            return "错误: 达到最大对话深度限制"
        
        # 获取流式响应
        response_content, has_function_calls = self.get_response_stream(
            system_prompt, 
            on_text_chunk=on_text_chunk
        )
        
        # 添加到上下文
        self.context.append({"role": "assistant", "content": response_content})
        
        if has_function_calls:
            # 执行函数调用
            results = self.registry.parse_and_execute(response_content)
            
            # 格式化结果并添加到上下文
            function_response = self.registry.format_results(results)
            self.context.append({"role": "assistant", "content": function_response})
            
            # 递归继续对话
            return self.process_conversation_turn(
                system_prompt, 
                depth + 1, 
                on_text_chunk
            )
        
        return response_content

# ===== 测试函数 =====

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

# ===== 主测试类 =====

class AIGirlfriendCore:
    def __init__(self):
        # 初始化处理器
        self.handler = StreamingChatHandler()
        self.setup_all_functions()
        self.setup_system_prompt()
    
    def setup_all_functions(self):
        """注册所有测试函数"""
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
        self.system_prompt = """你是一个智能AI女友助手，可以调用函数来帮助用户管理任务和日常需求。

可用函数:
- get_weather: 查询天气信息
- create_memory: 创建记忆 
- send_message: 发送消息
- calculate: 数学计算
- add_todo: 添加新任务
- batch_update_todos: 批量更新任务列表
- get_todos: 获取任务列表
- update_todo_status: 更新任务状态

调用函数时使用以下XML格式:
<function_calls>
  <invoke name="function_name">
    <parameter name="param_name">param_value</parameter>
  </invoke>
</function_calls>

请根据用户需求智能选择和调用函数，以温暖体贴的方式与用户交流。
"""

    def stream_text_handler(self, chunk: str):
        """处理流式文本输出"""
        print(chunk, end='', flush=True)
    
    def function_detected_handler(self, function_call: str):
        """函数调用检测回调"""
        print(f"\n🔧 检测到函数调用:\n{function_call}")
    
    def run_interactive_mode(self):
        """运行交互模式"""
        print("=== AI女友 - 0827整合版 ===")
        print("输入 'quit' 退出，'clear' 清空上下文，'todos' 查看当前任务")
        print("支持的功能:")
        print("- 天气查询: '查询北京天气'")
        print("- 任务管理: '添加任务：学习Python'")
        print("- 计算功能: '计算 2+3*4'") 
        print("- 记忆功能: '记住我喜欢喝咖啡'")
        print("- 消息功能: '给小明发消息说你好'")
        print("-" * 50)
        
        while True:
            try:
                user_input = input("\n💕 你: ").strip()
                
                if user_input.lower() == 'quit':
                    print("👋 再见，我会想你的~")
                    break
                elif user_input.lower() == 'clear':
                    self.handler.context.clear()
                    print("✅ 对话历史已清空")
                    continue
                elif user_input.lower() == 'todos':
                    todos = self.handler.todo_list.get_all()
                    print("📋 当前任务列表:")
                    for todo in todos:
                        status_emoji = "✅" if todo['status'] == 'completed' else "🔄" if todo['status'] == 'in_progress' else "📌"
                        print(f"  {status_emoji} {todo['id']}. {todo['content']} [{todo['priority']}]")
                    continue
                elif user_input.lower() == 'context':
                    print("📋 当前对话上下文:")
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
                
                print("🤖 AI女友: ", end='', flush=True)
                
                # 处理对话轮次 - 自动处理流式输出和函数调用
                response = self.handler.process_conversation_turn(
                    self.system_prompt,
                    on_text_chunk=self.stream_text_handler
                )
                
                print()  # 换行
                
            except KeyboardInterrupt:
                print("\n\n👋 程序被中断，再见~")
                break
            except Exception as e:
                print(f"\n❌ 出错了: {str(e)}")

    def run_batch_test(self):
        """运行批量测试"""
        print("\n🧪 开始批量测试...")
        
        test_cases = [
            "添加几个任务：学习Python高级功能、完成AI女友项目、准备技术分享",
            "查询一下北京的天气情况",
            "帮我计算 25 * 4 + 10",  
            "记住我今天整合了流式传输和Todo系统",
            "把第一个任务状态改为进行中"
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n--- 测试 {i}: {test_case} ---")
            
            self.handler.context = [{
                "role": "user",
                "content": test_case  
            }]
            
            print("🤖 AI女友: ", end='', flush=True)
            response = self.handler.process_conversation_turn(
                self.system_prompt,
                on_text_chunk=self.stream_text_handler
            )
            print("\n")
            time.sleep(1)  # 稍作停顿

def main():
    # 检查API密钥
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("❌ 请设置 ANTHROPIC_API_KEY 环境变量")
        return
    
    ai_girlfriend = AIGirlfriendCore()
    
    # 选择运行模式
    print("选择运行模式:")
    print("1. 交互式对话模式")
    print("2. 批量测试模式")
    
    choice = input("请选择 (1-2): ").strip()
    
    if choice == "1":
        ai_girlfriend.run_interactive_mode()
    elif choice == "2":
        ai_girlfriend.run_batch_test()
    else:
        print("无效选择，启动交互模式...")
        ai_girlfriend.run_interactive_mode()

if __name__ == "__main__":
    main()