from core.function_registry import function_registry
from functions.todo_functions import (
    add_todo, 
    update_todo_status, 
    get_all_todos,
    get_todos_by_status, 
    delete_todo, 
    modify_todo, 
    batch_update_todos
)
from functions.ai_task_functions import (
    my_add_task,
    my_start_task,
    my_break_down_task,
    my_update_progress,
    my_complete_subtask,
    my_current_tasks,
    my_task_summary,
    my_task_history,
    my_all_tasks,
    my_get_subtask_ids
)


def register_all_functions():
    """注册所有功能函数"""
    
    # Todo管理功能
    function_registry.register(
        "add_todo",
        add_todo,
        "添加新的待办事项",
        {
            "content": {
                "type": "string",
                "description": "待办事项内容"
            },
            "priority": {
                "type": "string", 
                "description": "优先级: high/medium/low",
                "options": [
                    {
                        "value": "high",
                        "description": "高优先级",
                        "usage": "重要紧急的任务"
                    },
                    {
                        "value": "medium", 
                        "description": "中等优先级",
                        "usage": "普通日常任务"
                    },
                    {
                        "value": "low",
                        "description": "低优先级", 
                        "usage": "可以延后的任务"
                    }
                ]
            }
        },
        ["content"]
    )
    
    function_registry.register(
        "update_todo_status",
        update_todo_status,
        "更新待办事项的状态",
        {
            "todo_id": {
                "type": "string",
                "description": "任务ID"
            },
            "status": {
                "type": "string",
                "description": "新状态: pending/in_progress/completed",
                "options": [
                    {
                        "value": "pending",
                        "description": "待处理",
                        "usage": "尚未开始的任务"
                    },
                    {
                        "value": "in_progress", 
                        "description": "进行中",
                        "usage": "正在执行的任务"
                    },
                    {
                        "value": "completed",
                        "description": "已完成",
                        "usage": "已经完成的任务"
                    }
                ]
            }
        },
        ["todo_id", "status"]
    )
    
    function_registry.register(
        "get_all_todos",
        get_all_todos,
        "获取所有待办事项列表",
        {},
        []
    )
    
    function_registry.register(
        "get_todos_by_status",
        get_todos_by_status,
        "根据状态筛选待办事项",
        {
            "status": {
                "type": "string",
                "description": "要筛选的状态: pending/in_progress/completed",
                "options": [
                    {"value": "pending", "description": "待处理的任务"},
                    {"value": "in_progress", "description": "进行中的任务"},
                    {"value": "completed", "description": "已完成的任务"}
                ]
            }
        },
        ["status"]
    )
    
    function_registry.register(
        "delete_todo",
        delete_todo,
        "删除指定的待办事项",
        {
            "todo_id": {
                "type": "string",
                "description": "要删除的任务ID"
            }
        },
        ["todo_id"]
    )
    
    function_registry.register(
        "modify_todo", 
        modify_todo,
        "修改待办事项的内容和优先级",
        {
            "todo_id": {
                "type": "string",
                "description": "要修改的任务ID"
            },
            "content": {
                "type": "string",
                "description": "新的任务内容"
            },
            "priority": {
                "type": "string",
                "description": "新的优先级: high/medium/low"
            }
        },
        ["todo_id", "content"]
    )
    
    function_registry.register(
        "batch_update_todos",
        batch_update_todos,
        "批量更新待办事项列表",
        {
            "todos_json": {
                "type": "string",
                "description": "JSON格式的任务数组，格式: [{'content': '任务内容', 'status': 'pending', 'priority': 'medium'}, ...]"
            }
        },
        ["todos_json"]
    )
    
    # 林晚晴的AI任务管理系统
    function_registry.register(
        "my_add_task",
        my_add_task,
        "我（林晚晴）接受新任务",
        {
            "content": {
                "type": "string",
                "description": "主人分配给我的任务内容"
            },
            "priority": {
                "type": "string",
                "description": "任务优先级: high/medium/low",
                "options": [
                    {"value": "high", "description": "高优先级任务"},
                    {"value": "medium", "description": "中等优先级任务"},
                    {"value": "low", "description": "低优先级任务"}
                ]
            }
        },
        ["content"]
    )
    
    function_registry.register(
        "my_start_task",
        my_start_task,
        "我开始执行某项任务",
        {
            "task_id": {
                "type": "string",
                "description": "要开始执行的任务ID"
            }
        },
        ["task_id"]
    )
    
    function_registry.register(
        "my_break_down_task",
        my_break_down_task,
        "我将任务分解为具体步骤",
        {
            "task_id": {
                "type": "string",
                "description": "要分解的任务ID"
            },
            "subtasks_json": {
                "type": "string",
                "description": "JSON格式的子任务数组，格式: ['子任务1', '子任务2', ...]"
            }
        },
        ["task_id", "subtasks_json"]
    )
    
    function_registry.register(
        "my_update_progress",
        my_update_progress,
        "我更新任务执行进度",
        {
            "task_id": {
                "type": "string",
                "description": "任务ID"
            },
            "progress": {
                "type": "string",
                "description": "进度百分比(0-100)"
            }
        },
        ["task_id", "progress"]
    )
    
    function_registry.register(
        "my_complete_subtask",
        my_complete_subtask,
        "我完成一个子任务步骤。子任务ID格式：{主任务ID}-{序号}，如任务1的第1个子任务ID为'1-1'",
        {
            "task_id": {
                "type": "string",
                "description": "主任务ID"
            },
            "subtask_id": {
                "type": "string",
                "description": "要完成的子任务ID（格式：主任务ID-序号，例如 '1-1', '1-2'）。可以用 my_current_tasks 或 my_get_subtask_ids 查看具体ID"
            }
        },
        ["task_id", "subtask_id"]
    )
    
    function_registry.register(
        "my_current_tasks",
        my_current_tasks,
        "查看我当前正在执行的任务",
        {},
        []
    )
    
    function_registry.register(
        "my_task_summary",
        my_task_summary,
        "我的任务执行摘要",
        {},
        []
    )
    
    function_registry.register(
        "my_task_history",
        my_task_history,
        "查看我某个任务的执行历史",
        {
            "task_id": {
                "type": "string",
                "description": "任务ID"
            }
        },
        ["task_id"]
    )
    
    function_registry.register(
        "my_all_tasks",
        my_all_tasks,
        "查看我的所有任务",
        {},
        []
    )
    
    function_registry.register(
        "my_get_subtask_ids",
        my_get_subtask_ids,
        "获取指定任务的所有子任务ID列表，方便完成子任务时使用",
        {
            "task_id": {
                "type": "string",
                "description": "要查询子任务ID的主任务ID"
            }
        },
        ["task_id"]
    )


# 自动注册所有函数
register_all_functions()