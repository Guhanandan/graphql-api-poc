import base64
import json
from typing import Optional

def encode_cursor(offset: int) -> str:
    """Encode offset as base64 cursor"""
    cursor_data = {"offset": offset}
    cursor_json = json.dumps(cursor_data)
    return base64.b64encode(cursor_json.encode()).decode()

def decode_cursor(cursor: str) -> int:
    """Decode base64 cursor to offset"""
    try:
        cursor_json = base64.b64decode(cursor.encode()).decode()
        cursor_data = json.loads(cursor_json)
        return cursor_data.get("offset", 0)
    except Exception:
        return 0