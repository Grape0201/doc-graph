.PHONY: help up down restart logs seed dev backend frontend build clean

# デフォルト環境変数
API_URL ?= http://localhost:8000
SEED_COUNT ?= 50

help: ## ヘルプ表示
	@echo ""
	@echo "Doc-Graph — 開発用コマンド"
	@echo "=========================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""

# --- インフラ ---

up: ## Docker Compose でサービスを起動
	docker compose up -d
	@echo "⏳ OpenSearch の起動を待機中..."
	@until curl -s http://localhost:9200 > /dev/null 2>&1; do sleep 2; done
	@echo "✅ OpenSearch 起動完了"
	@echo "⏳ Neo4j の起動を待機中..."
	@until curl -s http://localhost:7474 > /dev/null 2>&1; do sleep 2; done
	@echo "✅ Neo4j 起動完了"
	@echo "🚀 全サービス起動完了"

down: ## Docker Compose でサービスを停止
	docker compose down

restart: ## サービスを再起動
	docker compose restart

logs: ## サービスのログを表示
	docker compose logs -f

logs-backend: ## バックエンドのログのみ表示
	docker compose logs -f backend

logs-opensearch: ## OpenSearch のログのみ表示
	docker compose logs -f opensearch

logs-neo4j: ## Neo4j のログのみ表示
	docker compose logs -f neo4j

# --- データ ---

seed: ## サンプルデータを投入
	python scripts/seed_data.py --api-url $(API_URL) --count $(SEED_COUNT)

seed-export: ## サンプルデータをJSONに出力（API不要）
	python scripts/seed_data.py --export-only --count $(SEED_COUNT)

# --- 開発 ---

dev: ## バックエンド + フロントエンドを同時に開発起動（Docker サービス起動済み前提）
	@echo "🔧 バックエンドとフロントエンドを起動します..."
	@echo "   バックエンド: http://localhost:8000"
	@echo "   フロントエンド: http://localhost:5173"
	@$(MAKE) -j2 backend frontend

backend: ## バックエンドを開発モードで起動
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend: ## フロントエンドを開発モードで起動
	cd frontend && npm run dev

# --- ビルド ---

build: ## フロントエンドをビルド
	cd frontend && npm run build

# --- テスト ---

test: ## バックエンドのテストを実行
	cd backend && python -m pytest tests/ -v

test-integration: ## 統合テストを実行（Docker サービス起動済み前提）
	cd backend && python -m pytest tests/integration/ -v

# --- クリーンアップ ---

clean: ## ビルド成果物やキャッシュを削除
	rm -rf frontend/dist
	rm -rf frontend/node_modules
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

clean-data: ## Docker ボリューム（データ）を削除して初期化
	docker compose down -v
	@echo "🗑️ データボリュームを削除しました"
