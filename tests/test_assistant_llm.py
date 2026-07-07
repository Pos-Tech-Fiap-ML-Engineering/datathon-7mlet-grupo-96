import pytest

from bandit_platform.assistant.llm import get_chat_model


def test_get_chat_model_raises_clear_error_without_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr("bandit_platform.assistant.llm.dotenv.load_dotenv", lambda *a, **kw: None)

    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        get_chat_model()


def test_get_chat_model_returns_client_when_key_present(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key-for-test")

    model = get_chat_model()

    assert model is not None
