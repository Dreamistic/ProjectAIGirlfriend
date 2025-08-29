#!/usr/bin/env python3
"""
测试批量todo功能
"""

from function_core import ModernFunctionRegistry, SmartParameterParser
from todo_system import TodoList

def test_smart_parameter_parser():
    """测试智能参数解析"""
    print("=== 测试智能参数解析 ===")
    
    # 测试JSON解析
    json_str = '[{"content":"任务1","priority":"high"},{"content":"任务2","status":"completed"}]'
    parsed = SmartParameterParser.parse_value(json_str)
    print(f"JSON解析结果: {type(parsed)} - {parsed}")
    
    # 测试数字解析
    number_str = "123"
    parsed_num = SmartParameterParser.parse_value(number_str)
    print(f"数字解析结果: {type(parsed_num)} - {parsed_num}")
    
    # 测试布尔值解析
    bool_str = "true"
    parsed_bool = SmartParameterParser.parse_value(bool_str)
    print(f"布尔值解析结果: {type(parsed_bool)} - {parsed_bool}")
    print()

def batch_update_todos(todos_data):
    """批量更新todo的测试函数"""
    todo_list = TodoList()
    
    # 如果是字符串（JSON），先解析
    if isinstance(todos_data, str):
        import json
        todos_data = json.loads(todos_data)
    
    # 批量更新
    result = todo_list.update_all(todos_data)
    print(f"批量更新了 {len(result)} 个todo:")
    for todo in result:
        print(f"  - ID:{todo['id']} [{todo['status']}] {todo['content']} (优先级:{todo['priority']})")
    
    return f"成功更新了{len(result)}个todo"

def test_batch_function():
    """测试批量函数调用"""
    print("=== 测试批量函数调用 ===")
    
    # 创建注册器
    registry = ModernFunctionRegistry()
    
    # 注册批量更新函数
    registry.register(
        "batch_update_todos",
        batch_update_todos,
        "批量更新todo列表",
        {
            "todos_data": {
                "type": "array",
                "description": "todo数据列表，JSON格式"
            }
        }
    )
    
    # 模拟XML函数调用
    test_xml = """
    <function_calls>
      <invoke name="batch_update_todos">
        <parameter name="todos_data">[
          {"content": "开发AI女友记忆系统", "status": "in_progress", "priority": "high"},
          {"content": "完善函数调用机制", "status": "completed", "priority": "high"},
          {"content": "优化流式对话体验", "status": "pending", "priority": "medium"},
          {"content": "添加情感状态模块", "status": "pending", "priority": "low"}
        ]</parameter>
      </invoke>
    </function_calls>
    """
    
    # 解析并执行
    results = registry.parse_and_execute(test_xml)
    
    print(f"执行结果: {len(results)} 个函数调用")
    for result in results:
        if result.success:
            print(f"✅ {result.function_name}: {result.content}")
        else:
            print(f"❌ {result.function_name}: {result.error}")
    
    # 测试格式化输出
    formatted = registry.format_results(results)
    print(f"\n格式化输出: {formatted}")
    print()

def test_multiple_invokes():
    """测试单次调用中的多个invoke"""
    print("=== 测试多个invoke调用 ===")
    
    registry = ModernFunctionRegistry()
    registry.register("batch_update_todos", batch_update_todos, "批量更新todo")
    
    # 单个function_calls中多个invoke
    multi_xml = """
    <function_calls>
      <invoke name="batch_update_todos">
        <parameter name="todos_data">[{"content": "第一批任务", "priority": "high"}]</parameter>
      </invoke>
      <invoke name="batch_update_todos">
        <parameter name="todos_data">[{"content": "第二批任务", "priority": "medium"}]</parameter>
      </invoke>
    </function_calls>
    """
    
    results = registry.parse_and_execute(multi_xml)
    print(f"多invoke执行结果: {len(results)} 个函数调用")
    for i, result in enumerate(results, 1):
        print(f"调用{i}: {result.content}")
    print()

if __name__ == "__main__":
    print("开始测试批量todo功能...\n")
    
    # 运行所有测试
    test_smart_parameter_parser()
    test_batch_function()
    test_multiple_invokes()
    
    print("测试完成！")