# usage-statusline

[English](README.md)

Claude Code のプランの使用量を表示し、その記録を残す、小さなステータスラインです。

```
Opus | ctx 12% | セッション 20% / 週 41%
```

- モデル、コンテキストの使用率、Claude Code がステータスラインに渡す使用量（5 時間のセッション／7 日の週）を表示します。
- 使用量が変わったときだけ `usage-log.tsv` に 1 行足すので、作業ごとにどれだけ使ったかを後から見られます。
- 1 ファイル・約 50 行。Node.js で動きます。Node.js がなければ Python 3 版もあります。依存なし、ネットワークへのアクセスなし、追加の API 呼び出しなし。

## 入れ方

Node.js 18 以上が要ります。

1. `statusline.mjs` を `~/.claude/statusline.mjs` にコピーします。
2. `~/.claude/settings.json`（またはプロジェクトの `.claude/settings.json`）に次を足します。日本語で表示するときは `STATUSLINE_LANG=ja` を付けます。

```json
{
  "statusLine": {
    "type": "command",
    "command": "STATUSLINE_LANG=ja node ~/.claude/statusline.mjs"
  }
}
```

使用量は、会話の最初の応答のあとから表示されます。

### Node.js がないとき（Python）

`statusline.py` は、同じことを Python 3 の標準ライブラリだけで行います（3.11 と 3.13 で確かめました）。`~/.claude/statusline.py` にコピーし、コマンドを次のようにします。

```json
{
  "statusLine": {
    "type": "command",
    "command": "STATUSLINE_LANG=ja python3 ~/.claude/statusline.py"
  }
}
```

## 記録

`usage-log.tsv` は、スクリプトと同じフォルダに書かれます。列はタブ区切りです。

| 列 | 例 |
|---|---|
| 時刻（ローカル） | `2026-11-13 10:25` |
| セッション %（5 時間） | `7` |
| 週 %（7 日） | `13` |
| セッション ID（先頭 8 文字） | `a1b2c3d4` |

使用量はアカウント全体の値です。複数の会話を同時に動かしていると、それぞれの行に他の会話の分も含まれます。どの会話が書いた行かは、セッション ID の列で分かります。

## 設定

| 環境変数 | 意味 |
|---|---|
| `USAGE_LOG_FILE` | 記録のファイルのパス |
| `STATUSLINE_LANG` | `ja` で日本語の表示 |

## 注意

- Claude Code がステータスラインに渡す JSON の `rate_limits` に頼っています。これが変わると使用量の部分は消えますが、ほかの表示は動き続けます。
- ペースの表示や、上限に達する時刻の予測が欲しい場合は、ほかのステータスラインにあります。これはわざと小さくしています。

## テスト

```bash
node --test          # statusline.mjs
python3 -m unittest  # statusline.py
```

## ライセンス

MIT
