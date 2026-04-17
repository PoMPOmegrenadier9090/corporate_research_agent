---
name: schedule-from-email-workflow
description: 新着予定・最新の選考情報の確認や管理が必要なときに、メール検索から予定抽出、ユーザー確認、Notion Task DBへの登録までを段階的に実行するワークフロー。
---

# Schedule From Email Workflow

新着の予定確認を依頼されたとき、または確認が必要だと判断したときに使うワークフローです。

## Workflow

1. Keyword Generation
- ユーザーの質問や文脈から、予定検索に使うキーワードを作る。
- 例: 会社名、イベント種別、日付語（締切、面談、説明会、インターン、一次締切 など）。

2. Fetch Emails via MCP
- `gmail_search_emails` を使って関連メールを取得する。
- `query` は生成したキーワードを中心に作る。
- `max_results` は必要最小限（例: 5-20件）で開始する。

3. Analyze and Extract Relevant Schedules
- メール本文から予定情報を抽出する。
- 抽出対象:
  - タイトル
  - 日時
  - 締切
  - 企業名/主催
  - 参加URLや応募URL
  - 根拠（どのメールから抽出したか）
- 質問に無関係な予定は除外する。

4. Present to User First
- 抽出結果を一度ユーザーに提示する。
- この時点では Notion へ書き込まない。
- 不明点（日時不明、重複候補、曖昧表現）は明示する。

5. Add to Notion Task DB Only on Explicit Instruction
- ユーザーから追加指示があった場合のみ `notion_add_task` を実行する。
- 必要に応じて `notion_task_list_records` で既存タスクの重複確認を行う。
- すでにあるタスクで追記情報がある場合は `notion_append_task_content` を使う。

## Mandatory Rules

1. No implicit write:
- ユーザーの明示指示なしに `notion_add_task` を呼ばない。

2. Relevance first:
- ユーザー質問との関連性が弱い予定は候補から除外する。

3. Traceability:
- 抽出した予定には根拠メール（subject/date/id）の参照情報を残す。

4. Dedup before create:
- 同一予定の重複登録を避ける。タイトル・日時・企業名で照合する。

## Output Contract

ユーザー提示時は、次の形式で簡潔にまとめる。

- 候補予定一覧（箇条書き）
  - 件名/イベント名
  - 日時・締切
  - 企業名
  - 参考リンク
  - 根拠メール（subject, date, id）
- 追加対象として推奨する予定
- 不明点・確認事項
