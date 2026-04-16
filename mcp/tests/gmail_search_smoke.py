import argparse
import json
import os
import sys


AGENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if AGENT_DIR not in sys.path:
    sys.path.append(AGENT_DIR)


def run_test(query: str, max_results: int) -> int:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except Exception:
        pass

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
