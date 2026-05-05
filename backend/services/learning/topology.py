"""拓撲排序（priority Kahn's algorithm）— 純函式，無 DB / 框架依賴（roadmap 3-1b）。

設計：
- 邊語意：(src, tgt) 表示「學 tgt 前要先學 src」（src 是 tgt 的 prerequisite）
- 弱項優先：in-degree=0 的可選節點中，依 priority（confidence）升序選擇
  → 學生未練 / 弱項（confidence 低）會排在前面，已熟練的延後
- 穩定性：priority 相同 → 用插入順序（counter）破除 tie，輸出可重現
- Cycle 容錯：拓撲完成後若仍有節點殘留（必為 cycle 一員）→ 按 priority 升序附加到尾端
  避免擲錯（PREREQUISITE 理論上不該有 cycle，但容錯比硬報錯實用）

效能：O((N+E) log N)；對 N < 500 的概念數綽綽有餘。
"""

import heapq
from typing import TypeVar

T = TypeVar("T")


def topological_sort_with_priority(
    nodes: list[T],
    edges: list[tuple[T, T]],
    priority: dict[T, float],
    default_priority: float = 0.0,
) -> list[T]:
    """priority Kahn's 拓撲排序：拓撲安全 + 弱項優先。

    Args:
        nodes: 待排序節點列表（保留輸入順序作為 stable tie-breaker）
        edges: prerequisite 邊 (src, tgt)；src 為 tgt 的前置
        priority: {node: priority}；數值越小越優先（學生 confidence 低 = 弱項 = 先學）
        default_priority: 不在 priority 中的節點預設值（cold start 通常 0.0）

    Returns:
        排序後節點列表（前置節點必在依賴節點之前；同層優先排弱項）
    """
    in_degree: dict[T, int] = {n: 0 for n in nodes}
    adj: dict[T, list[T]] = {n: [] for n in nodes}
    node_set = set(nodes)

    for src, tgt in edges:
        # 忽略指向 nodes 集合外的邊（filter 後可能有殘邊）
        if src in node_set and tgt in node_set:
            adj[src].append(tgt)
            in_degree[tgt] += 1

    # heap 元素：(priority, insertion_counter, node)
    # counter 保證穩定性 + 避免比較 node 物件
    counter = 0
    heap: list[tuple[float, int, T]] = []
    for n in nodes:
        if in_degree[n] == 0:
            heapq.heappush(heap, (priority.get(n, default_priority), counter, n))
            counter += 1

    result: list[T] = []
    while heap:
        _, _, n = heapq.heappop(heap)
        result.append(n)
        for m in adj[n]:
            in_degree[m] -= 1
            if in_degree[m] == 0:
                heapq.heappush(heap, (priority.get(m, default_priority), counter, m))
                counter += 1

    # Cycle 容錯：殘留節點按 priority 升序附加
    if len(result) < len(nodes):
        produced = set(result)
        remaining = [n for n in nodes if n not in produced]
        remaining.sort(key=lambda n: (priority.get(n, default_priority), nodes.index(n)))
        result.extend(remaining)

    return result
