"""5.1: límite de intentos de login (atómico, sin bloqueo dirigido) y secreto JWT (sin base de datos)."""

import threading

from escudo_api.security import LoginThrottle


def test_pair_limit_window_and_release():
    t = LoginThrottle()
    for i in range(t.MAX_PER_PAIR):
        assert t.reserve("a@x", "1.1.1.1", 1000 + i) is None  # cada reserva cuenta como intento
    assert t.reserve("a@x", "1.1.1.1", 1011) > 0
    assert t.reserve("a@x", "1.1.1.1", 1000 + t.WINDOW_S + 20) is None  # la ventana caduca
    t.reset()
    for i in range(5):
        t.reserve("b@x", "2.2.2.2", 5000 + i)
    t.release("b@x", "2.2.2.2", 5004)  # acceso correcto: limpia el par
    assert t.retry_after("b@x", "2.2.2.2", 5010) is None


def test_no_targeted_lockout_from_another_ip():
    """Un tercero que falla 10 veces con el email de la gestora no la bloquea desde la conexión de ella."""
    t = LoginThrottle()
    for i in range(t.MAX_PER_PAIR):
        t.reserve("gestora@x", "6.6.6.6", 100 + i)
    assert t.reserve("gestora@x", "6.6.6.6", 120) > 0
    assert t.reserve("gestora@x", "7.7.7.7", 120) is None


def test_ip_limit_blocks_spraying_many_emails():
    t = LoginThrottle()
    for i in range(t.MAX_PER_IP):
        t.reserve(f"u{i}@x", "3.3.3.3", 100 + i)
    assert t.reserve("nuevo@x", "3.3.3.3", 200) > 0
    assert t.reserve("nuevo@x", "4.4.4.4", 200) is None


def test_reservation_is_atomic_under_concurrency():
    """100 intentos simultáneos desde el mismo par: solo MAX_PER_PAIR pasan el límite."""
    t = LoginThrottle()
    passed = []
    barrier = threading.Barrier(100)

    def go():
        barrier.wait()
        if t.reserve("c@x", "5.5.5.5", 1000.0) is None:
            passed.append(1)

    threads = [threading.Thread(target=go) for _ in range(100)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    assert len(passed) == t.MAX_PER_PAIR


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


def test_decompression_bomb_is_rejected_before_decoding():
    import io

    import pytest
    from fastapi import HTTPException
    from PIL import Image

    from escudo_api.routers.private import _strip_image_metadata

    b = io.BytesIO()
    Image.new("1", (9000, 9000), 0).save(b, "PNG")  # 81 MP que ocupan unos pocos KB comprimidos
    assert len(b.getvalue()) < 200_000
    with pytest.raises(HTTPException) as e:
        _strip_image_metadata(b.getvalue(), "image/png")
    assert e.value.status_code == 413


def test_global_per_account_cap_stops_distributed_brute_force():
    t = LoginThrottle()
    for i in range(t.MAX_PER_EMAIL):
        assert t.reserve("victima@x", f"10.0.{i // 250}.{i % 250}", 100 + i * 0.01) is None  # 1 intento por IP
    assert t.reserve("victima@x", "10.9.9.9", 102) > 0


def test_ipv6_grouped_by_64():
    t = LoginThrottle()
    for i in range(t.MAX_PER_PAIR):
        t.reserve("a@x", f"2001:db8:1:2::{i + 1:x}", 100 + i)
    assert t.reserve("a@x", "2001:db8:1:2::ffff", 120) > 0  # mismo /64
    assert t.reserve("a@x", "2001:db8:1:3::1", 120) is None  # otro /64
