"""Coddy 多型學生模擬驗收 harness（7-C 診斷輪 / 驗證輪共用）。

以真實 HTTP API + 真實 LLM 跑七型學生腳本，同步收集 DEV-7 debug_sink
（evidence / strategy / RAG 分數 / kgraph）與 DB 探針（dialogue_act /
mastery 差分 / coding_events），輸出逐輪 transcript 供人工分析。

僅限本機 DB（scripts._db_guard.require_local_db）。
"""
