
"""
25.8.18

{
Todo对象结构 - 扩展版（可执行TODO系统）

  "id": "unique-string",
  "content": "任务描述",
  "status": "pending|in_progress|completed",
  "priority": "high|medium|low",
  "progress": 0,                 // 0-100进度百分比
  "activeForm": "正在执行任务",   // 执行时的描述
  "subtasks": [                  // 子任务列表
    {"id": "1-1", "content": "子任务1", "completed": false},
    {"id": "1-2", "content": "子任务2", "completed": true}
  ],
  "created_at": "2025-08-28 00:17",
  "started_at": null,            // 开始执行时间
  "completed_at": null,          // 完成时间
  "execution_log": []            // 执行历史记录
}
"""

TODO_HIGH = "high"
TODO_MEDIUM = "medium"
TODO_LOW = "low"

class TodoList:
    def __init__(self):
        self.todos = []

    def add(self, content, priority = "medium"):
        from datetime import datetime
        todo = {
            # id从1开始，依次增加
            "id": len(self.todos) + 1,
            "content": content,
            "status": "pending",
            "priority": priority,
            "progress": 0,
            "activeForm": f"正在{content}",
            "subtasks": [],
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "started_at": None,
            "completed_at": None,
            "execution_log": []
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
        """
        批量更新todo列表
        
        Args:
            todos_data: list of dict, 格式:
            [
                {"content": "任务描述", "status": "pending|in_progress|completed", "priority": "high|medium|low"},
                ...
            ]
        """
        # 清空现有todos
        self.todos.clear()
        
        # 批量添加新的todos
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
    
    # ===== 可执行TODO系统扩展方法 =====
    
    def start_todo(self, todo_id):
        """开始执行任务（同时只能有一个任务处于进行中状态）"""
        from datetime import datetime
        
        # 检查是否已有进行中的任务
        active_tasks = [t for t in self.todos if t["status"] == "in_progress"]
        if active_tasks:
            return None  # 已有进行中的任务，不能开始新任务
        
        for todo in self.todos:
            if todo["id"] == todo_id:
                todo["status"] = "in_progress"
                todo["started_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.log_execution(todo_id, "started", f"开始执行任务: {todo['content']}")
                return todo
        return None
    
    def break_down_task(self, todo_id, subtasks_list):
        """分解任务为子任务"""
        for todo in self.todos:
            if todo["id"] == todo_id:
                subtasks = []
                for i, subtask_content in enumerate(subtasks_list, 1):
                    subtasks.append({
                        "id": f"{todo_id}-{i}",
                        "content": subtask_content,
                        "completed": False
                    })
                todo["subtasks"] = subtasks
                self.log_execution(todo_id, "breakdown", f"任务分解为{len(subtasks)}个子任务")
                return todo
        return None
    
    def update_progress(self, todo_id, progress):
        """更新任务进度"""
        for todo in self.todos:
            if todo["id"] == todo_id:
                old_progress = todo["progress"]
                todo["progress"] = max(0, min(100, progress))  # 确保在0-100范围内
                self.log_execution(todo_id, "progress", f"进度更新: {old_progress}% -> {progress}%")
                
                # 如果进度达到100%，自动标记为完成
                if progress >= 100:
                    self.complete_todo(todo_id)
                
                return todo
        return None
    
    def complete_subtask(self, todo_id, subtask_id):
        """完成子任务"""
        for todo in self.todos:
            if todo["id"] == todo_id:
                for subtask in todo["subtasks"]:
                    if subtask["id"] == subtask_id:
                        subtask["completed"] = True
                        self.log_execution(todo_id, "subtask_completed", f"完成子任务: {subtask['content']}")
                        
                        # 计算整体进度
                        completed_count = sum(1 for st in todo["subtasks"] if st["completed"])
                        total_count = len(todo["subtasks"])
                        if total_count > 0:
                            progress = int((completed_count / total_count) * 100)
                            todo["progress"] = progress
                            
                            # 如果所有子任务都完成，标记主任务为完成
                            if completed_count == total_count:
                                self.complete_todo(todo_id)
                        
                        return todo
        return None
    
    def complete_todo(self, todo_id):
        """完成任务"""
        from datetime import datetime
        for todo in self.todos:
            if todo["id"] == todo_id:
                todo["status"] = "completed"
                todo["progress"] = 100
                todo["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.log_execution(todo_id, "completed", f"任务完成: {todo['content']}")
                return todo
        return None
    
    def get_active_todos(self):
        """获取正在执行的任务"""
        return [todo for todo in self.todos if todo["status"] == "in_progress"]
    
    def get_pending_todos(self):
        """获取待处理的任务"""
        return [todo for todo in self.todos if todo["status"] == "pending"]
    
    def log_execution(self, todo_id, action, description):
        """记录执行历史"""
        from datetime import datetime
        for todo in self.todos:
            if todo["id"] == todo_id:
                log_entry = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "action": action,
                    "description": description
                }
                todo["execution_log"].append(log_entry)
                return True
        return False
    
    def get_todo_progress_summary(self):
        """获取所有任务的进度摘要"""
        active_todos = self.get_active_todos()
        if not active_todos:
            return "当前没有正在进行的任务"
        
        summary = "📋 正在进行的任务:\n"
        for todo in active_todos:
            progress_bar = "█" * (todo["progress"] // 10) + "░" * (10 - todo["progress"] // 10)
            summary += f"🔄 {todo['content']}\n"
            summary += f"   进度: [{progress_bar}] {todo['progress']}%\n"
            
            if todo["subtasks"]:
                completed_subtasks = [st for st in todo["subtasks"] if st["completed"]]
                summary += f"   子任务: {len(completed_subtasks)}/{len(todo['subtasks'])} 已完成\n"
            
            summary += "\n"
        
        return summary.strip()

if __name__ == "__main__":
    todo_list = TodoList()
    
    # 传统方式添加
    todo_list.add("完成项目")
    todo_list.add("学习Python", TODO_HIGH)
    todo_list.add("锻炼身体", TODO_LOW)
    print("传统添加:", todo_list.todos)
    print()
    
    # 批量更新todo列表（类似TodoWrite工具）
    batch_todos = [
        {"content": "开发AI女友功能", "status": "in_progress", "priority": "high"},
        {"content": "完善记忆系统", "status": "pending", "priority": "high"},
        {"content": "优化对话体验", "status": "pending", "priority": "medium"},
        {"content": "添加情感模块", "status": "pending", "priority": "low"}
    ]
    
    todo_list.update_all(batch_todos)
    print("批量更新后:", todo_list.get_all())
    print()
    
    # 状态筛选
    print("进行中的任务:", todo_list.get_by_status("in_progress"))
    print("待完成的任务:", todo_list.get_by_status("pending"))
