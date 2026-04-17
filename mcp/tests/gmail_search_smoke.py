import argparse
import json
import os
import sys


AGENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if AGENT_DIR not in sys.path:
    sys.path.append(AGENT_DIR)


def _resolve_auth_file_paths() -> tuple[str, str]:
    credentials_path = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")
    token_path = os.getenv("GMAIL_TOKEN_PATH", "token.json")
    return credentials_path, token_path


def run_test(query: str, max_results: int) -> int:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except Exception:
        pass

    credentials_path, token_path = _resolve_auth_file_paths()
    if not os.path.exists(token_path) and not os.path.exists(credentials_path):
        print(
            json.dumps(
                {
                    "status": "skipped",
                    "reason": "Gmail auth files are not configured.",
                    "credentials_path": credentials_path,
                    "token_path": token_path,
                    "hint": "Set GMAIL_CREDENTIALS_PATH (or place credentials.json) and rerun.",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    from tools.gmail_search.main import search_emails

    result = search_emails(query=query, max_results=max_results)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if isinstance(result, dict) and result.get("status") == "error":
        return 1
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke script for Gmail MCP tool")
    parser.add_argument(
        "--query",
        default="就活 面接",
        help="Gmail search query. Tool enforces recent 14 days filter automatically.",
    )
    parser.add_argument("--max_results", type=int, default=5, help="Maximum number of messages to fetch")

    args = parser.parse_args()
    code = run_test(query=args.query, max_results=args.max_results)
    sys.exit(code)


if __name__ == "__main__":
    main()
