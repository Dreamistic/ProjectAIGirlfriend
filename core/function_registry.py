import re
import json
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
from config.settings import FUNCTION_SUCCESS_MESSAGE


@dataclass
class FunctionResult:
    """函数调用结果"""
    success: bool
    content: str
    function_name: str = ""
    parameters: Dict = None
    error: str = ""
    needs_confirmation: bool = False


class SmartParameterParser:
    """智能参数解析器 - 来自function_core.py的优化版本"""
    
    @staticmethod
    def parse_value(value: str) -> Any:
        """智能解析参数值"""
        if not isinstance(value, str):
            return value
            
        value = value.strip()
        
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


class UnifiedFunctionRegistry:
    """统一的函数注册器 - 整合新旧版本特性"""
    
    def __init__(self):
        self._functions: Dict[str, Callable] = {}
        self._descriptions: Dict[str, dict] = {}
    
    @staticmethod
    def format_result_xml(content: str, success: bool) -> str:
        """格式化函数调用结果为XML - 来自0218.py"""
        tag = "success" if success else "failed"
        return f"<{tag}>{content}</{tag}>"
    
    def register(self, name: str, func: Callable, description: str = None, 
                parameters: Dict = None, required: List[str] = None):
        """
        注册函数 - 整合两个版本的特性
        
        Args:
            name: 函数名
            func: 函数对象
            description: 函数描述
            parameters: 参数定义
            required: 必需参数列表
        """
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
            
            # 处理需要确认的情况 - 来自0218.py的逻辑
            if isinstance(result, str) and "需要用户输入Y确认" in result:
                return FunctionResult(
                    success=False,
                    content=result,
                    function_name=name,
                    parameters=kwargs,
                    needs_confirmation=True
                )
            
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
    
    def generate_xml(self) -> str:
        """生成XML格式的函数描述 - 来自0218.py的优化版本"""
        xml_parts = []
        
        for name, info in self._descriptions.items():
            function_xml = [f'      <function name="{name}">']
            function_xml.append(f'        <description>{info["description"]}</description>')
            
            if info["parameters"]:
                for param_name, param_info in info["parameters"].items():
                    param_xml = [f'          <parameter name="{param_name}" type="{param_info["type"]}">']
                    param_xml.append(f'            <description>{param_info["description"]}</description>')
                    
                    if "options" in param_info:
                        param_xml.append('            <options>')
                        for option in param_info["options"]:
                            option_xml = [f'              <option value="{option["value"]}">']
                            option_xml.append(f'                <description>{option["description"]}</description>')
                            if "usage" in option:
                                option_xml.append(f'                <usage>{option["usage"]}</usage>')
                            option_xml.append('              </option>')
                            param_xml.extend(option_xml)
                        param_xml.append('            </options>')
                    
                    param_xml.append('          </parameter>')
                    function_xml.extend(param_xml)
            
            function_xml.append('      </function>')
            xml_parts.append('\n'.join(function_xml))
        
        return '\n'.join(xml_parts)
    
    def parse_and_execute(self, xml_content: str) -> List[FunctionResult]:
        """解析XML并执行所有函数调用 - 来自function_core.py的优化版本"""
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
            if result.needs_confirmation:
                # 需要确认的情况
                formatted_responses.append(self.format_result_xml(result.content, False))
            elif result.success:
                formatted_responses.append(self.format_result_xml(result.content, True))
            else:
                error_msg = result.error or "未知错误"
                formatted_responses.append(self.format_result_xml(error_msg, False))
        
        return f"<function_response>{''.join(formatted_responses)}</function_response>"
    
    def get_function_list(self) -> List[str]:
        """获取所有注册的函数名列表"""
        return list(self._functions.keys())
    
    def get_function_info(self, name: str) -> Optional[dict]:
        """获取指定函数的信息"""
        return self._descriptions.get(name)


# 创建全局实例
function_registry = UnifiedFunctionRegistry()