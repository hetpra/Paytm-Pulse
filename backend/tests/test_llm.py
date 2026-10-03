import app.llm as llm


def _compat_env(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai_compat")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("LLM_API_KEY", "test-key")


def test_complete_compat_success(monkeypatch):
    _compat_env(monkeypatch)
    monkeypatch.setattr(llm, "_post_json", lambda *args: {"choices": [{"message": {"content": "ok"}}]})
    assert llm.complete("system", "user") == "ok"


def test_complete_timeout_returns_none(monkeypatch):
    _compat_env(monkeypatch)
    monkeypatch.setattr(llm, "_post_json", lambda *args: (_ for _ in ()).throw(llm.TransportError("timeout")))
    assert llm.complete("system", "user") is None


def test_complete_retries_429(monkeypatch):
    _compat_env(monkeypatch)
    calls = {"count": 0}
    def fake_post(*args):
        calls["count"] += 1
        if calls["count"] == 1:
            raise llm.TransportError("limited", 429)
        return {"choices": [{"message": {"content": "retried"}}]}
    monkeypatch.setattr(llm, "_post_json", fake_post)
    monkeypatch.setattr(llm.time, "sleep", lambda _: None)
    assert llm.complete("system", "user") == "retried"
    assert calls["count"] == 2


def test_json_mode_rejects_malformed_response(monkeypatch):
    _compat_env(monkeypatch)
    monkeypatch.setattr(llm, "_post_json", lambda *args: {"choices": [{"message": {"content": "not-json"}}]})
    assert llm.complete("system", "user", json_mode=True) is None


def test_none_provider_returns_none(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "none")
    assert llm.complete("system", "user") is None
