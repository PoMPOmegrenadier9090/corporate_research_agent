---
name: schedule-from-email-workflow
description: メールの予定抽出からユーザー確認を経て、Notion Task DBへ登録する一連のフロー．企業の最新イベント・選考情報などについて質問された際に使用．
---

# Schedule From Email Workflow

## 1. Core Workflow
1. **Search**: `gmail_search_emails` で関連メールを取得 (クエリは企業名等に限定)
2. **Extract & Present**: メール本文から 日時・企業・イベント名・URL を抽出し，ユーザーに提示．追加の許可を得る．
4. **Company Resolution**: `notion_search_company()` で企業IDを取得．この際，日本語名とともに英語名をaliasesに含める (マッチ複数時は尤もらしいものを選択．該当なし時は設定を省略)
3. **Schema Check**: `notion_task_get_schema()` を実行し、使用可能なプロパティ名と型(`multi_select`, `date`, `relation`等)を**絶対の基準**とする
5. **Create**: ユーザー許可後、重複確認(`notion_task_list_records`)の上、`notion_add_job_task` を実行．この際，**確認できた情報に関してはスキーマに従ってプロパティ設定する**
6. **Append Notes**: `notion_append_task_content` で概要、参考URL、根拠メール(subject/date/id)を追記


## 2. Property Mapping Strict Rules
例外なく `notion_task_get_schema()` の結果に完全一致させること。定義にないプロパティは引数に含めない。

| 型 | 設定方法・フォーマット | 備考 |
| --- | --- | --- |
| **Title** | `notion_add_job_task(title="...")` | `properties`の中ではなく引数で直接指定 |
| **multi_select** | `{"カテゴリ": ["選考"]}` | `options`に完全一致する値のみ指定可 |
| **date** | `{"日付": "2026-04-23"}`<br>時間指定: `{"日付": {"start": "2026-04-23T23:59", "time_zone": "Asia/Tokyo"}}` | 形式に注意 |
| **relation** | `{"企業": {"id": "<page_id>"}}` | 該当企業が存在しない場合はこのプロパティ設定自体を省略し、本文に企業名を記載 |

## 3. Mandatory Rules
- **No Implicit Write**: ユーザーの明示指示前に `notion_add_job_task` を決して呼ばない。
- **Strict Schema**: エラー時は必ずスキーマを再確認し、存在しない項目や選択肢を設定しない。
- **Dedup Before Create**: 作成前に同一予定（タイトル・日時・企業）が存在しないか確認する。
- **Traceability**: 予定の根拠となったメールの subject, date, id は必ず本文に追記する。

### Tool Usage Notes
- `notion_task_list_records` は既定で `include_completed=False`（完了タスクは除外）。
- 完了タスクも重複確認対象にしたい場合のみ `include_completed=True` を明示する。
- 就活予定の重複確認では `area="就活"` を必ず指定する。

## 4. Output Contract (ユーザー提示時)
抽出結果は以下の形式で簡潔に提示し、登録の許可を求める。

```
📋 検索結果: N 件の予定候補

- **[イベント名]** (日時: ..., 企業: DB登録済/未登録)
  - 根拠メール: Subject "...", Date "..."

⚠️ 確認事項: (日時が曖昧、企業が未登録でDB紐付けできない等があれば記載)

これらの予定を Notion に追加してもよろしいですか？
```
