from app.core.config import Settings


def test_settings_when_env_values_given_reads_them(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("LLM_MODEL", "some-model")
    monkeypatch.setenv("LLM_API_KEY", "secret")
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.llm_model == "some-model"
    assert settings.llm_api_key.get_secret_value() == "secret"


def test_settings_when_printed_hides_secrets(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("DEEPGRAM_API_KEY", "super-secret")
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert "super-secret" not in repr(settings)
