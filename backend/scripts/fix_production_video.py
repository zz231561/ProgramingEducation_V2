"""把單一 video 的教學內容修正同步到生產庫（2026-08-05 v41 `extern` 事件）。

用途：教材/題庫在本機修正後，只重播該章而不動其他章節。
`seed_production_content.py` 是 `on conflict do nothing` 的初次播種，無法更新既有資料。

用法：
    export TARGET_DB_URL='postgresql://...'
    python -m scripts.fix_production_video --video 41 --dry-run
    python -m scripts.fix_production_video --video 41
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


def fetch_one(cur, sql: str, params: tuple = ()) -> tuple:
    cur.execute(sql, params)
    row = cur.fetchone()
    return row if row else (None,)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", type=int, required=True, help="video_order")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    target = os.getenv("TARGET_DB_URL")
    if not target:
        raise SystemExit("[中止] 請先設定 TARGET_DB_URL")
    if "localhost" in target or "127.0.0.1" in target:
        raise SystemExit("[中止] TARGET_DB_URL 指向本機——方向反了")

    src = psycopg2.connect(SOURCE_DB_URL)
    dst = psycopg2.connect(target)
    s, d = src.cursor(), dst.cursor()

    (tag,) = fetch_one(s, "select tag from concepts where video_order=%s", (args.video,))
    if tag is None:
        raise SystemExit(f"[中止] 本機找不到 video_order={args.video}")
    (dst_concept,) = fetch_one(d, "select id from concepts where tag=%s", (tag,))
    if dst_concept is None:
        raise SystemExit(f"[中止] 生產庫找不到 tag={tag}")
    print(f"目標章節：v{args.video} {tag}")

    # 1) RAG chunks（本機為正本，整章替換）
    s.execute(
        "select text, metadata_, node_id, embedding from data_codedge_rag "
        "where metadata_->>'video_order' = %s",
        (str(args.video),),
    )
    chunks = s.fetchall()
    d.execute(
        "select count(*) from data_codedge_rag where metadata_->>'video_order' = %s",
        (str(args.video),),
    )
    print(f"  RAG chunks：生產 {d.fetchone()[0]} → 換成本機 {len(chunks)} 筆")

    # 2) staging content
    s.execute(
        "select content, status from unit_content_staging s "
        "join concepts c on c.id=s.concept_id where c.tag=%s",
        (tag,),
    )
    staging = s.fetchone()

    # 3) questions
    s.execute(
        "select id, type, concept_tags, bloom_level, difficulty, content, "
        "explanation, source, validated from questions "
        "where concept_tags::text like %s",
        (f"%{tag}%",),
    )
    questions = s.fetchall()
    d.execute(
        "select count(*) from questions where concept_tags::text like %s", (f"%{tag}%",)
    )
    print(f"  questions：生產 {d.fetchone()[0]} → 換成本機 {len(questions)} 題")

    if args.dry_run:
        print("\n[dry-run] 未寫入任何資料")
        return

    # --- 實際寫入 ---
    d.execute(
        "delete from data_codedge_rag where metadata_->>'video_order' = %s",
        (str(args.video),),
    )
    for text, meta, node_id, emb in chunks:
        d.execute(
            "insert into data_codedge_rag (text, metadata_, node_id, embedding) "
            "values (%s,%s,%s,%s)",
            (text, Json(meta), node_id, emb),
        )

    d.execute(
        "update unit_content_staging set content=%s, status=%s where concept_id=%s",
        (Json(staging[0]), staging[1], dst_concept),
    )
    d.execute(
        "update learning_units set content=%s where concept_id=%s",
        (Json(staging[0]), dst_concept),
    )

    d.execute(
        "delete from student_answers where question_id in "
        "(select id from questions where concept_tags::text like %s)",
        (f"%{tag}%",),
    )
    d.execute("delete from questions where concept_tags::text like %s", (f"%{tag}%",))
    for q in questions:
        d.execute(
            "insert into questions (id,type,concept_tags,bloom_level,difficulty,"
            "content,explanation,source,validated) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (q[0], q[1], Json(q[2]), q[3], q[4], Json(q[5]), q[6], q[7], q[8]),
        )

    dst.commit()
    print("\n完成。生產庫現況：")
    for label, sql, params in [
        ("RAG chunks", "select count(*) from data_codedge_rag where metadata_->>'video_order'=%s", (str(args.video),)),
        ("questions", "select count(*) from questions where concept_tags::text like %s", (f"%{tag}%",)),
        ("含 external 殘留", "select count(*) from questions where content::text like %s", ("%external%",)),
    ]:
        d.execute(sql, params)
        print(f"  {label:20} {d.fetchone()[0]}")

    src.close()
    dst.close()


if __name__ == "__main__":
    sys.exit(main())
