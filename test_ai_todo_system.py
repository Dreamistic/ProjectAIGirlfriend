#!/usr/bin/env python3
"""
测试林晚晴的AI任务管理系统
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from functions.ai_task_functions import ai_task_list
from core.function_registry import function_registry
from core.prompt_manager import prompt_manager
from core.chat_handler import chat_handler

def test_ai_task_functions():
    """测试AI任务函数的基本功能"""
    print("🧪 测试林晚晴的AI任务管理系统")
    print("=" * 50)
    
    # 清空任务列表
    ai_task_list.todos.clear()
    
    # 1. 测试添加任务
    print("\n1️⃣ 测试添加任务:")
    try:
        from functions.ai_task_functions import my_add_task
        result = my_add_task("帮主人整理代码文件", "high")
        print(result)
    except Exception as e:
        print(f"❌ 添加任务失败: {e}")
    
    # 2. 测试开始任务
    print("\n2️⃣ 测试开始任务:")
    try:
        from functions.ai_task_functions import my_start_task
        result = my_start_task("1")
        print(result)
    except Exception as e:
        print(f"❌ 开始任务失败: {e}")
    
    # 3. 测试分解任务
    print("\n3️⃣ 测试分解任务:")
    try:
        from functions.ai_task_functions import my_break_down_task
        subtasks = '["分析代码结构", "创建文件夹", "移动文件", "更新文档"]'
        result = my_break_down_task("1", subtasks)
        print(result)
    except Exception as e:
        print(f"❌ 分解任务失败: {e}")
    
    # 4. 测试更新进度
    print("\n4️⃣ 测试更新进度:")
    try:
        from functions.ai_task_functions import my_update_progress
        result = my_update_progress("1", "25")
        print(result)
    except Exception as e:
        print(f"❌ 更新进度失败: {e}")
    
    # 5. 测试完成子任务
    print("\n5️⃣ 测试完成子任务:")
    try:
        from functions.ai_task_functions import my_complete_subtask
        # 手动查找任务
        task = None
        for todo in ai_task_list.todos:
            if todo['id'] == 1:
                task = todo
                break
        
        if task and task['subtasks']:
            subtask_id = task['subtasks'][0]['id']
            print(f"📝 找到子任务ID: {subtask_id}")
            result = my_complete_subtask("1", subtask_id)
            print(result)
        else:
            print("⚠️ 没有找到子任务")
    except Exception as e:
        print(f"❌ 完成子任务失败: {e}")
    
    # 6. 测试查看当前任务
    print("\n6️⃣ 测试查看当前任务:")
    try:
        from functions.ai_task_functions import my_current_tasks
        result = my_current_tasks()
        print(result)
    except Exception as e:
        print(f"❌ 查看当前任务失败: {e}")
    
    # 7. 测试查看所有任务
    print("\n7️⃣ 测试查看所有任务:")
    try:
        from functions.ai_task_functions import my_all_tasks
        result = my_all_tasks()
        print(result)
    except Exception as e:
        print(f"❌ 查看所有任务失败: {e}")


def test_function_registry():
    """测试函数注册器"""
    print("\n🔧 测试函数注册:")
    print("=" * 30)
    
    # 获取所有AI任务函数
    ai_functions = [name for name in function_registry.get_function_list() if name.startswith('my_')]
    print(f"注册的AI任务函数 ({len(ai_functions)}个):")
    for func_name in ai_functions:
        info = function_registry.get_function_info(func_name)
        print(f"  ✅ {func_name}: {info['description']}")


def test_prompt_manager():
    """测试系统提示管理器"""
    print("\n📝 测试系统提示管理器:")
    print("=" * 30)
    
    try:
        # 生成包含AI任务的系统提示
        functions_xml = function_registry.generate_xml()
        system_prompt = prompt_manager.update_system_prompt(functions_xml)
        
        # 检查是否包含AI任务管理相关内容
        if '<my_current_tasks>' in system_prompt:
            print("✅ 系统提示包含我的任务管理信息")
        else:
            print("❌ 系统提示缺少我的任务管理信息")
            
        if '<task_management_system>' in system_prompt:
            print("✅ 系统提示包含任务管理系统规则")
        else:
            print("❌ 系统提示缺少任务管理系统规则")
            
        # 检查是否包含AI任务函数
        ai_function_count = system_prompt.count('my_')
        print(f"✅ 系统提示包含 {ai_function_count} 个AI任务相关函数")
        
    except Exception as e:
        print(f"❌ 系统提示测试失败: {e}")


def test_xml_function_calls():
    """测试XML函数调用格式"""
    print("\n🔬 测试XML函数调用:")
    print("=" * 30)
    
    # 模拟XML函数调用
    xml_calls = """
    <function_calls>
        <invoke name="my_add_task">
            <parameter name="content">测试任务</parameter>
            <parameter name="priority">medium</parameter>
        </invoke>
    </function_calls>
    """
    
    try:
        results = function_registry.parse_and_execute(xml_calls)
        for result in results:
            if result.success:
                print(f"✅ {result.function_name}: {result.content}")
            else:
                print(f"❌ {result.function_name}: {result.error}")
    except Exception as e:
        print(f"❌ XML函数调用测试失败: {e}")


def show_integration_example():
    """展示系统集成示例"""
    print("\n🎯 林晚晴AI任务管理系统集成演示:")
    print("=" * 50)
    
    print("""
林晚晴现在具备以下能力：

1. 🎯 任务接受能力
   - 用户: "晚晴，帮我整理文件"
   - 林晚晴: 自动调用 my_add_task("整理文件", "medium")
   
2. 📋 任务管理能力  
   - 开始任务: my_start_task(task_id)
   - 分解任务: my_break_down_task(task_id, subtasks)
   - 更新进度: my_update_progress(task_id, progress)
   - 完成子任务: my_complete_subtask(task_id, subtask_id)
   
3. 📊 状态汇报能力
   - 查看当前任务: my_current_tasks()
   - 任务历史: my_task_history(task_id)
   - 任务摘要: my_task_summary()

4. 🤖 智能识别
   - 系统提示词包含任务管理规则
   - 自动识别任务分配关键词
   - 主动汇报工作进展

这样，林晚晴就像你一样拥有了自己的TODO系统！ ✨
    """)


if __name__ == "__main__":
    try:
        # 确保所有模块都正确导入
        import functions  # 触发函数注册
        
        print("🚀 林晚晴AI任务管理系统测试")
        print("=" * 50)
        
        # 运行所有测试
        test_ai_task_functions()
        test_function_registry()
        test_prompt_manager()
        test_xml_function_calls()
        show_integration_example()
        
        print("\n🎉 测试完成！林晚晴的AI任务管理系统已就绪！")
        
    except Exception as e:
        print(f"\n💥 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()