# --- Gemini CLIの設定 ---
# キーバリュー形式で指定します。
# True はオプションのみ付与（例: "--yolo"）、False や None はオプションを無効化。
# それ以外の文字列などは値として展開されます（例: "--approval-mode", "auto_edit"）。
GEMINI_CONFIG = {
    "approval-mode": "yolo",
    "output-format": "text",
    "screen-reader": "true",
    "model": "flash"
}