import pytest

import run_server


def test_find_available_port_skips_occupied_ports(monkeypatch) -> None:
    monkeypatch.setattr(
        run_server,
        "is_port_available",
        lambda _host, port: port == 8002,
    )

    assert run_server.find_available_port(start_port=8000, search_count=5) == 8002


def test_find_available_port_reports_exhausted_range(monkeypatch) -> None:
    monkeypatch.setattr(run_server, "is_port_available", lambda *_: False)

    with pytest.raises(RuntimeError, match="端口 8000 到 8002 都已被占用"):
        run_server.find_available_port(start_port=8000, search_count=3)


def test_argument_parser_uses_safe_defaults() -> None:
    arguments = run_server.build_argument_parser().parse_args([])

    assert arguments.host == "127.0.0.1"
    assert arguments.port == 8000
    assert arguments.reload is False
