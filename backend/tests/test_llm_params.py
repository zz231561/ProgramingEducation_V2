"""core/llm_params.py 相容層測試（6-M1 實機驗證後新增）。

規則依 2026-07-06 實測：
- gpt-5 reasoning 系列拒收自訂 temperature → 省略 + reasoning_effort=minimal
- 全 gpt-5 世代拒收 max_tokens → 一律用 max_completion_tokens
"""

from core.llm_params import chat_model_kwargs


class TestChatModelKwargs:
    def test_standard_model_keeps_temperature(self):
        kwargs = chat_model_kwargs(model="gpt-5.4-mini", temperature=0.3, max_tokens=200)
        assert kwargs == {
            "model": "gpt-5.4-mini",
            "temperature": 0.3,
            "max_completion_tokens": 200,
        }

    def test_reasoning_model_drops_temperature_adds_minimal_effort(self):
        kwargs = chat_model_kwargs(model="gpt-5-mini", temperature=0.7, max_tokens=900)
        assert kwargs == {
            "model": "gpt-5-mini",
            "reasoning_effort": "minimal",
            "max_completion_tokens": 900,
        }

    def test_gpt5_exact_is_reasoning_family(self):
        kwargs = chat_model_kwargs(model="gpt-5", temperature=0.5)
        assert "temperature" not in kwargs
        assert kwargs["reasoning_effort"] == "minimal"

    def test_gpt54_is_not_reasoning_family(self):
        kwargs = chat_model_kwargs(model="gpt-5.4", temperature=0.2, max_tokens=500)
        assert kwargs["temperature"] == 0.2
        assert "reasoning_effort" not in kwargs

    def test_no_max_tokens_omits_limit(self):
        kwargs = chat_model_kwargs(model="gpt-4o", temperature=0.3)
        assert kwargs == {"model": "gpt-4o", "temperature": 0.3}

    def test_gen56_drops_temperature_adds_none_effort(self):
        # 2026-08-06 更正：gpt-5.6 值域是 none/low/…（不收 minimal）；
        # 預設會浮動燒 reasoning tokens（同 prompt 0～96+ 顆），
        # 不壓制曾造成 reflection 評分整包空輸出被靜默吞掉
        for model in ("gpt-5.6-luna", "gpt-5.6-terra", "gpt-5.6-sol"):
            kwargs = chat_model_kwargs(model=model, temperature=0.3, max_tokens=400)
            assert kwargs == {
                "model": model,
                "reasoning_effort": "none",
                "max_completion_tokens": 400,
            }
