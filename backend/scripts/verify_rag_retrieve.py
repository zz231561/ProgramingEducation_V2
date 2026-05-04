"""2-1c 驗證腳本 — 用既有 data_codedge_rag 測試檢索 service 端到端可用。

前置：先跑 `verify_rag_ingest.py` 至少一次（向量表需有資料）。

用法：
    cd backend
    .venv/bin/python -m scripts.verify_rag_retrieve

驗收標準：
    - 對「nullptr 解引用會發生什麼？」做檢索，回傳 >= 1 筆 chunk
    - 每筆 chunk 含 text / score / doc_id（來自 ingest metadata）
"""

import asyncio

from services.rag import retrieve_chunks

QUERY = "對 nullptr 解引用會發生什麼？要怎麼避免？"
TOP_K = 3


async def main() -> None:
    print(f"[query] {QUERY}\n")
    chunks = await retrieve_chunks(QUERY, top_k=TOP_K)

    if not chunks:
        print("❌ 2-1c 驗證失敗：retrieve_chunks 回傳空 list")
        raise SystemExit(1)

    for i, c in enumerate(chunks, 1):
        preview = c.text.replace("\n", " ")[:80]
        print(f"[{i}/{len(chunks)}] score={c.score:.4f}  doc_id={c.doc_id}")
        print(f"        text={preview}...\n")

    print(f"✅ 2-1c 驗證通過：top-{TOP_K} 共回傳 {len(chunks)} 筆 chunks（依相似度排序）")


if __name__ == "__main__":
    asyncio.run(main())
