import logging
import traceback
from typing import Optional, Any, Dict
from pathlib import Path


class ErrorHandler:
    """统一错误处理器"""
    
    def __init__(self, log_file: Optional[Path] = None):
        self.logger = self._setup_logger(log_file)
    
    def _setup_logger(self, log_file: Optional[Path] = None) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('AIGirlfriend')
        logger.setLevel(logging.INFO)
        
        # 避免重复添加handler
        if not logger.handlers:
            # 控制台输出
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # 文件输出（如果指定）
            if log_file:
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setLevel(logging.WARNING)
                logger.addHandler(file_handler)
            
            # 设置格式
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    def handle_system_prompt_error(self, error: Exception, fallback_prompt: str = None) -> str:
        """
        处理系统提示文件错误
        
        Args:
            error: 错误对象
            fallback_prompt: 备用系统提示
            
        Returns:
            可用的系统提示内容
        """
        error_msg = f"系统提示文件错误: {str(error)}"
        self.logger.error(error_msg)
        
        if isinstance(error, FileNotFoundError):
            user_msg = "❌ 系统提示文件不存在，请检查文件路径配置"
        elif isinstance(error, PermissionError):
            user_msg = "❌ 无权限读取系统提示文件，请检查文件权限"
        elif isinstance(error, UnicodeDecodeError):
            user_msg = "❌ 系统提示文件编码错误，请使用UTF-8编码"
        else:
            user_msg = f"❌ 系统提示文件读取失败: {str(error)}"
        
        print(user_msg)
        
        # 返回备用提示或默认提示
        if fallback_prompt:
            self.logger.info("使用备用系统提示")
            return fallback_prompt
        
        # 最基础的默认系统提示
        default_prompt = """
        <system_prompt>
          <Your_info>
          你是一个智能助手，可以帮助用户处理各种问题。
          </Your_info>
          
          <current_time>2025-01-01 00:00 周一</current_time>
        </system_prompt>
        """
        self.logger.warning("使用默认系统提示")
        return default_prompt.strip()
    
    def handle_api_error(self, error: Exception) -> str:
        """
        处理API调用错误
        
        Args:
            error: API错误
            
        Returns:
            用户友好的错误消息
        """
        error_msg = f"API调用错误: {str(error)}"
        self.logger.error(error_msg)
        
        # 根据错误类型返回不同的用户消息
        if "api_key" in str(error).lower():
            return "❌ API密钥配置错误，请检查ANTHROPIC_API_KEY环境变量"
        elif "rate_limit" in str(error).lower():
            return "❌ API调用频率超限，请稍后再试"
        elif "timeout" in str(error).lower():
            return "❌ API调用超时，请检查网络连接"
        elif "connection" in str(error).lower():
            return "❌ 网络连接错误，请检查网络设置"
        else:
            return f"❌ AI服务调用失败: {str(error)}"
    
    def handle_function_error(self, function_name: str, error: Exception, 
                            parameters: Dict[str, Any] = None) -> str:
        """
        处理函数调用错误
        
        Args:
            function_name: 函数名
            error: 错误对象
            parameters: 函数参数
            
        Returns:
            错误描述
        """
        error_msg = f"函数调用错误 {function_name}: {str(error)}"
        if parameters:
            error_msg += f", 参数: {parameters}"
        
        self.logger.error(error_msg)
        self.logger.debug(traceback.format_exc())
        
        return f"函数 {function_name} 执行失败: {str(error)}"
    
    def handle_general_error(self, context: str, error: Exception, 
                           critical: bool = False) -> Optional[str]:
        """
        处理通用错误
        
        Args:
            context: 错误发生的上下文
            error: 错误对象
            critical: 是否为关键错误
            
        Returns:
            用户消息（如果需要显示给用户）
        """
        error_msg = f"{context}: {str(error)}"
        
        if critical:
            self.logger.critical(error_msg)
            self.logger.critical(traceback.format_exc())
            return f"❌ 系统发生严重错误: {str(error)}"
        else:
            self.logger.error(error_msg)
            self.logger.debug(traceback.format_exc())
            return None  # 不显示给用户
    
    def safe_execute(self, func, *args, context: str = "操作", **kwargs):
        """
        安全执行函数，自动处理异常
        
        Args:
            func: 要执行的函数
            *args: 函数参数
            context: 操作上下文描述
            **kwargs: 函数关键字参数
            
        Returns:
            (success: bool, result_or_error: Any)
        """
        try:
            result = func(*args, **kwargs)
            return True, result
        except Exception as e:
            error_msg = self.handle_general_error(context, e)
            return False, error_msg or str(e)


# 创建全局错误处理器实例
error_handler = ErrorHandler()