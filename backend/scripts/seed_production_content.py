"""把本機開發庫的教學內容搬到生產庫（Phase 7-1a 生產資料播種）。

背景：`concepts` 的 seed migration 用 uuid4() 隨機產生 id，因此生產庫的
concept UUID 與本機不同。`unit_content_staging.concept_id` 必須以 tag 為橋樑
重新映射，其餘三張表無此依賴可直接複製。

用法：
    export TARGET_DB_URL='postgresql://postgres:PASS@HOST:PORT/programing_education'
    python scripts/seed_production_content.py --dry-run   # 先看計畫
    python scripts/seed_production_content.py             # 實際執行
"""

import argparse
import os
import sys

import psycopg2
from psycopg2.extras import Json

SOURCE_DB_URL = os.getenv(
    "SOURCE_DB_URL",
    "postgresql://postgres:postgres@localhost:5432/programing_education",
)

# 無外鍵依賴，可整表直接複製
DIRECT_TABLES = ("documents", "questions")
# 需以 concept tag 重新映射 concept_id
MAPPED_TABLE = "unit_content_staging"
# 由 LlamaIndex 執行期建表，用 pg_dump 連 schema 一起搬（本 script 只驗證）
RAG_TABLE = "data_codedge_rag"


def columns_of(cur, table: str) -> list[str]:
    """取得表的欄位名（依序）。"""
    cur.execute(
        "select column_name from information_schema.columns "
        "where table_schema = 'public' and table_name = %s order by ordinal_position",
        (table,),
    )
    return [r[0] for r in cur.fetchall()]


def json_indexes(cur, table: str, cols: list[str]) -> set[int]:
    """回傳 json/jsonb 欄位在 cols 中的位置。

    psycopg2 讀 JSON 欄位得到 dict/list，直接寫回會被 adapt 成 hstore/array，
    必須以 Json() 包裝才會送出 JSON 字面值。
    """
    cur.execute(
        "select column_name from information_schema.columns "
        "where table_schema = 'public' and table_name = %s and data_type in ('json', 'jsonb')",
        (table,),
    )
    names = {r[0] for r in cur.fetchall()}
    return {i for i, c in enumerate(cols) if c in names}


def wrap_json(row: tuple, indexes: set[int]) -> tuple:
    """把 JSON 欄位的值包成 Json（None 保持原樣）。"""
    if not indexes:
        return row
    return tuple(
        Json(v) if i in indexes and v is not None else v for i, v in enumerate(row)
    )


def count_of(cur, table: str) -> int:
    cur.execute(f'select count(*) from "{table}"')  # noqa: S608 — 表名來自白名單常數
    return cur.fetchone()[0]


def copy_direct(src_cur, dst_cur, table: str, dry_run: bool) -> int:
    """整表複製（欄位以來源為準，目標缺欄位則報錯中止）。"""
    src_cols = columns_of(src_cur, table)
    dst_cols = columns_of(dst_cur, table)
    missing = set(src_cols) - set(dst_cols)
    if missing:
        raise SystemExit(f"[中止] 生產庫 {table} 缺少欄位：{sorted(missing)}（migration 版本不一致？）")

    quoted = ", ".join(f'"{c}"' for c in src_cols)
    src_cur.execute(f'select {quoted} from "{table}"')  # noqa: S608
    rows = src_cur.fetchall()
    if dry_run or not rows:
        return len(rows)

    jidx = json_indexes(src_cur, table, src_cols)
    placeholders = ", ".join(["%s"] * len(src_cols))
    dst_cur.executemany(
        f'insert into "{table}" ({quoted}) values ({placeholders}) '  # noqa: S608
        "on conflict (id) do nothing",
        [wrap_json(r, jidx) for r in rows],
    )
    return len(rows)


def sync_concept_metadata(src_cur, dst_cur, dry_run: bool) -> tuple[int, int]:
    """以 tag 為鍵同步 concepts 的影片 metadata，回傳 (待更新數, 生產缺漏數)。

    migration 把 video_youtube_id seed 成 NULL（6-1d 才由 patch script 寫入本機），
    生產庫因此沒有影片 ID——前端 concept-tab 會 early return 成 placeholder，
    連已灌好的 grounded 教材都不渲染。
    """
    dst_cur.execute("select count(*) from concepts where video_youtube_id is null")
    missing = dst_cur.fetchone()[0]

    src_cur.execute(
        "select tag, video_youtube_id, video_duration_seconds from concepts "
        "where video_youtube_id is not null"
    )
    rows = src_cur.fetchall()
    if rows and not dry_run:
        dst_cur.executemany(
            "update concepts set video_youtube_id = %s, video_duration_seconds = %s "
            "where tag = %s",
            [(yid, dur, tag) for tag, yid, dur in rows],
        )
    return len(rows), missing


def copy_staging_mapped(src_cur, dst_cur, dry_run: bool) -> tuple[int, list[str]]:
    """搬 unit_content_staging，concept_id 依 tag 重新映射到生產庫的 UUID。"""
    cols = columns_of(src_cur, MAPPED_TABLE)
    quoted = ", ".join(f's."{c}"' for c in cols)
    src_cur.execute(
        f"select {quoted}, c.tag from {MAPPED_TABLE} s "  # noqa: S608
        "join concepts c on c.id = s.concept_id where s.status = 'approved'"
    )
    rows = src_cur.fetchall()

    dst_cur.execute("select tag, id from concepts")
    tag_to_id = dict(dst_cur.fetchall())

    concept_idx = cols.index("concept_id")
    payload, unmatched = [], []
    for row in rows:
        tag = row[-1]
        new_id = tag_to_id.get(tag)
        if new_id is None:
            unmatched.append(tag)
            continue
        values = list(row[:-1])
        values[concept_idx] = new_id
        payload.append(tuple(values))

    if payload and not dry_run:
        jidx = json_indexes(src_cur, MAPPED_TABLE, cols)
        col_sql = ", ".join(f'"{c}"' for c in cols)
        placeholders = ", ".join(["%s"] * len(cols))
        dst_cur.executemany(
            f"insert into {MAPPED_TABLE} ({col_sql}) values ({placeholders}) "  # noqa: S608
            "on conflict (id) do nothing",
            [wrap_json(r, jidx) for r in payload],
        )
    return len(payload), unmatched


def main() -> None:
    parser = argparse.ArgumentParser(description="生產環境教學內容播種")
    parser.add_argument("--dry-run", action="store_true", help="只顯示計畫不寫入")
    parser.add_argument("--force", action="store_true", help="目標表已有資料時仍繼續")
    args = parser.parse_args()

    target = os.getenv("TARGET_DB_URL")
    if not target:
        raise SystemExit("[中止] 請先設定環境變數 TARGET_DB_URL")
    if "localhost" in target or "127.0.0.1" in target:
        raise SystemExit("[中止] TARGET_DB_URL 指向本機——方向反了")

    src = psycopg2.connect(SOURCE_DB_URL)
    dst = psycopg2.connect(target)
    src_cur, dst_cur = src.cursor(), dst.cursor()

    # 前置檢查：alembic 建的表必須存在
    for table in ("documents", "questions", MAPPED_TABLE, "concepts"):
        dst_cur.execute("select to_regclass(%s)", (f"public.{table}",))
        if dst_cur.fetchone()[0] is None:
            raise SystemExit(f"[中止] 生產庫找不到表 {table} —— alembic 還沒跑完？")

    # data_codedge_rag 由 LlamaIndex 執行期建立，不在 migration 內：
    # 全新生產庫沒有這張表，需先用 pg_dump 連同 schema 一起搬過去
    dst_cur.execute(f"select to_regclass('public.{RAG_TABLE}')")
    if dst_cur.fetchone()[0] is None:
        raise SystemExit(
            "[中止] 生產庫沒有 data_codedge_rag（LlamaIndex 執行期才建表）。\n"
            "  請先搬這張表（含 schema），再重跑本 script：\n\n"
            "  docker exec codedge-postgres-dev pg_dump -U postgres \\\n"
            "      -d programing_education -t data_codedge_rag --no-owner --no-acl \\\n"
            "      > /tmp/rag.sql\n"
            "  docker exec -i codedge-postgres-dev psql \"$TARGET_DB_URL\" < /tmp/rag.sql\n"
        )

    src_concepts, dst_concepts = count_of(src_cur, "concepts"), count_of(dst_cur, "concepts")
    print(f"concepts：本機 {src_concepts} / 生產 {dst_concepts}（migration seed，不搬）")
    if src_concepts != dst_concepts:
        raise SystemExit("[中止] 兩邊 concepts 數量不同，migration 版本可能不一致")

    src_rag, dst_rag = count_of(src_cur, RAG_TABLE), count_of(dst_cur, RAG_TABLE)
    print(f"{RAG_TABLE}：本機 {src_rag} / 生產 {dst_rag}（pg_dump 搬，不由本 script 處理）")
    if dst_rag != src_rag:
        print(f"  [警告] 筆數不一致——pg_dump 步驟可能沒跑完")

    print(f"\n{'表':24} {'本機':>8} {'生產(前)':>10} {'將寫入':>8}")
    print("-" * 54)
    plan = []
    for table in DIRECT_TABLES:
        before = count_of(dst_cur, table)
        if before and not args.force:
            raise SystemExit(f"[中止] 生產庫 {table} 已有 {before} 筆——加 --force 才會續跑")
        n = copy_direct(src_cur, dst_cur, table, args.dry_run)
        plan.append((table, count_of(src_cur, table), before, n))

    staged, unmatched = copy_staging_mapped(src_cur, dst_cur, args.dry_run)
    plan.append((MAPPED_TABLE, staged, count_of(dst_cur, MAPPED_TABLE), staged))

    for table, s, before, n in plan:
        print(f"{table:24} {s:>8} {before:>10} {n:>8}")

    synced, missing = sync_concept_metadata(src_cur, dst_cur, args.dry_run)
    print(f"\nconcepts 影片 metadata：生產原本 {missing} 筆缺 video_youtube_id → 同步 {synced} 筆")

    if unmatched:
        print(f"\n[警告] {len(unmatched)} 個 concept tag 在生產庫找不到：{unmatched[:5]}")

    if args.dry_run:
        print("\n[dry-run] 未寫入任何資料")
        dst.rollback()
    else:
        dst.commit()
        print("\n完成。生產庫現況：")
        for table in (*DIRECT_TABLES, MAPPED_TABLE):
            print(f"  {table:24} {count_of(dst_cur, table):>8}")
        dst_cur.execute("select count(*) from concepts where video_youtube_id is not null")
        print(f"  {'concepts(有影片ID)':24} {dst_cur.fetchone()[0]:>8}")

    src.close()
    dst.close()


if __name__ == "__main__":
    sys.exit(main())
