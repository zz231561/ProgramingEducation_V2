"""LLM chat completion 參數相容層（6-M1 實機驗證後新增）。

設計意圖：gpt-5 世代模型的參數規則與 gpt-4o 不同，實測（2026-07-06）：
- 全系列拒收 `max_tokens`，必須改用 `max_completion_tokens`（gpt-4o 兩者皆收）
- reasoning 系列（gpt-5 / gpt-5-mini / gpt-5-nano）只接受預設 temperature=1，
  且預設會把 completion 預算燒在 reasoning 上導致空輸出——
  必須 `reasoning_effort="minimal"`（實測 minimal → 0 reasoning tokens、正常輸出）
- gpt-5.4 / gpt-5.4-mini 接受自訂 temperature，行為同傳統模型
- gpt-5.6 世代（sol / terra / luna，2026-08-05 實測）：拒收自訂 temperature，
  **也拒收 `reasoning_effort`**；預設 reasoning_tokens=0，無須壓制

集中此處判斷，13 個呼叫點統一經由 `chat_model_kwargs()` 組參數。
"""

from __future__ import annotations

from typing import Any

# reasoning 系列：gpt-5 本體與 gpt-5-* 衍生（gpt-5.4 系列不屬之）
_REASONING_PREFIX = "gpt-5-"
_REASONING_EXACT = "gpt-5"
# gpt-5.6 世代（sol / terra / luna）：同樣拒收自訂 temperature，
# 但**也拒收 reasoning_effort**，且預設 reasoning_tokens=0 不需壓制（2026-08-05 實測）
_GEN56_PREFIX = "gpt-5.6"


def _is_reasoning_family(model: str) -> bool:
    """判斷是否需要 `reasoning_effort=minimal` 壓制 reasoning 預算。"""
    return model == _REASONING_EXACT or model.startswith(_REASONING_PREFIX)


def _accepts_custom_temperature(model: str) -> bool:
    """判斷是否接受自訂 temperature（gpt-5 與 gpt-5.6 世代皆只收預設值）。"""
    return not (_is_reasoning_family(model) or model.startswith(_GEN56_PREFIX))


def chat_model_kwargs(
    *, model: str, temperature: float, max_tokens: int | None = None
) -> dict[str, Any]:
    """組出 chat.completions.create 的模型相關 kwargs。

    Args:
        model: 模型 ID（來自 settings 的 6-M 路由）。
        temperature: 期望溫度；reasoning 系列不支援時自動省略。
        max_tokens: 期望輸出上限；None 表示不設限。

    Returns:
        可直接 `**` 展開進 create() 的 dict。
    """
    kwargs: dict[str, Any] = {"model": model}
    if _is_reasoning_family(model):
        kwargs["reasoning_effort"] = "minimal"
    if _accepts_custom_temperature(model):
        kwargs["temperature"] = temperature
    if max_tokens is not None:
        kwargs["max_completion_tokens"] = max_tokens
    return kwargs
