import json
from todo_system import TodoList
from config.settings import FUNCTION_SUCCESS_MESSAGE


# 创建全局Todo实例
todo_list = TodoList()


def add_todo(content: str, priority: str = "medium") -> str:
    """添加新的待办事项"""
    todo = todo_list.add(content, priority)
    return f"成功添加待办事项: {content} (ID: {todo['id']}, 优先级: {priority})"


def update_todo_status(todo_id: str, status: str) -> str:
    """更新待办事项状态"""
    try:
        todo_id = int(todo_id)
    except ValueError:
        return "错误: 任务ID必须是数字"
    
    if status not in ["pending", "in_progress", "completed"]:
        return "错误: 状态必须是 pending, in_progress, 或 completed"
    
    updated_todo = todo_list.update_status(todo_id, status)
    if updated_todo:
        return f"成功更新任务状态: {updated_todo['content']} -> {status}"
    else:
        return f"错误: 找不到ID为 {todo_id} 的任务"


def get_all_todos() -> str:
    """获取所有待办事项"""
    todos = todo_list.get_all()
    if not todos:
        return "当前没有任何待办事项"
    
    result = "所有待办事项:\n"
    for todo in todos:
        status_emoji = {
            "pending": "⏳",
            "in_progress": "🔄", 
            "completed": "✅"
        }.get(todo["status"], "❓")
        
        priority_emoji = {
            "high": "🔴",
            "medium": "🟡",
            "low": "🟢"
        }.get(todo["priority"], "⚪")
        
        result += f"{status_emoji} {priority_emoji} ID:{todo['id']} - {todo['content']}\n"
    
    return result.strip()


def get_todos_by_status(status: str) -> str:
    """根据状态获取待办事项"""
    if status not in ["pending", "in_progress", "completed"]:
        return "错误: 状态必须是 pending, in_progress, 或 completed"
    
    todos = todo_list.get_by_status(status)
    if not todos:
        status_names = {
            "pending": "待处理",
            "in_progress": "进行中", 
            "completed": "已完成"
        }
        return f"当前没有{status_names[status]}的任务"
    
    status_emoji = {
        "pending": "⏳",
        "in_progress": "🔄", 
        "completed": "✅"
    }[status]
    
    result = f"{status_emoji} {['待处理', '进行中', '已完成'][['pending', 'in_progress', 'completed'].index(status)]}的任务:\n"
    for todo in todos:
        priority_emoji = {
            "high": "🔴",
            "medium": "🟡", 
            "low": "🟢"
        }.get(todo["priority"], "⚪")
        
        result += f"{priority_emoji} ID:{todo['id']} - {todo['content']}\n"
    
    return result.strip()


def delete_todo(todo_id: str) -> str:
    """删除待办事项"""
    try:
        todo_id = int(todo_id)
    except ValueError:
        return "错误: 任务ID必须是数字"
    
    deleted_todo = todo_list.delete(todo_id)
    if deleted_todo:
        return f"成功删除任务: {deleted_todo['content']}"
    else:
        return f"错误: 找不到ID为 {todo_id} 的任务"


def modify_todo(todo_id: str, content: str, priority: str = "medium") -> str:
    """修改待办事项"""
    try:
        todo_id = int(todo_id)
    except ValueError:
        return "错误: 任务ID必须是数字"
    
    if priority not in ["high", "medium", "low"]:
        return "错误: 优先级必须是 high, medium, 或 low"
    
    updated_todo = todo_list.modify(todo_id, content, priority)
    if updated_todo:
        return f"成功修改任务: ID:{todo_id} -> {content} (优先级: {priority})"
    else:
        return f"错误: 找不到ID为 {todo_id} 的任务"


def batch_update_todos(todos_json: str) -> str:
    """批量更新待办事项列表"""
    try:
        todos_data = json.loads(todos_json) if isinstance(todos_json, str) else todos_json
        
        if not isinstance(todos_data, list):
            return "错误: 输入必须是任务数组"
        
        # 验证数据格式
        for i, todo_data in enumerate(todos_data):
            if not isinstance(todo_data, dict):
                return f"错误: 第{i+1}个任务不是有效的对象"
            if "content" not in todo_data:
                return f"错误: 第{i+1}个任务缺少content字段"
        
        updated_todos = todo_list.update_all(todos_data)
        return f"成功批量更新 {len(updated_todos)} 个待办事项"
        
    except json.JSONDecodeError:
        return "错误: JSON格式不正确"
    except Exception as e:
        return f"错误: {str(e)}"


# ===== 可执行TODO系统扩展函数 =====

def start_todo(todo_id: str) -> str:
    """开始执行任务"""
    try:
        todo_id = int(todo_id)
    except ValueError:
        return "错误: 任务ID必须是数字"
    
    started_todo = todo_list.start_todo(todo_id)
    if started_todo:
        return f"✅ 开始执行任务: {started_todo['content']}\n📋 {started_todo['activeForm']}"
    else:
        return f"错误: 找不到ID为 {todo_id} 的任务"


def break_down_task(todo_id: str, subtasks_json: str) -> str:
    """分解任务为子任务"""
    try:
        todo_id = int(todo_id)
    except ValueError:
        return "错误: 任务ID必须是数字"
    
    try:
        subtasks_list = json.loads(subtasks_json) if isinstance(subtasks_json, str) else subtasks_json
        
        if not isinstance(subtasks_list, list):
            return "错误: 子任务必须是数组格式"
        
        updated_todo = todo_list.break_down_task(todo_id, subtasks_list)
        if updated_todo:
            result = f"🎯 成功分解任务: {updated_todo['content']}\n"
            result += f"📝 分解为 {len(subtasks_list)} 个子任务:\n"
            for i, subtask in enumerate(updated_todo['subtasks'], 1):
                result += f"  {i}. {subtask['content']}\n"
            return result.strip()
        else:
            return f"错误: 找不到ID为 {todo_id} 的任务"
    
    except json.JSONDecodeError:
        return "错误: 子任务JSON格式不正确"
    except Exception as e:
        return f"错误: {str(e)}"


def update_todo_progress(todo_id: str, progress: str) -> str:
    """更新任务进度"""
    try:
        todo_id = int(todo_id)
        progress = int(progress)
    except ValueError:
        return "错误: 任务ID和进度必须是数字"
    
    if progress < 0 or progress > 100:
        return "错误: 进度必须在0-100之间"
    
    updated_todo = todo_list.update_progress(todo_id, progress)
    if updated_todo:
        progress_bar = "█" * (progress // 10) + "░" * (10 - progress // 10)
        result = f"📈 进度更新: {updated_todo['content']}\n"
        result += f"[{progress_bar}] {progress}%"
        
        if progress >= 100:
            result += "\n🎉 任务已完成！"
        
        return result
    else:
        return f"错误: 找不到ID为 {todo_id} 的任务"


def complete_subtask(todo_id: str, subtask_id: str) -> str:
    """完成子任务"""
    try:
        todo_id = int(todo_id)
    except ValueError:
        return "错误: 任务ID必须是数字"
    
    updated_todo = todo_list.complete_subtask(todo_id, subtask_id)
    if updated_todo:
        # 找到完成的子任务
        completed_subtask = None
        for subtask in updated_todo['subtasks']:
            if subtask['id'] == subtask_id:
                completed_subtask = subtask
                break
        
        result = f"✅ 完成子任务: {completed_subtask['content']}\n"
        
        # 显示整体进度
        completed_count = sum(1 for st in updated_todo['subtasks'] if st['completed'])
        total_count = len(updated_todo['subtasks'])
        progress_bar = "█" * (updated_todo['progress'] // 10) + "░" * (10 - updated_todo['progress'] // 10)
        
        result += f"📊 整体进度: [{progress_bar}] {updated_todo['progress']}%\n"
        result += f"🎯 子任务进度: {completed_count}/{total_count} 已完成"
        
        if updated_todo['status'] == 'completed':
            result += "\n🎉 所有子任务完成，主任务已完成！"
        
        return result
    else:
        return f"错误: 找不到ID为 {todo_id} 的任务或子任务 {subtask_id}"


def get_active_todos() -> str:
    """获取正在执行的任务"""
    active_todos = todo_list.get_active_todos()
    if not active_todos:
        return "📝 当前没有正在执行的任务"
    
    result = f"🔄 正在执行的任务 ({len(active_todos)}个):\n"
    for todo in active_todos:
        progress_bar = "█" * (todo['progress'] // 10) + "░" * (10 - todo['progress'] // 10)
        result += f"\n📋 ID:{todo['id']} - {todo['content']}\n"
        result += f"   进度: [{progress_bar}] {todo['progress']}%\n"
        
        if todo['subtasks']:
            completed_count = sum(1 for st in todo['subtasks'] if st['completed'])
            result += f"   子任务: {completed_count}/{len(todo['subtasks'])} 已完成\n"
            
            # 显示未完成的子任务
            pending_subtasks = [st for st in todo['subtasks'] if not st['completed']]
            if pending_subtasks:
                result += f"   📌 待完成子任务:\n"
                for subtask in pending_subtasks[:3]:  # 只显示前3个
                    result += f"     • {subtask['content']}\n"
                if len(pending_subtasks) > 3:
                    result += f"     ... 还有{len(pending_subtasks)-3}个\n"
    
    return result.strip()


def get_todo_progress_summary() -> str:
    """获取任务进度摘要"""
    return todo_list.get_todo_progress_summary()


def get_todo_execution_log(todo_id: str) -> str:
    """获取任务执行历史"""
    try:
        todo_id = int(todo_id)
    except ValueError:
        return "错误: 任务ID必须是数字"
    
    for todo in todo_list.todos:
        if todo["id"] == todo_id:
            if not todo['execution_log']:
                return f"📋 任务 '{todo['content']}' 还没有执行历史"
            
            result = f"📝 任务执行历史: {todo['content']}\n"
            for log_entry in todo['execution_log']:
                timestamp = log_entry['timestamp']
                action_emoji = {
                    "started": "▶️",
                    "progress": "📈",
                    "breakdown": "🎯",
                    "subtask_completed": "✅",
                    "completed": "🎉"
                }.get(log_entry['action'], "📝")
                
                result += f"{action_emoji} {timestamp}: {log_entry['description']}\n"
            
            return result.strip()
    
    return f"错误: 找不到ID为 {todo_id} 的任务"


