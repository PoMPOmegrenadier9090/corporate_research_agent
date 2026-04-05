---
name: notion-episode-workflow
description: 就活エピソードDB（Notion）から情報を段階的に取得するワークフロー。レコード一覧を取得して、興味深いエピソードの内容を読む際に使用します。
---

# Notion Episode Workflow

就活エピソードDB（Notion）からエピソード情報を段階的に取得するワークフローです。

## Workflow Overview

1. **List Records**: `notion-episode-list-records` スキルを使用して、就活エピソード一覧を取得
2. **Get Content**: `notion-episode-get-content` スキルを使用して、重要だと判断したエピソードの本文を読む