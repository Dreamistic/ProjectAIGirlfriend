import re
import json
import time
from typing import Dict, List, Callable, Any, Optional, Tuple
from dataclasses import dataclass
from anthropic import Anthropic
import os

@dataclass
class FunctionResult:
    """函数调用结果"""
    success: bool
    content: str
    function_name: str = ""
    parameters: Dict = None
    error: str = ""

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

class StreamingChatHandler:
    """流式对话处理器"""
    
    def __init__(self, api_key: str = None):
        self.client = Anthropic(api_key=api_key or os.getenv('ANTHROPIC_API_KEY'))
        self.registry = ModernFunctionRegistry()
        self.detector = StreamFunctionDetector()
        self.context = []
        self.max_depth = 5
    
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

# 导出主要类
__all__ = [
    'ModernFunctionRegistry', 
    'StreamingChatHandler', 
    'FunctionResult',
    'SmartParameterParser'
]