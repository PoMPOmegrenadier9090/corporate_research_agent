## Agent Development
Gemini CLIを使ったエージェントシステムの構築を行います．

## 開発方法
### Dockerコンテナの開始
`agent`，メッセージングアプリとの通信を担う`bot`のデプロイを同時に行います．

```
docker compose up -d --build --remove-orphans
```

### Agentの開発
`agent/`においてagentの呼び出しやツールスクリプトの作成を行います．agentはuvで開発しています．パッケージの追加は以下で実行できます．

```
docker compose exec gemini-agent uv add [package-name]
```