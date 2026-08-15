from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_dockerfile_runs_as_non_root_with_healthcheck() -> None:
    content = (PROJECT_ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "FROM python:3.12-slim" in content
    assert "USER appuser" in content
    assert "HEALTHCHECK" in content
    assert "app.main:app" in content
    assert '"--host", "0.0.0.0"' in content
    assert "requirements-prod.txt" in content
    assert "COPY ." not in content


def test_compose_persists_database_and_avoids_common_host_ports() -> None:
    content = (PROJECT_ROOT / "compose.yaml").read_text(encoding="utf-8")

    assert "${APP_HOST_PORT:-8080}:8000" in content
    assert "sqlite:////app/data/ecommerce.db" in content
    assert "ecommerce_data:/app/data" in content
    assert "healthcheck:" in content


def test_docker_context_excludes_secrets_and_local_data() -> None:
    entries = {
        line.strip()
        for line in (PROJECT_ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()
        if line.strip()
    }

    assert ".env" in entries
    assert ".venv" in entries
    assert ".git" in entries
    assert "data" in entries
    assert "*.db" in entries
