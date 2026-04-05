## Corporate Research Agent Workflow
Gemini CLIを利用した，就活をサポートするための企業調査エージェント．
Discordから指示を出し，エージェントが企業の財務情報，企業文化，技術スタックなどの情報を自律的に調査してNotionに記録します．Discordのスレッド機能を利用して，マルチターンの会話を通し，段階的に企業研究を深めることも可能です．

## システム構成
### コンポーネント
- `gemini-agent`（Docker）
	- FastAPI サーバ（`agent/api.py`）
	- Gemini CLI（認証情報は `/root/.gemini` に保存され，ホストの `./.gemini` と共有）
	- 調査/更新ツール群（`uv run -m tools....`）
- `discord-bot`（Docker）
	- Discord からのメッセージを受け取り，`gemini-agent` の `/ask` にHTTPで転送

### データフロー
1. User → Discord で企業名などを指示
2. Discord → `discord-bot` がメッセージを受信
3. `discord-bot` → `gemini-agent` に `/ask` を POST
4. `gemini-agent` → 検索/IR取得/ページ抽出 → Notion へ追記

## セットアップ
### 1. Dockerコンテナの開始
`agent`，メッセージングアプリとの通信を担う`bot`のデプロイを同時に行います．

```
docker compose up -d --build --remove-orphans
```

### 2. Gemini CLI認証
Google loginでGemini CLIにログインします．

```
docker compose exec gemini-agent gemini
```

利用規約のため，Gemini API Keyを利用して認証する必要があります

### 3. Notion DBの準備
https://www.notion.so/ed5718ffb6a883aaa1f481bc0c7a62e7?v=de6718ffb6a883f99df18872e13e6014&source=copy_link
上記のNotionページを参照して，企業データベースを作成します．

DBの構成に合わせて，
`agent/tools/notion/profiles/` 配下の profile JSON（例: `company.json`）を編集します．

Notionツールは汎用エントリから profile を指定して実行できます。追加したDBの設定に合わせて，profile，Skills，toolsを適宜編集/追加します．

```bash
cd agent
uv run -m tools.notion.main --profile company get --name "PKSHA Technology"
```

### 4. 環境変数の設定
```
cp .env.example .env
```

`.env`ファイルを開いて、Notion API，Discord botの認証に必要な環境変数を設定してください．

- Discord Bot：https://discord.com/developers/applications にて新しいアプリケーションを作成し，Botを追加します．Botのトークンを`.env`の`DISCORD_TOKEN`に設定してください
- Notion API: https://www.notion.so/profile/integrations/internal にて新しいインテグレーションを作成し，DBへのアクセス権を付与します．インテグレーションのシークレットを`.env`の`NOTION_API_TOKEN`に設定してください
- また、複製したNotion DBのURLからDB IDを抜き取って、`.env`の`NOTION_DB_ID`に設定してください
- その他，DBの構成に応じてprofile JSONの編集を行います．
- JINA AI: https://jina.ai/
- Tavily: https://www.tavily.com/

### 5. 実行
Discordでスレッドを作成し，`/new`から始めると新規セッション，`/chat`から始めると続きの会話が可能です．企業名を指示すると，エージェントが自律的に企業を調査してNotionに記録します．

### Agentの開発
`agent/`においてagentの呼び出しやツールスクリプトの作成を行います．agentはuvで開発しています．パッケージの追加は以下で実行できます．

```
docker compose exec gemini-agent uv add [package-name]
```

## 注意
Gemini CLIのYOLOモードを利用しています．そのため，エージェントはあらゆるコマンドを承認なしに実行することができます．プロンプトインジェクションにより，意図しないコマンドが実行されるリスクがあります．
コンテナ内で実行するため，システムに対する危険性はありませんが，環境変数の漏洩の危険性があります．Gemini CLIが実行できるコマンドの制限や，コンテナの分離などの対策が必要です．

## 参考文献
1. [Build, debug & deploy with AI | Gemini CLI](https://geminicli.com/)
2. [IRBANK - 企業の決算情報・株価情報・企業分析・銘柄発掘](https://irbank.net/)
3. [東証上場銘柄一覧 | 日本取引所グループ](https://www.jpx.co.jp/markets/statistics-equities/misc/01.html)
4. [Jina AI - Your Search Foundation, Supercharged.](https://jina.ai/)
5. [Discord Developer Platform - Documentation - Discord](https://docs.discord.com/developers/intro)
6. [マーケットプレイスプロフィール](https://www.notion.so/profile/integrations/internal)
7. [Overview - Agent Skills](https://agentskills.io/home)
8. [FastAPI](https://fastapi.tiangolo.com/)
9. [ramnes/notion-sdk-py: Notion API client SDK, rewritten in Python! (sync + async)](https://github.com/ramnes/notion-sdk-py)
10. [Beautiful Soup Documentation — Beautiful Soup 4.4.0 documentation](https://beautiful-soup-4.readthedocs.io/en/latest/)
