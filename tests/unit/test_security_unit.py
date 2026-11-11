"""5.1: límite de intentos y secreto JWT (sin base de datos)."""

from escudo_api.security import LoginThrottle


def test_throttle_window_and_success_reset():
    t = LoginThrottle()
    for i in range(10):
        assert t.retry_after("a@x", "1.1.1.1", 1000 + i) is None
        t.fail("a@x", "1.1.1.1", 1000 + i)
    assert t.retry_after("a@x", "1.1.1.1", 1011) > 0
    assert t.retry_after("a@x", "1.1.1.1", 1000 + t.WINDOW_S + 20) is None  # la ventana caduca
    for i in range(10):
        t.fail("b@x", "2.2.2.2", 5000 + i)
    t.success("b@x")
    assert t.retry_after("b@x", "2.2.2.2", 5011) is None


def test_ip_limit_blocks_spraying_many_emails():
    t = LoginThrottle()
    for i in range(t.MAX_PER_IP):
        t.fail(f"u{i}@x", "3.3.3.3", 100 + i)
    assert t.retry_after("nuevo@x", "3.3.3.3", 200) > 0
    assert t.retry_after("nuevo@x", "4.4.4.4", 200) is None


def test_published_example_secret_is_never_used(monkeypatch):
    import importlib

    import escudo_api.config as cfg

    monkeypatch.setenv("ESCUDO_JWT_SECRET", "dev-only-change-me")
    mod = importlib.reload(cfg)
    try:
        assert mod.JWT_SECRET_EPHEMERAL and mod.settings.escudo_jwt_secret != "dev-only-change-me"
        assert len(mod.settings.escudo_jwt_secret) >= 32
    finally:
        monkeypatch.undo()
        importlib.reload(cfg)
