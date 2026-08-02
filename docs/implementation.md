# Doc-Graph 実装ドキュメント

> ナレッジグラフ型ドキュメント管理システム  
> バージョン: 0.1 / 最終更新: 2026-08-02

---

## 目次

1. [システム概要](#1-システム概要)
2. [アーキテクチャ](#2-アーキテクチャ)
3. [インフラ構成](#3-インフラ構成)
4. [バックエンド](#4-バックエンド)
   - 4.1 [設定管理](#41-設定管理)
   - 4.2 [データモデル](#42-データモデル)
   - 4.3 [データストアクライアント](#43-データストアクライアント)
   - 4.4 [API エンドポイント](#44-api-エンドポイント)
   - 4.5 [データフロー（取り込み）](#45-データフロー取り込み)
5. [フロントエンド](#5-フロントエンド)
   - 5.1 [ディレクトリ構成](#51-ディレクトリ構成)
   - 5.2 [状態管理](#52-状態管理)
   - 5.3 [コンポーネント](#53-コンポーネント)
   - 5.4 [グラフ描画の仕様](#54-グラフ描画の仕様)
6. [起動手順](#6-起動手順)
7. [データ投入手順](#7-データ投入手順)
8. [設計上の決定事項](#8-設計上の決定事項)
9. [バグ修正履歴](#9-バグ修正履歴)

---

## 1. システム概要

PDF文書・OCRテキスト・メタデータ（約30項目）を管理し、**グラフ探索を主UI**とするドキュメント管理システム。

従来型の「検索ボックス＋一覧表示」ではなく、文書・キーワード・機器番号を結ぶナレッジグラフとして情報を提示する。

| 特徴 | 内容 |
|---|---|
| 検索 | 日本語OCRテキスト＋キーワード・機器番号の全文検索 |
| グラフ | 文書間の参照関係・キーワード・機器番号をノードとして可視化 |
| 探索 | 起点ノードから最大3ホップのネットワーク展開 |
| スケール | 想定 数TB規模のPDF、同時接続数名 |

---

## 2. アーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (React 19 + Vite + Cytoscape.js)                  │
│  localhost:5173                                             │
└─────────┬──────────────────────────────┬───────────────────┘
          │ GET /api/search              │ GET /api/graph/*
          ▼                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Backend API (FastAPI / Python 3.12)                        │
│  localhost:8000                                             │
│                                                             │
│  /api/search  →  SearchService  →  OpenSearchClient        │
│  /api/graph/* →  GraphService   →  Neo4jClient             │
│  /api/ingest  →  IngestService  →  両クライアントへ二重書込  │
└──────────┬──────────────────────────┬────────────────────────┘
           │                          │
           ▼                          ▼
┌─────────────────┐        ┌──────────────────────┐
│  OpenSearch 2.x  │        │  Neo4j 5 Community   │
│  + kuromoji      │        │  Bolt: 7687          │
│  localhost:9200  │        │  Browser: 7474       │
│                 │        │                      │
│  インデックス:   │        │  (:Document)         │
│  doc-graph-      │        │  (:Keyword)          │
│  documents       │        │  (:Equipment)        │
└─────────────────┘        └──────────────────────┘
```

**設計原則**: 検索エンジン（OpenSearch）とグラフDB（Neo4j）を役割分担させる2ストア構成。

- OpenSearch: 全文検索・メタデータ絞り込み・ハイライト
- Neo4j: ノード/エッジの関係管理・グラフ探索クエリ
- PDF実体は**ファイルストレージに置き、パスのみをDBに記録**（DBに格納しない）

---

## 3. インフラ構成

### Docker Compose サービス

| サービス | イメージ | ポート | 用途 |
|---|---|---|---|
| `opensearch` | カスタム (opensearch:2.18.0 + kuromoji) | 9200, 9600 | 全文検索エンジン |
| `neo4j` | neo4j:5-community | 7474 (HTTP), 7687 (Bolt) | グラフDB |
| `backend` | カスタム (python:3.12-slim) | 8000 | FastAPI サーバー |

#### 依存関係
```
backend → opensearch (healthy後に起動)
backend → neo4j     (healthy後に起動)
```

#### データ永続化
```yaml
volumes:
  opensearch-data:  # /usr/share/opensearch/data
  neo4j-data:       # /data
```

### OpenSearch カスタムイメージ

[docker/opensearch/Dockerfile](file:///Users/shotaro/work/doc-graph/docker/opensearch/Dockerfile) で `analysis-kuromoji` プラグインをインストール済み。

設定 ([docker/opensearch/opensearch.yml](file:///Users/shotaro/work/doc-graph/docker/opensearch/opensearch.yml)):
- `discovery.type: single-node`
- セキュリティプラグイン: 無効（開発用）

---

## 4. バックエンド

### 4.1 設定管理

[backend/app/config.py](file:///Users/shotaro/work/doc-graph/backend/app/config.py) — `pydantic-settings` による環境変数管理

| 変数名 | デフォルト値 | 説明 |
|---|---|---|
| `OPENSEARCH_HOST` | `localhost` | OpenSearch ホスト |
| `OPENSEARCH_PORT` | `9200` | OpenSearch ポート |
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j Bolt URI |
| `PDF_STORAGE_PATH` | `/tmp/pdf_storage` | PDF ファイル格納パス |
| `INDEX_NAME` | `doc-graph-documents` | OpenSearch インデックス名 |

`.env` ファイルで上書き可能。

---

### 4.2 データモデル

#### DocumentMetadata ([backend/app/models/document.py](file:///Users/shotaro/work/doc-graph/backend/app/models/document.py))

| フィールド | 型 | 説明 |
|---|---|---|
| `doc_id` | str | 文書管理ID（主キー） |
| `title` | str | 文書タイトル |
| `related_doc_ids` | list[str] | 参照先の文書管理IDリスト |
| `keywords` | list[str] | キーワードリスト（→ Keyword ノード生成元） |
| `equipment_nos` | list[str] | 機器番号リスト（→ Equipment ノード生成元） |
| `pdf_path` | str | PDFファイルのパス（ストレージ上の絶対パス） |
| `ocr_text` | str | OCRテキスト全文（全文検索対象） |
| `category` | str | 文書種別（例: 設計書, 報告書） |
| `author` | str | 作成者 |
| `created_date` | str | 作成日 (YYYY-MM-DD) |
| `department` | str | 担当部署 |
| `document_type` | str | ドキュメント種別 |
| `status` | str | 文書ステータス（有効/改訂中/廃止/ドラフト） |
| `version` | str | バージョン番号 |
| `facility` | str | 施設名 |
| `building` | str | 建屋 |
| `system_name` | str | 系統名 |
| `manufacturer` | str | メーカー |
| `inspection_date` | str | 点検日 |
| *(他 10 項目)* | str | floor, room, subsystem, model_number 等 |

#### グラフモデル ([backend/app/models/graph.py](file:///Users/shotaro/work/doc-graph/backend/app/models/graph.py))

```python
GraphNode:
  id: str           # ノード識別子 (doc_id / keyword名 / equipment_no)
  label: str        # 表示名
  node_type: str    # "Document" | "Keyword" | "Equipment"
  properties: dict  # Neo4j ノードの全プロパティ

GraphEdge:
  id: str           # "{source}-{type}-{target}" 形式
  source: str       # 始点ノードID
  target: str       # 終点ノードID
  edge_type: str    # "REFERENCES" | "HAS_KEYWORD" | "USES_EQUIPMENT"

GraphExpandResponse:
  nodes: list[GraphNode]
  edges: list[GraphEdge]
  has_more: bool    # limit超過時に true
  total_connected: int  # 実際の接続ノード総数

NodeDetailResponse:
  node: GraphNode
  metadata: dict | None  # Document: OpenSearch の全メタデータ
                         # Keyword/Equipment: {connected_document_count: int}
```

---

### 4.3 データストアクライアント

#### OpenSearchClient ([backend/app/clients/opensearch_client.py](file:///Users/shotaro/work/doc-graph/backend/app/clients/opensearch_client.py))

シングルトンパターン。主要メソッド:

| メソッド | 説明 |
|---|---|
| `initialize()` | インデックスが存在しない場合に kuromoji マッピングで作成 |
| `bulk_index(docs)` | ドキュメント一括インデックス登録 |
| `search(query, filters, page, size)` | `multi_match` + kuromoji + ハイライト |
| `get_document(doc_id)` | ID指定でドキュメント取得 |

**kuromoji アナライザー設定**:
```json
{
  "analyzer": {
    "kuromoji_analyzer": {
      "type": "custom",
      "tokenizer": "kuromoji_tokenizer",
      "filter": ["kuromoji_baseform", "kuromoji_part_of_speech", "cjk_width", "lowercase"]
    }
  }
}
```

**全文検索対象フィールド**: `title`, `ocr_text`, `remarks`, `keywords`, `equipment_nos`

#### Neo4jClient ([backend/app/clients/neo4j_client.py](file:///Users/shotaro/work/doc-graph/backend/app/clients/neo4j_client.py))

シングルトンパターン。主要メソッド:

| メソッド | 説明 |
|---|---|
| `initialize()` | ユニーク制約を作成（doc_id, keyword.name, equipment.equipment_no） |
| `create_document_node()` | Document ノードを MERGE |
| `create_reference_edge()` | REFERENCES エッジを MERGE |
| `create_keyword_node_and_edge()` | Keyword ノード + HAS_KEYWORD エッジを MERGE |
| `create_equipment_node_and_edge()` | Equipment ノード + USES_EQUIPMENT エッジを MERGE |
| `expand_graph()` | 可変長パスで双方向グラフ展開（最大 hops ホップ, limit 件） |
| `get_node_detail()` | 単一ノードの詳細取得 |
| `count_connected_documents()` | Keyword/Equipment に接続する Document 数をカウント |

**グラフスキーマ (Cypher)**:
```cypher
// 制約
CREATE CONSTRAINT doc_id_unique FOR (d:Document) REQUIRE d.doc_id IS UNIQUE
CREATE CONSTRAINT keyword_name_unique FOR (k:Keyword) REQUIRE k.name IS UNIQUE
CREATE CONSTRAINT equip_no_unique FOR (e:Equipment) REQUIRE e.equipment_no IS UNIQUE

// 関係
(:Document {doc_id, title, ...}) -[:REFERENCES]->  (:Document)
(:Document)                      -[:HAS_KEYWORD]->  (:Keyword {name})
(:Document)                      -[:USES_EQUIPMENT]-> (:Equipment {equipment_no})
```

**グラフ展開クエリ** (双方向):
```cypher
MATCH path = (start:Document {doc_id: $node_id})-[*1..{hops}]-(connected)
RETURN path
LIMIT $limit
```

> [!NOTE]
> `[*1..N]-()` は方向なし（双方向）パターン。REFERENCES エッジは有向だが探索は双方向で行う。

---

### 4.4 API エンドポイント

#### 検索 API

```
GET /api/search
```

| パラメータ | 型 | デフォルト | 説明 |
|---|---|---|---|
| `q` | str | `""` | 検索クエリ（空の場合は全件） |
| `page` | int | `1` | ページ番号 |
| `size` | int | `20` | 1ページあたりの件数（最大 100） |

レスポンス:
```json
{
  "results": [
    {
      "doc_id": "DOC-00001",
      "title": "第一発電所 冷却水系統 設計書",
      "score": 4.23,
      "snippet": "...耐震評価を実施した...",
      "highlights": { "ocr_text": ["...耐震<em>評価</em>..."] }
    }
  ],
  "total": 42,
  "page": 1,
  "size": 20
}
```

#### グラフ API

```
GET /api/graph/expand
```

| パラメータ | 型 | デフォルト | 制約 | 説明 |
|---|---|---|---|---|
| `node_id` | str | 必須 | — | 起点ノードID |
| `node_type` | str | `"Document"` | Document/Keyword/Equipment | ノード種別 |
| `hops` | int | `1` | 1〜3 | 展開ホップ数 |
| `limit` | int | `50` | 1〜200 | 取得ノード数上限 |

```
GET /api/graph/node/{node_type}/{node_id}
```

Document の場合は OpenSearch からフルメタデータを返す。  
Keyword/Equipment の場合は `connected_document_count` を返す。

#### データ取り込み API

```
POST /api/ingest/documents   # JSON body: { "documents": [...] }
POST /api/ingest/upload      # multipart/form-data: file (.json)
```

---

### 4.5 データフロー（取り込み）

```
入力 JSON（DocumentMetadataのリスト）
    │
    ├─► OpenSearch: bulk_index()
    │     └─ ocr_text, title, メタデータ全フィールドをインデックス登録
    │
    └─► Neo4j（ドキュメントごとに順次処理）
          ├─ create_document_node(doc_id, title, props)
          ├─ create_reference_edge(doc_id → related_doc_id) × related_doc_ids件数
          ├─ create_keyword_node_and_edge(doc_id, keyword) × keywords件数
          └─ create_equipment_node_and_edge(doc_id, equipment_no) × equipment_nos件数
```

> [!IMPORTANT]
> `related_doc_ids` で参照先 Document ノードが未登録の場合、REFERENCES エッジは作成されない（`MATCH` ベースのため）。取り込み順序に注意するか、全ドキュメントノードを先に作成してからエッジを張ること。

---

## 5. フロントエンド

### 5.1 ディレクトリ構成

```
frontend/
├── src/
│   ├── api/
│   │   └── client.ts         # バックエンドAPIクライアント
│   ├── types/
│   │   └── index.ts          # TypeScript 型定義
│   ├── components/
│   │   ├── SearchBar.tsx      # 検索入力（デバウンス付き）
│   │   ├── FilterPanel.tsx    # メタデータ絞り込みパネル
│   │   ├── SearchResults.tsx  # 検索結果リスト
│   │   ├── GraphView.tsx      # Cytoscape.js グラフ描画
│   │   ├── GraphControls.tsx  # ホップ数・種別フィルター
│   │   └── NodeDetail.tsx     # ノード詳細スライドインパネル
│   ├── App.tsx                # メインレイアウト・状態管理
│   ├── index.css              # デザインシステム（CSS変数・グラスモーフィズム）
│   └── main.tsx
├── package.json
└── vite.config.ts
```

### 5.2 状態管理

`App.tsx` でフラットな React state として管理（外部状態管理ライブラリなし）。

```
Search State
  searchQuery       string          現在の検索クエリ
  searchResults     SearchResult[]  検索結果リスト
  searchTotal       number          ヒット総件数
  searchPage        number          現在ページ
  isSearching       boolean         検索中フラグ

Graph State
  nodes             Map<id, GraphNode>   グラフのノード（ID→ノード）
  edges             Map<id, GraphEdge>   グラフのエッジ（ID→エッジ）
  selectedNodeId    string | null        選択中ノードID
  hops              number               展開ホップ数（1〜3）
  visibleTypes      Set<NodeType>        表示する種別フィルター

Detail State
  nodeDetail        NodeDetailResponse | null   選択ノードの詳細
  isDetailLoading   boolean                     詳細ロード中フラグ
```

**グラフデータ更新の戦略**:
- 新規ノードクリック・ダブルクリック（展開）: 既存 Map に **マージ**（以前のグラフを残す）
- 検索結果クリック（新しい起点）: Map を **クリア**してから新規ロード
- Hops 増加: マージ
- Hops 減少: クリアして再ロード（古いノードを除去するため）

**パフォーマンス**:
- `filteredNodes` / `filteredEdges` は `useMemo` でメモ化し、不要な GraphView 再描画を防止
- `SearchBar` の `onSearch` コールバックは `useCallback` + `useRef` で参照安定化

### 5.3 コンポーネント

#### SearchBar ([SearchBar.tsx](file:///Users/shotaro/work/doc-graph/frontend/src/components/SearchBar.tsx))
- 300ms デバウンス
- `onSearch` を `useRef` 経由で参照（依存配列から除外して繰り返し検索を防止）

#### FilterPanel ([FilterPanel.tsx](file:///Users/shotaro/work/doc-graph/frontend/src/components/FilterPanel.tsx))
- Document Type / Department / Status の絞り込み
- 現状は `console.log`（バックエンドの filter 連携は未実装）

#### SearchResults ([SearchResults.tsx](file:///Users/shotaro/work/doc-graph/frontend/src/components/SearchResults.tsx))
- スコアバッジ・OCRスニペット・ハイライト表示
- ページネーション
- 結果クリック → グラフをクリア → 新規展開

#### GraphView ([GraphView.tsx](file:///Users/shotaro/work/doc-graph/frontend/src/components/GraphView.tsx))
- Cytoscape.js インスタンスは `useRef` で保持（マウント時に1回だけ初期化）
- 要素更新は**差分更新**（削除すべき要素のみ除去、新要素のみ追加）
- 追加または削除があった場合のみ `cose` レイアウトを再実行

#### GraphControls ([GraphControls.tsx](file:///Users/shotaro/work/doc-graph/frontend/src/components/GraphControls.tsx))
- ホップ数スライダー（1〜3）
- ノード種別トグル（Document / Keyword / Equipment）
- ノード数カウント表示

#### NodeDetail ([NodeDetail.tsx](file:///Users/shotaro/work/doc-graph/frontend/src/components/NodeDetail.tsx))
- 右パネルにスライドイン（`animate-slide-right`）
- Document: フルメタデータテーブル + PDF リンクボタン + キーワード/機器番号タグ
- Keyword/Equipment: 接続文書数（バックエンドの `connected_document_count` を参照）
- タグクリック → 新規グラフ展開

### 5.4 グラフ描画の仕様

#### ノード種別

| 種別 | 形状 | 色 | サイズ | IDフィールド |
|---|---|---|---|---|
| Document | 角丸四角形 | シアン `#00d4ff` | 70 × 40 px | `doc_id` |
| Keyword | 円（ellipse） | エメラルド `#00e68a` | 56 × 56 px | `name` |
| Equipment | 六角形 | アンバー `#ffb800` | 52 × 52 px | `equipment_no` |

- ラベル: ノード中央に表示
- Document: 最大12文字（超過は `…`）
- Keyword/Equipment: 最大8文字（超過は `…`）

#### エッジ種別

| 種別 | 線種 | 色 |
|---|---|---|
| REFERENCES | 実線 | シアン 50% |
| HAS_KEYWORD | 破線 | エメラルド 40% |
| USES_EQUIPMENT | 点線 | アンバー 40% |

#### ズーム制限

| 設定 | 値 |
|---|---|
| `minZoom` | 0.3 |
| `maxZoom` | 3.0 |
| `wheelSensitivity` | 0.3 |

#### インタラクション

| 操作 | 挙動 |
|---|---|
| シングルクリック | ノード詳細パネルを表示 |
| ダブルクリック | 隣接ノードを展開（マージ） |

---

## 6. 起動手順

### 前提条件

- Docker & Docker Compose
- Python 3.12+
- [bun](https://bun.sh/) （フロントエンドパッケージマネージャー）

### ステップ

```bash
# 1. データストアを起動
make up
# → OpenSearch (9200), Neo4j (7474/7687) が起動するまで待機

# 2. Python 環境構築
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 3. バックエンド起動（別ターミナル）
make backend
# → http://localhost:8000

# 4. フロントエンド依存インストール（初回のみ）
cd frontend && bun install

# 5. フロントエンド起動（別ターミナル）
make frontend
# → http://localhost:5173
```

### 確認 URL

| サービス | URL |
|---|---|
| フロントエンド | http://localhost:5173 |
| バックエンド API ドキュメント | http://localhost:8000/docs |
| OpenSearch | http://localhost:9200 |
| Neo4j Browser | http://localhost:7474 |

---

## 7. データ投入手順

### サンプルデータ（ダミー）

```bash
# バックエンドが起動している状態で実行
make seed                     # 50件投入
make seed SEED_COUNT=200      # 件数指定

# API不使用でJSONファイルのみ出力
make seed-export
```

[scripts/seed_data.py](file:///Users/shotaro/work/doc-graph/scripts/seed_data.py) で生成されるデータ:
- 文書メタデータ（全30項目）
- OCRテキスト（テンプレートから自動生成）
- related_doc_ids（ランダム参照）
- keywords, equipment_nos（プールからランダム選択）

### 実データの投入

```bash
# JSON 形式でAPIに直接 POST
curl -X POST http://localhost:8000/api/ingest/documents \
  -H "Content-Type: application/json" \
  -d '{"documents": [{"doc_id": "DOC-00001", "title": "設計書", ...}]}'

# JSON ファイルをアップロード
curl -X POST http://localhost:8000/api/ingest/upload \
  -F "file=@your_data.json"
```

JSONの形式:
```json
{
  "documents": [
    {
      "doc_id": "DOC-00001",
      "title": "冷却水系統 設計書",
      "related_doc_ids": ["DOC-00002", "DOC-00005"],
      "keywords": ["冷却", "ポンプ", "バルブ"],
      "equipment_nos": ["P-101", "V-201"],
      "pdf_path": "/data/pdf/DOC-00001.pdf",
      "ocr_text": "本文書は...",
      "category": "設計書",
      "department": "設計部",
      ...
    }
  ]
}
```

---

## 8. 設計上の決定事項

| 項目 | 決定内容 | 理由 |
|---|---|---|
| 参照関係の方向 | 双方向探索（有向エッジ + 双方向クエリ） | どちらの文書からでも参照関係を辿れるようにするため |
| グラフ展開ホップ上限 | 3ホップ | それ以上は過大なノード数になりUIが破綻するため |
| 表示ノード数上限 | 200件 | グラフの視認性とレスポンス性能のバランス |
| グラフ主用途 | 1文書起点のネットワーク探索 | 全体俯瞰（数万ノード）は別途性能設計が必要 |
| キーワード生成方法 | メタデータから機械的抽出 | OCRからの抽出は別途NLP実装が必要なため |
| ハブ制御 | 表示件数上限（has_more フラグ） | UIで「さらに表示」への拡張を想定 |
| DB配置 | Docker Compose 同一ホスト | 開発用。本番では分離を検討 |
| 検索対象 | OCRテキスト + ノード名 | キーワードや機器番号での直接検索ニーズのため |

---

## 9. バグ修正履歴

| 日付 | 問題 | 原因 | 修正 |
|---|---|---|---|
| 2026-08-02 | グラフがチラつく（1ノード↔グラフを行き来） | `App.tsx` の filteredNodes/filteredEdges が毎レンダリング新参照 → GraphView の useEffect が毎回発火 → 全削除+再追加 | `useMemo` でメモ化。GraphView を差分更新方式に変更 |
| 2026-08-02 | 検索バーが定期的にチラつく（繰り返し検索） | SearchBar の useEffect 依存配列に `onSearch` が含まれ、インライン関数の新参照で毎回デバウンスリセット | `onSearch` を `useRef` 経由で参照し依存配列から除外 |
| 2026-08-02 | 他の検索結果クリック時に前のグラフが残る | `loadGraphData` が Map をマージするため古いデータが消えない | `handleResultClick` でグラフを事前クリア |
| 2026-08-02 | Hops を減らしても反映されない | ホップ減少でノードが減るはずが、マージ方式で古いノードが残る | Hops 減少時はクリア+再ロード。GraphView で削除時もレイアウト再計算 |
| 2026-08-02 | ラベル文字がノードに重なり見づらい | `text-valign: bottom` でノード下にラベル配置、長いタイトルが隣接ノードに重なる | ラベルをノード中央 (`center`) に変更、文字数上限で切り詰め、ノードサイズ拡大 |
| 2026-08-02 | Keyword/Equipment の Connected Documents が常に 0 | バックエンドが `metadata: null` を返すためフロントが `related_doc_ids.length` で 0 | Neo4j で接続文書数をカウントして返す `count_connected_documents()` を追加 |
| 2026-08-02 | ズームの上限・下限なし | 未設定 | `minZoom: 0.3`, `maxZoom: 3.0` を設定 |
