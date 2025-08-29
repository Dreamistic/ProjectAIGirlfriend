import time
from typing import Tuple


def get_current_time_string() -> str:
    """获取格式化的当前时间字符串，包含星期几的中文显示"""
    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    current_time = time.strftime("%Y-%m-%d %H:%M")
    weekday = weekday_names[time.localtime().tm_wday]
    return f"{current_time} {weekday}"


def get_time_components() -> Tuple[str, str]:
    """获取时间组件，返回(时间字符串, 星期几)"""
    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    current_time = time.strftime("%Y-%m-%d %H:%M")
    weekday = weekday_names[time.localtime().tm_wday]
    return current_time, weekday