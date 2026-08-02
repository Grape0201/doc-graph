# Doc-Graph — ナレッジグラフ型ドキュメント管理システム

PDF文書・OCRテキスト・詳細メタデータを管理し、日本語での全文検索および文書間参照関係を中心としたグラフ可視化を実現するシステム。

従来型の「検索ボックス＋一覧表示」ではなく、**グラフ探索を主UI**とし、文書・キーワード・機器番号などを結ぶナレッジグラフとして情報を提示します。

## アーキテクチャ

```
┌─────────────────────────────────────────────────────────┐
│  Frontend (React + Vite + Cytoscape.js)                 │
│  検索UI + グラフ可視化 + ノード詳細パネル                    │
└──────────────┬──────────────────────┬────────────────────┘
               │                      │
       検索API │              グラフAPI │
               ▼                      ▼
┌─────────────────────────────────────────────────────────┐
│  Backend API (FastAPI)                                   │
│  /api/search  /api/graph/expand  /api/ingest            │
└──────┬──────────────────────────────────┬───────────────┘
       │                                  │
       ▼                                  ▼
┌──────────────────┐          ┌───────────────────────┐
│  OpenSearch       │          │  Neo4j Community      │
│  + kuromoji       │          │  グラフDB              │
│  全文検索/メタデータ │          │  関係探索              │
└──────────────────┘          └───────────────────────┘
```

## 技術スタック

| コンポーネント | 技術 | 用途 |
|---|---|---|
| バックエンド | Python 3.12 + FastAPI | 検索API・グラフ探索API |
| フロントエンド | React + TypeScript (Vite) | UI |
| グラフ描画 | Cytoscape.js | グラフ可視化 |
| 全文検索 | OpenSearch + kuromoji | 日本語全文検索・メタデータ検索 |
| グラフDB | Neo4j Community Edition | 文書間関係の管理・探索 |
| インフラ | Docker Compose | 開発環境 |

## セットアップ

### 前提条件

- Docker & Docker Compose
- Python 3.12+
- Node.js 20+

### 1. リポジトリをクローン

```bash
git clone <repository-url>
cd doc-graph
```

### 2. Docker サービスを起動

```bash
make up
```

OpenSearch（port 9200）、Neo4j（port 7474, 7687）が起動します。

### 3. バックエンド環境構築

```bash
# Python 仮想環境を作成
python -m venv .venv
source .venv/bin/activate

# 依存パッケージをインストール
pip install -e ".[dev]"
```

### 4. フロントエンド環境構築

```bash
cd frontend
npm install
```

### 5. サンプルデータを投入

```bash
# バックエンドを起動（別ターミナル）
make backend

# サンプルデータを投入
make seed
```

### 6. 開発サーバーを起動

```bash
# バックエンド + フロントエンドを同時に起動
make dev
```

- バックエンド: http://localhost:8000
- フロントエンド: http://localhost:5173
- OpenSearch: http://localhost:9200
- Neo4j Browser: http://localhost:7474

## 開発コマンド

```bash
make help        # 利用可能なコマンド一覧
make up          # Docker サービスを起動
make down        # Docker サービスを停止
make dev         # 開発サーバーを起動
make seed        # サンプルデータを投入
make test        # テストを実行
make clean       # キャッシュ等を削除
make clean-data  # データを初期化
```

## ディレクトリ構成

```
doc-graph/
├── docker-compose.yml          # Docker Compose 設定
├── docker/
│   └── opensearch/             # OpenSearch カスタムイメージ
├── backend/
│   └── app/
│       ├── main.py             # FastAPI エントリーポイント
│       ├── config.py           # 設定管理
│       ├── models/             # Pydantic モデル
│       ├── clients/            # OpenSearch / Neo4j クライアント
│       ├── routers/            # APIルーター
│       └── services/           # ビジネスロジック
├── frontend/                   # React + TypeScript (Vite)
│   └── src/
│       ├── api/                # API クライアント
│       ├── types/              # TypeScript 型定義
│       └── components/         # UIコンポーネント
├── scripts/
│   └── seed_data.py            # サンプルデータ生成
├── Makefile                    # 開発用コマンド
└── specification.md            # 要件定義・仕様書
```

## ライセンス

- OpenSearch: Apache License 2.0
- Neo4j Community Edition: GPL v3（自社利用のみ、再配布なし）
