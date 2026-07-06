"""6-M1 分組模型環境變數 fallback 邏輯測試。

設計意圖：分組變數（GENERATE / VALIDATE / CONTENT）未設定時
一律 fallback LLM_MODEL，確保單一模型時代的行為完全不變。
"""

from core.config import Settings


def _make_settings(**overrides) -> Settings:
    """建立不讀 .env 的 Settings 實例，只吃顯式參數。"""
    return Settings(_env_file=None, **overrides)


class TestLlmModelRouting:
    def test_unset_groups_fallback_to_llm_model(self):
        s = _make_settings(LLM_MODEL="base-model")
        assert s.llm_model_generate == "base-model"
        assert s.llm_model_validate == "base-model"
        assert s.llm_model_content == "base-model"

    def test_set_groups_override_llm_model(self):
        s = _make_settings(
            LLM_MODEL="base-model",
            LLM_MODEL_GENERATE="gen-model",
            LLM_MODEL_VALIDATE="val-model",
            LLM_MODEL_CONTENT="content-model",
        )
        assert s.llm_model_generate == "gen-model"
        assert s.llm_model_validate == "val-model"
        assert s.llm_model_content == "content-model"

    def test_partial_override_mixes_correctly(self):
        s = _make_settings(LLM_MODEL="base-model", LLM_MODEL_VALIDATE="val-model")
        assert s.llm_model_generate == "base-model"
        assert s.llm_model_validate == "val-model"
        assert s.llm_model_content == "base-model"
