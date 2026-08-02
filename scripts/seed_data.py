"""
サンプルデータ生成・投入スクリプト

ダミーの文書メタデータ・OCRテキスト・参照関係を生成し、
バックエンドAPI (/api/ingest/documents) を通じて OpenSearch / Neo4j にロードする。

Usage:
    python scripts/seed_data.py [--api-url http://localhost:8000] [--count 50]
"""

import argparse
import json
import random
import sys
from datetime import datetime, timedelta
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# --- サンプルデータ定義 ---

CATEGORIES = ["設計書", "報告書", "手順書", "仕様書", "議事録", "点検記録", "試験成績書", "図面", "マニュアル", "通知"]
DEPARTMENTS = ["設計部", "保守部", "品質管理部", "安全管理部", "運転部", "技術部", "計装制御部", "電気部", "機械部", "土木建築部"]
DOCUMENT_TYPES = ["技術文書", "管理文書", "外部文書", "法定文書", "社内標準"]
STATUSES = ["有効", "改訂中", "廃止", "ドラフト"]
FACILITIES = ["第一発電所", "第二発電所", "変電所A", "変電所B", "制御センター"]
BUILDINGS = ["本館", "タービン建屋", "制御建屋", "補機建屋", "事務棟"]
FLOORS = ["1F", "2F", "3F", "B1F", "屋上"]
SYSTEMS = ["冷却水系統", "蒸気系統", "電気系統", "計装制御系統", "換気空調系統", "給排水系統", "防災系統"]
SUBSYSTEMS = ["一次系", "二次系", "補助系", "非常用系", "常用系"]
MANUFACTURERS = ["東芝", "日立", "三菱重工", "富士電機", "横河電機", "アズビル", "オムロン"]

KEYWORDS_POOL = [
    "定期点検", "バルブ", "ポンプ", "配管", "耐震", "安全評価",
    "運転手順", "緊急停止", "冷却", "温度監視", "圧力計",
    "電動機", "変圧器", "遮断器", "制御盤", "センサー",
    "漏洩検知", "腐食対策", "保全計画", "劣化診断",
    "振動測定", "絶縁抵抗", "熱交換器", "フィルター", "タンク",
    "流量計", "レベル計", "警報設定", "インターロック", "試運転",
]

EQUIPMENT_POOL = [
    "P-101", "P-102", "P-201", "P-301", "V-101", "V-102", "V-201",
    "HX-101", "HX-201", "T-101", "T-201", "C-101", "FT-101", "FT-201",
    "PT-101", "PT-201", "TT-101", "TT-201", "LT-101", "LT-201",
    "MV-101", "MV-201", "MV-301", "CV-101", "CV-201",
    "TR-101", "TR-201", "CB-101", "CB-201", "MCC-101",
]

AUTHORS = [
    "田中太郎", "鈴木一郎", "佐藤花子", "高橋健一", "渡辺美咲",
    "伊藤大輔", "山本和子", "中村正", "小林幸子", "加藤裕介",
]

TITLE_TEMPLATES = [
    "{facility} {system} {category}",
    "{equipment} {category} （{year}年度）",
    "{system} {subsystem} {category}",
    "{facility} {building} {category}",
    "{system} {keyword} に関する{category}",
]

OCR_TEXT_TEMPLATES = [
    "本文書は{facility}の{system}に関する{category}である。{keyword1}および{keyword2}について記載する。対象機器は{equipment}である。",
    "{year}年{month}月に実施した{keyword1}の結果を報告する。{facility} {building}の{system}において、{equipment}の{keyword2}を確認した。",
    "{system}の{subsystem}における{keyword1}手順を定める。{equipment}の運転操作に際し、{keyword2}に留意すること。",
    "本{category}は{facility}の{building}に設置された{equipment}の{keyword1}結果をまとめたものである。{keyword2}に関する評価も含む。",
    "{keyword1}に基づく{system}の安全評価結果を示す。{facility}の{equipment}について、{keyword2}の観点から検討を行った。",
]


def generate_date(start_year: int = 2015, end_year: int = 2026) -> str:
    """ランダムな日付を生成"""
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = end - start
    random_date = start + timedelta(days=random.randint(0, delta.days))
    return random_date.strftime("%Y-%m-%d")


def generate_document(doc_index: int, total_count: int) -> dict:
    """1件のダミー文書メタデータを生成"""
    doc_id = f"DOC-{doc_index:05d}"
    facility = random.choice(FACILITIES)
    building = random.choice(BUILDINGS)
    system = random.choice(SYSTEMS)
    subsystem = random.choice(SUBSYSTEMS)
    category = random.choice(CATEGORIES)
    keywords = random.sample(KEYWORDS_POOL, k=random.randint(2, 6))
    equipment_nos = random.sample(EQUIPMENT_POOL, k=random.randint(1, 4))
    year = random.randint(2015, 2026)

    # タイトル生成
    title_template = random.choice(TITLE_TEMPLATES)
    title = title_template.format(
        facility=facility,
        system=system,
        category=category,
        equipment=equipment_nos[0],
        subsystem=subsystem,
        keyword=keywords[0],
        year=year,
        building=building,
    )

    # OCRテキスト生成
    ocr_template = random.choice(OCR_TEXT_TEMPLATES)
    ocr_text = ocr_template.format(
        facility=facility,
        building=building,
        system=system,
        subsystem=subsystem,
        category=category,
        equipment=equipment_nos[0],
        keyword1=keywords[0],
        keyword2=keywords[1] if len(keywords) > 1 else keywords[0],
        year=year,
        month=random.randint(1, 12),
    )
    # OCRテキストを少し長くする
    ocr_text = ocr_text * random.randint(2, 5)

    # 関連文書ID（他の文書への参照をランダムに生成）
    num_related = random.randint(0, min(5, total_count - 1))
    related_indices = random.sample(
        [i for i in range(1, total_count + 1) if i != doc_index],
        k=min(num_related, total_count - 1),
    )
    related_doc_ids = [f"DOC-{i:05d}" for i in related_indices]

    created_date = generate_date(2015, 2024)
    updated_date = generate_date(2024, 2026)
    installation_date = generate_date(2010, 2020)
    inspection_date = generate_date(2024, 2025)
    next_inspection_date = generate_date(2026, 2027)

    return {
        "doc_id": doc_id,
        "title": title,
        "related_doc_ids": related_doc_ids,
        "keywords": keywords,
        "equipment_nos": equipment_nos,
        "pdf_path": f"/data/pdf/{doc_id}.pdf",
        "ocr_text": ocr_text,
        "category": category,
        "author": random.choice(AUTHORS),
        "created_date": created_date,
        "updated_date": updated_date,
        "department": random.choice(DEPARTMENTS),
        "document_type": random.choice(DOCUMENT_TYPES),
        "status": random.choice(STATUSES),
        "version": f"{random.randint(1, 5)}.{random.randint(0, 9)}",
        "classification": random.choice(["一般", "社外秘", "部外秘"]),
        "facility": facility,
        "building": building,
        "floor": random.choice(FLOORS),
        "room": f"R-{random.randint(100, 999)}",
        "system_name": system,
        "subsystem": subsystem,
        "manufacturer": random.choice(MANUFACTURERS),
        "model_number": f"MDL-{random.randint(1000, 9999)}",
        "serial_number": f"SN-{random.randint(100000, 999999)}",
        "installation_date": installation_date,
        "inspection_date": inspection_date,
        "next_inspection_date": next_inspection_date,
        "remarks": "" if random.random() > 0.3 else "特記事項あり。詳細は本文参照。",
        "tags": random.sample(keywords, k=min(3, len(keywords))),
    }


def generate_documents(count: int) -> list[dict]:
    """指定数のダミー文書を生成"""
    print(f"📝 {count} 件のダミー文書データを生成中...")
    documents = []
    for i in range(1, count + 1):
        doc = generate_document(i, count)
        documents.append(doc)
    print(f"✅ {count} 件のデータ生成完了")
    return documents


def ingest_to_api(api_url: str, documents: list[dict], batch_size: int = 50) -> None:
    """バックエンドAPIを通じてデータを投入"""
    endpoint = f"{api_url}/api/ingest/documents"
    total = len(documents)
    ingested = 0

    print(f"🚀 データ投入開始: {endpoint}")
    print(f"   バッチサイズ: {batch_size}")

    for i in range(0, total, batch_size):
        batch = documents[i : i + batch_size]
        payload = json.dumps({"documents": batch}).encode("utf-8")

        req = Request(
            endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode("utf-8"))
                ingested += len(batch)
                print(f"   [{ingested}/{total}] バッチ投入成功: {result}")
        except HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else "N/A"
            print(f"   ❌ HTTPエラー {e.code}: {error_body}", file=sys.stderr)
            sys.exit(1)
        except URLError as e:
            print(f"   ❌ 接続エラー: {e.reason}", file=sys.stderr)
            print(f"   💡 バックエンドAPI ({api_url}) が起動しているか確認してください。", file=sys.stderr)
            sys.exit(1)

    print(f"🎉 全 {total} 件のデータ投入が完了しました。")


def export_to_json(documents: list[dict], output_path: str) -> None:
    """生成データをJSONファイルとして出力（APIを使わずに確認したい場合用）"""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"documents": documents}, f, ensure_ascii=False, indent=2)
    print(f"📁 データを {output_path} に出力しました。")


def main():
    parser = argparse.ArgumentParser(
        description="Doc-Graph サンプルデータ生成・投入スクリプト"
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="バックエンドAPIのURL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=50,
        help="生成する文書数 (default: 50)",
    )
    parser.add_argument(
        "--export-only",
        action="store_true",
        help="APIに投入せず、JSONファイルとして出力のみ行う",
    )
    parser.add_argument(
        "--output",
        default="scripts/seed_data.json",
        help="出力先JSONファイルパス (--export-only 時に使用)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="API投入時のバッチサイズ (default: 50)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="乱数シード (default: 42, 再現性確保用)",
    )

    args = parser.parse_args()
    random.seed(args.seed)

    # データ生成
    documents = generate_documents(args.count)

    if args.export_only:
        export_to_json(documents, args.output)
    else:
        # APIに投入
        ingest_to_api(args.api_url, documents, args.batch_size)
        # 投入したデータもJSONとして保存（デバッグ用）
        export_to_json(documents, args.output)

    print("✨ 完了!")


if __name__ == "__main__":
    main()
