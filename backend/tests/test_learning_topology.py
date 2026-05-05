"""拓撲排序 unit tests（roadmap 3-1b）— 純函式，無 DB 依賴。

涵蓋：
- 空圖 / 單節點 / 線性鏈 / 多分支
- 弱項優先（priority 低先排）
- 同優先級 → 插入順序穩定
- 拓撲約束維持（前置一定在依賴之前）
- Cycle 容錯（殘留節點按 priority 附加尾端）
- edges 指向圖外節點 → 忽略不擲錯
"""

from services.learning.topology import topological_sort_with_priority


def test_empty_graph_returns_empty():
    assert topological_sort_with_priority([], [], {}) == []


def test_single_node():
    assert topological_sort_with_priority(["a"], [], {"a": 0.5}) == ["a"]


def test_linear_chain_respects_order():
    """a → b → c → d；輸出必為 a, b, c, d。"""
    nodes = ["d", "a", "c", "b"]  # 故意亂順
    edges = [("a", "b"), ("b", "c"), ("c", "d")]
    result = topological_sort_with_priority(nodes, edges, {})
    assert result == ["a", "b", "c", "d"]


def test_priority_orders_independent_nodes():
    """無依賴的 a/b/c → 按 confidence 升序（弱項先學）。"""
    result = topological_sort_with_priority(
        nodes=["a", "b", "c"],
        edges=[],
        priority={"a": 0.9, "b": 0.1, "c": 0.5},
    )
    assert result == ["b", "c", "a"]


def test_priority_within_topological_layer():
    """a → b, a → c；先 a 再 (b, c)；b/c 內按 priority。"""
    result = topological_sort_with_priority(
        nodes=["a", "b", "c"],
        edges=[("a", "b"), ("a", "c")],
        priority={"a": 0.5, "b": 0.8, "c": 0.2},
    )
    assert result[0] == "a"
    # b/c 順序：c (0.2) 先於 b (0.8)
    assert result[1:] == ["c", "b"]


def test_priority_does_not_violate_topology():
    """即使 b 是弱項，a 是 b 的前置 → a 必先於 b。"""
    result = topological_sort_with_priority(
        nodes=["a", "b"],
        edges=[("a", "b")],
        priority={"a": 0.9, "b": 0.0},
    )
    assert result == ["a", "b"]


def test_default_priority_for_unmapped():
    """未在 priority 中的節點用 default_priority；cold start 0.0 → 排前。"""
    result = topological_sort_with_priority(
        nodes=["practiced", "fresh"],
        edges=[],
        priority={"practiced": 0.7},  # fresh 不在 map
        default_priority=0.0,
    )
    assert result == ["fresh", "practiced"]


def test_stable_tie_breaker_preserves_input_order():
    """priority 相同時用插入順序破除 tie。"""
    result = topological_sort_with_priority(
        nodes=["a", "b", "c"],
        edges=[],
        priority={"a": 0.5, "b": 0.5, "c": 0.5},
    )
    assert result == ["a", "b", "c"]


def test_diamond_graph():
    """a → b, a → c, b → d, c → d；多種合法排序，驗證拓撲性質。"""
    result = topological_sort_with_priority(
        nodes=["a", "b", "c", "d"],
        edges=[("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")],
        priority={},
    )
    # 拓撲約束
    assert result.index("a") < result.index("b")
    assert result.index("a") < result.index("c")
    assert result.index("b") < result.index("d")
    assert result.index("c") < result.index("d")


def test_cycle_nodes_appended_to_tail():
    """a → b → a 形成 cycle；剩餘節點 (a, b) 按 priority 附加。"""
    result = topological_sort_with_priority(
        nodes=["a", "b", "c"],
        edges=[("a", "b"), ("b", "a")],
        priority={"a": 0.5, "b": 0.1, "c": 0.0},
    )
    # c 無依賴 → 先排
    assert result[0] == "c"
    # a/b 在 cycle 中 → 附加尾端，按 priority：b (0.1) 先於 a (0.5)
    assert set(result[1:]) == {"a", "b"}


def test_edges_referencing_external_nodes_ignored():
    """edges 指向 nodes 集合外的節點 → 忽略不擲錯（filter 後常見）。"""
    result = topological_sort_with_priority(
        nodes=["a", "b"],
        edges=[("a", "b"), ("external", "a"), ("b", "external")],
        priority={},
    )
    assert result == ["a", "b"]


def test_multiple_independent_chains():
    """兩條獨立鏈：x → y, p → q；priority 決定誰先。"""
    result = topological_sort_with_priority(
        nodes=["x", "y", "p", "q"],
        edges=[("x", "y"), ("p", "q")],
        priority={"x": 0.5, "p": 0.1},  # p 弱，先學
    )
    assert result.index("p") < result.index("x")
    assert result.index("x") < result.index("y")
    assert result.index("p") < result.index("q")
