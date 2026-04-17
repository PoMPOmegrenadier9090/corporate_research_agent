import os
import datetime
import json
import base64
import re
import html
from typing import Any
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def _get_auth_file_paths() -> tuple[str, str]:
    """Resolve credential/token paths from environment or sensible defaults."""
    credentials_path = os.getenv('GMAIL_CREDENTIALS_PATH', 'credentials.json')
    token_path = os.getenv('GMAIL_TOKEN_PATH', 'token.json')
    return credentials_path, token_path

def setup_gmail_token() -> str:
    """Run the OAuth flow locally to generate a token.json file."""
    credentials_path, token_path = _get_auth_file_paths()
    
    if not os.path.exists(credentials_path):
        raise FileNotFoundError(
            f"Gmail OAuth client file not found: {credentials_path}. "
            "Download it from GCP and place it here."
        )

    from google_auth_oauthlib.flow import InstalledAppFlow
    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
    creds = flow.run_local_server(port=0)
    
    with open(token_path, 'w') as token:
        token.write(creds.to_json())
        
    return token_path


def get_gmail_service():
    """Returns Gmail API service instance using strictly the environment variable."""
    env_token = os.getenv('GMAIL_OAUTH_TOKEN_JSON')

    if not env_token:
        raise ValueError(
            "GMAIL_OAUTH_TOKEN_JSON error: Environment variable is not set. "
            "Run setup (python -m mcp.tools.gmail_search.main --setup) to generate it."
        )

    try:
        token_info = json.loads(env_token)
        creds = Credentials.from_authorized_user_info(token_info, SCOPES)
    except json.JSONDecodeError:
        raise ValueError("GMAIL_OAUTH_TOKEN_JSON is not a valid JSON string.")

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise ValueError("Credentials are not valid and cannot be refreshed. Please run setup again.")

    service = build('gmail', 'v1', credentials=creds)
    return service

def _extract_header(headers, name: str) -> str:
    for h in headers:
        if h.get('name', '').lower() == name.lower():
            return h.get('value', '')
    return ''


def _decode_base64url(data: str) -> str:
    if not data:
        return ''
    padded = data + '=' * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded).decode('utf-8', errors='replace')


def _compact_text(text: str) -> str:
    """空白や改行を整理してテキストをコンパクトにする"""
    if not text:
        return ''

    # Normalize line endings and invisible spaces often found in HTML emails.
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)
    text = re.sub(r'[\u00a0\u2000-\u200a\u202f\u205f\u3000]', ' ', text)

    # Collapse inline whitespace and trim spaces around newlines.
    text = re.sub(r'[\t\f\v ]+', ' ', text)
    text = re.sub(r' *\n *', '\n', text)

    # Collapse repeated blank lines (including lines that only had spaces).
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _html_to_text(raw_html: str) -> str:
    if not raw_html:
        return ''

    # Keep major block boundaries as newlines before stripping tags.
    text = re.sub(r'(?is)<(script|style).*?>.*?</\1>', ' ', raw_html)
    text = re.sub(r'(?i)<br\s*/?>', '\n', text)
    text = re.sub(r'(?i)</(p|div|li|tr|td|th|h[1-6])\s*>', '\n', text)
    text = re.sub(r'(?s)<[^>]+>', ' ', text)
    text = html.unescape(text)
    return _compact_text(text)


def _extract_body(payload: dict[str, Any]) -> str:
    # Simple strategy: prefer text/plain in parts, then text/html, then direct body.data.
    plain_parts: list[str] = []
    html_parts: list[str] = []

    def walk(part: dict[str, Any]) -> None:
        mime_type = part.get('mimeType', '')
        body_data = part.get('body', {}).get('data', '')

        if body_data:
            decoded = _decode_base64url(body_data)
            if mime_type == 'text/plain':
                plain_parts.append(decoded)
            elif mime_type == 'text/html':
                html_parts.append(decoded)

        for child in part.get('parts', []) or []:
            walk(child)

    walk(payload)

    if plain_parts:
        return _compact_text('\n'.join(plain_parts))
    if html_parts:
        return _html_to_text('\n'.join(html_parts))

    direct = payload.get('body', {}).get('data', '')
    direct_decoded = _decode_base64url(direct)
    if '<' in direct_decoded and '>' in direct_decoded:
        return _html_to_text(direct_decoded)
    return _compact_text(direct_decoded)


def _truncate_text(text: str, max_chars: int) -> str:
    if max_chars <= 0:
        return text
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n... (truncated)"


def _is_strict_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)

def search_emails(
    query: str,
    max_results: int = 10,
    lookback_days: int = 14,
    body_max_chars: int = 3000,
) -> dict[str, Any]:
    """
    Search Gmail for messages matching query within the last 14 days.
    """
    try:
        service = get_gmail_service()

        if not _is_strict_int(max_results):
            return {"status": "error", "error": "max_results must be int"}
        if not _is_strict_int(lookback_days):
            return {"status": "error", "error": "lookback_days must be int"}
        if not _is_strict_int(body_max_chars):
            return {"status": "error", "error": "body_max_chars must be int"}

        if max_results <= 0:
            return {"status": "error", "error": "max_results must be >= 1"}
        
        if lookback_days <= 0:
            return {"status": "error", "error": "lookback_days must be >= 1"}

        # Enforce the newer_than filter
        if "newer_than:" not in query and "after:" not in query:
            query = f"{query} newer_than:{lookback_days}d"

        results = service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
        messages = results.get('messages', [])

        if not messages:
            return {"status": "success", "messages": [], "message": f"No messages found within the last {lookback_days} days."}

        email_data_list = []
        for msg in messages:
            txt = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
            payload = txt.get('payload', {})
            headers = payload.get('headers', [])
            
            subject = _extract_header(headers, "Subject")
            sender = _extract_header(headers, "From")
            date = _extract_header(headers, "Date")

            body = _truncate_text(_extract_body(payload), body_max_chars)
            
            email_data = {
                "id": msg['id'],
                "subject": subject,
                "from": sender,
                "date": date,
                "body": body
            }
            email_data_list.append(email_data)

        return {
            "status": "success",
            "messages": email_data_list,
            "query": query,
            "count": len(email_data_list),
            "lookback_days": lookback_days,
            "body_max_chars": body_max_chars,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    import argparse
    import json as json_lib

    parser = argparse.ArgumentParser(description="Gmail Search Tool Local Setup and Testing")
    parser.add_argument("--setup", action="store_true", help="Run OAuth setup to generate token.json")
    parser.add_argument("--search", type=str, help="Test search query (e.g., 'is:unread')")
    parser.add_argument("--days", type=int, default=14, help="Look back this many days (default: 14)")
    parser.add_argument("--body-max-chars", type=int, default=3000, help="Max body chars per email (0 to disable truncation)")
    args = parser.parse_args()

    if args.setup:
        print("=== Gmail API OAuth Setup ===")
        print("※ ブラウザ認証を起動し、新しい token.json を生成します。")
        
        try:
            token_path = setup_gmail_token()
            if os.path.exists(token_path):
                print(f"\n【成功】 トークンが {token_path} に生成されました！")
                print("\n以下のJSON文字列をすべてコピーし、環境変数 GMAIL_OAUTH_TOKEN_JSON に設定してください:\n")
                with open(token_path, "r") as f:
                    print(f.read())
                print("\n===============================")
        except Exception as e:
            print(f"\n【エラー】 セットアップに失敗しました: {e}")
            print("credentials.json がカレントディレクトリにあることを確認してください")

    elif args.search:
        print(f"検索クエリ: {args.search} を実行中...")
        result = search_emails(
            args.search,
            lookback_days=args.days,
            body_max_chars=args.body_max_chars,
        )
        print(json_lib.dumps(result, indent=2, ensure_ascii=False))
        
    else:
        parser.print_help()
