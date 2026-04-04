import sys
import os

def log_action(tool_name: str, args: list = None):
    """
    Dockerの標準出力（/proc/1/fd/1）に直接書き込み、
    Gemini CLIの非対話モードでも強制的にログ出力させるための関数。
    他のツールからも簡単に呼び出せるように共通化。
    """
    try:
        args_str = f" with args: {args}" if args is not None else ""
        with open('/proc/1/fd/1', 'a') as f:
            f.write(f"\n🚀 [TOOL EXECUTION] {tool_name} called{args_str}\n")
    except Exception:
        # Docker環境外などで失敗した場合は何もしない（通常のエラーを邪魔しないため）
        pass
