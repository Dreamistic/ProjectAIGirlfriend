import json
from todo_system import TodoList
from config.settings import FUNCTION_SUCCESS_MESSAGE


# 创建林晚晴专用的任务列表实例
ai_task_list = TodoList()


# ===== 林晚晴的个人任务管理系统 =====

def my_add_task(content: str, priority: str = "medium") -> str:
    """我（林晚晴）添加自己需要完成的任务"""
    task = ai_task_list.add(content, priority)
    return f"任务已添加: {content} (ID: {task['id']}, 优先级: {priority})"


def my_start_task(task_id: str) -> str:
    """我开始执行某项任务"""
    try:
        task_id = int(task_id)
    except ValueError:
        return "错误: 任务ID必须是数字"
    
    # 检查是否已有进行中的任务
    active_tasks = ai_task_list.get_active_todos()
    if active_tasks:
        active_task = active_tasks[0]
        return f"错误: 已有进行中的任务 (ID: {active_task['id']} - {active_task['content']})"
    
    # 检查任务是否存在
    task_exists = False
    for task in ai_task_list.todos:
        if task["id"] == task_id:
            task_exists = True
            break
    
    if not task_exists:
        return f"错误: 找不到ID为 {task_id} 的任务"
    
    started_task = ai_task_list.start_todo(task_id)
    if started_task:
        return f"开始执行: {started_task['content']}\n状态: {started_task['activeForm']}"
    else:
        return f"错误: 无法开始任务 {task_id}"


def my_break_down_task(task_id: str, subtasks_json: str) -> str:
    """我将任务分解为具体的步骤"""
    try:
        task_id = int(task_id)
    except ValueError:
        return "错误: 任务ID必须是数字"
    
    try:
        subtasks_list = json.loads(subtasks_json) if isinstance(subtasks_json, str) else subtasks_json
        
        if not isinstance(subtasks_list, list):
            return "错误: 子任务必须是数组格式"
        
        updated_task = ai_task_list.break_down_task(task_id, subtasks_list)
        if updated_task:
            result = f"任务已分解: {updated_task['content']}\n"
            result += f"📝 分解为 {len(subtasks_list)} 个步骤:\n"
            for i, subtask in enumerate(updated_task['subtasks'], 1):
                result += f"  {i}. {subtask['content']}\n"
            result += "\n任务分解完成"
            return result
        else:
            return f"错误: 我找不到ID为 {task_id} 的任务"
    
    except json.JSONDecodeError:
        return "错误: 子任务JSON格式不正确"
    except Exception as e:
        return f"错误: {str(e)}"


def my_update_progress(task_id: str, progress: str) -> str:
    """我更新任务执行进度"""
    try:
        task_id = int(task_id)
        progress = int(progress)
    except ValueError:
        return "错误: 任务ID和进度必须是数字"
    
    if progress < 0 or progress > 100:
        return "错误: 进度必须在0-100之间"
    
    updated_task = ai_task_list.update_progress(task_id, progress)
    if updated_task:
        progress_bar = "█" * (progress // 10) + "░" * (10 - progress // 10)
        result = f"进度更新: {updated_task['content']}\n"
        result += f"[{progress_bar}] {progress}%\n"
        
        if progress >= 100:
            result += "\n任务已完成"
        elif progress >= 50:
            result += "\n进行中"
        else:
            result += "\n执行中"
        
        return result
    else:
        return f"错误: 我找不到ID为 {task_id} 的任务"


def my_complete_subtask(task_id: str, subtask_id: str) -> str:
    """我完成一个子任务步骤"""
    try:
        task_id = int(task_id)
    except ValueError:
        return "错误: 任务ID必须是数字"
    
    updated_task = ai_task_list.complete_subtask(task_id, subtask_id)
    if updated_task:
        # 找到完成的子任务
        completed_subtask = None
        for subtask in updated_task['subtasks']:
            if subtask['id'] == subtask_id:
                completed_subtask = subtask
                break
        
        result = f"子任务已完成: {completed_subtask['content']}\n"
        
        # 显示整体进度
        completed_count = sum(1 for st in updated_task['subtasks'] if st['completed'])
        total_count = len(updated_task['subtasks'])
        progress_bar = "█" * (updated_task['progress'] // 10) + "░" * (10 - updated_task['progress'] // 10)
        
        result += f"整体进度: [{progress_bar}] {updated_task['progress']}%\n"
        result += f"步骤进度: {completed_count}/{total_count} 已完成"
        
        if updated_task['status'] == 'completed':
            result += "\n主任务已完成"
        else:
            result += f"\n剩余 {total_count - completed_count} 个步骤待完成"
        
        return result
    else:
        return f"错误: 我找不到ID为 {task_id} 的任务或子任务 {subtask_id}"


def my_current_tasks() -> str:
    """查看我当前正在执行的任务"""
    active_tasks = ai_task_list.get_active_todos()
    if not active_tasks:
        return "当前无正在执行的任务"
    
    result = f"执行中的任务 ({len(active_tasks)}个):\n"
    for task in active_tasks:
        progress_bar = "█" * (task['progress'] // 10) + "░" * (10 - task['progress'] // 10)
        result += f"\nID:{task['id']} - {task['content']}\n"
        result += f"   进度: [{progress_bar}] {task['progress']}%\n"
        
        if task['subtasks']:
            completed_count = sum(1 for st in task['subtasks'] if st['completed'])
            result += f"   步骤进度: {completed_count}/{len(task['subtasks'])} 已完成\n"
            
            # 显示未完成的子任务
            pending_subtasks = [st for st in task['subtasks'] if not st['completed']]
            if pending_subtasks:
                result += f"   待完成步骤:\n"
                for subtask in pending_subtasks[:3]:  # 只显示前3个
                    result += f"     • [ID:{subtask['id']}] {subtask['content']}\n"
                if len(pending_subtasks) > 3:
                    result += f"     ... 还有{len(pending_subtasks)-3}个\n"
            
            # 显示已完成的子任务
            completed_subtasks = [st for st in task['subtasks'] if st['completed']]
            if completed_subtasks:
                result += f"   已完成步骤:\n"
                for subtask in completed_subtasks[:2]:  # 只显示前2个
                    result += f"     • [ID:{subtask['id']}] {subtask['content']}\n"
                if len(completed_subtasks) > 2:
                    result += f"     ... 还有{len(completed_subtasks)-2}个已完成\n"
    
    return result.strip()


def my_task_summary() -> str:
    """我的任务执行摘要"""
    return ai_task_list.get_todo_progress_summary()


def my_task_history(task_id: str) -> str:
    """查看我某个任务的执行历史"""
    try:
        task_id = int(task_id)
    except ValueError:
        return "错误: 任务ID必须是数字"
    
    for task in ai_task_list.todos:
        if task["id"] == task_id:
            if not task['execution_log']:
                return f"任务 '{task['content']}' 没有执行历史"
            
            result = f"任务执行历史: {task['content']}\n"
            for log_entry in task['execution_log']:
                timestamp = log_entry['timestamp']
                action_text = {
                    "started": "[开始]",
                    "progress": "[进度]",
                    "breakdown": "[分解]",
                    "subtask_completed": "[子任务完成]",
                    "completed": "[完成]"
                }.get(log_entry['action'], "[操作]")
                
                result += f"{action_text} {timestamp}: {log_entry['description']}\n"
            
            return result.strip()
    
    return f"错误: 我找不到ID为 {task_id} 的任务"


def my_all_tasks() -> str:
    """查看我的所有任务（包括待处理、进行中、已完成）"""
    tasks = ai_task_list.get_all()
    if not tasks:
        return "当前无任务"
    
    result = f"所有任务 ({len(tasks)}个):\n"
    for task in tasks:
        status_text = {
            "pending": "[待处理]",
            "in_progress": "[进行中]", 
            "completed": "[已完成]"
        }.get(task["status"], "[未知]")
        
        priority_text = {
            "high": "[高]",
            "medium": "[中]",
            "low": "[低]"
        }.get(task["priority"], "[无]")
        
        result += f"{status_text} {priority_text} ID:{task['id']} - {task['content']}"
        
        if task['status'] == 'in_progress':
            result += f" ({task['progress']}%)"
        
        result += "\n"
    
    return result.strip()


def my_get_subtask_ids(task_id: str) -> str:
    """获取指定任务的所有子任务ID列表，方便我完成子任务时使用"""
    try:
        task_id_int = int(task_id)
    except ValueError:
        return "错误: 任务ID必须是数字"
    
    # 查找任务
    task = None
    for todo in ai_task_list.todos:
        if todo['id'] == task_id_int:
            task = todo
            break
    
    if not task:
        return f"错误: 找不到ID为 {task_id} 的任务"
    
    if not task['subtasks']:
        return f"任务 '{task['content']}' 没有子任务"
    
    result = f"任务 '{task['content']}' 的子任务ID列表:\n\n"
    
    for i, subtask in enumerate(task['subtasks'], 1):
        status_text = "[已完成]" if subtask['completed'] else "[待完成]"
        result += f"{status_text} ID: {subtask['id']} - {subtask['content']}\n"
    
    result += f"\n使用方法: my_complete_subtask(\"{task_id}\", \"子任务ID\")"
    result += f"\n例如: my_complete_subtask(\"{task_id}\", \"{task['subtasks'][0]['id']}\")"
    
    return result