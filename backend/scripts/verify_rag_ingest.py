"""2-1b 驗證腳本 — 跑一份範例教材檢查 IngestionPipeline 端到端可用。

用法：
    cd backend
    .venv/bin/python -m scripts.verify_rag_ingest

驗收標準（roadmap 2-1b）：
    SELECT count(*) FROM data_codedge_rag > 0
"""

import asyncio
from uuid import uuid4

from sqlalchemy import text as sa_text

from core.database import async_session
from services.rag import VECTOR_TABLE_NAME, ingest_document

SAMPLE_TEXT = """\
C++ 指標基礎

指標（pointer）是儲存記憶體位址的變數。在 C++ 中，宣告指標的語法如下：

    int x = 42;
    int* p = &x;  // p 指向 x 的位址

解引用（dereference）使用 `*` 運算子取得指標所指位址中的值：

    std::cout << *p;  // 輸出 42

注意：對未初始化或 nullptr 的指標解引用會造成 undefined behavior，
是 C++ 中最常見的執行期錯誤之一。建議：
1. 宣告時初始化為 nullptr
2. 解引用前用 `if (p != nullptr)` 檢查
3. 使用智慧指標（std::unique_ptr / std::shared_ptr）取代裸指標
"""


async def main() -> None:
    doc_id = uuid4()
    actual_table = f"data_{VECTOR_TABLE_NAME}"

    async with async_session() as db:
        # 1) 建立 documents 行（模擬已上傳教材）
        await db.execute(
            sa_text(
                """
                INSERT INTO documents (id, source, title, version)
                VALUES (:id, 'manual', :title, 1)
                """
            ).bindparams(id=doc_id, title="C++ 指標基礎（驗證用）")
        )
        await db.commit()
        print(f"[1/3] documents row created — id={doc_id}")

        # 2) 跑 ingest pipeline
        node_count = await ingest_document(db, doc_id, SAMPLE_TEXT)
        print(f"[2/3] ingest_document done — {node_count} chunks emitted")

        # 3) 驗證向量表內有資料
        result = await db.execute(
            sa_text(f"SELECT count(*) FROM {actual_table}")  # noqa: S608
        )
        total = result.scalar_one()
        print(f"[3/3] {actual_table} count = {total}")

        if total > 0:
            print(f"\n✅ 2-1b 驗證通過：向量表 {actual_table} 寫入 {total} 筆")
        else:
            print(f"\n❌ 2-1b 驗證失敗：向量表 {actual_table} 為空")
            raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
