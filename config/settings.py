import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

AI_MODEL = "claude-sonnet-4-20250514"  # 手动修改为 claude-opus-4-1-20250805 用于正式使用
#AI_MODEL = "claude-opus-4-1-20250805"
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

SYSTEM_PROMPT_PATH = BASE_DIR / "config" / "system_prompt.xml"

MAX_CONVERSATION_DEPTH = 5

CHAT_CONFIG = {
    "max_tokens": 4086,
    "temperature": 0.7,
}

FUNCTION_SUCCESS_MESSAGE = "函数调用成功"