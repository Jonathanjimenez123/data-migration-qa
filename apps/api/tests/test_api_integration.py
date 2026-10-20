from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_rejects_unsupported_file_extension():
    source = b"id,nombre\n1,Ana\n"
    target = b"id,nombre\n1,Ana\n"

    response = client.post(
        "/api/v1/reconciliation/files",
        files={
            "source_file": ("origen.txt", source, "text/plain"),
            "target_file": ("destino.csv", target, "text/csv"),
        },
        data={"key_column": "id"},
    )

    assert response.status_code == 422


def test_reconciliation_is_saved_and_queryable():
    source = b"id,nombre,saldo\n1,Ana,100\n2,Carlos,200\n"
    target = b"id,nombre,saldo\n1,Ana,100\n2,Carlos,180\n3,Luisa,300\n"

    response = client.post(
        "/api/v1/reconciliation/files",
        files={
            "source_file": ("origen.csv", source, "text/csv"),
            "target_file": ("destino.csv", target, "text/csv"),
        },
        data={"key_column": "id"},
    )

    assert response.status_code == 200, response.text

    result = response.json()
    run_id = result["run_id"]

    assert isinstance(run_id, int)
    assert result["status"] == "FAIL"
    assert result["summary"]["unexpected_records"] == 1
    assert result["summary"]["field_differences"] == 1

    # Verificar que la ejecucion se puede recuperar de PostgreSQL.
    detail_response = client.get(f"/api/v1/runs/{run_id}")

    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["id"] == run_id

    check_names = {check["name"] for check in detail["checks"]}
    assert "FIELD_DIFFERENCES" in check_names

    differences = detail["differences"]
    assert any(
        difference["column_name"] == "saldo"
        for difference in differences
    )

    # Verificar que la ejecucion aparece en el historial.
    history_response = client.get("/api/v1/runs")

    assert history_response.status_code == 200
    history = history_response.json()
    assert any(item["id"] == run_id for item in history["items"])


def test_run_inexistente_devuelve_404(monkeypatch):
    import app.routers.runs as runs_router

    monkeypatch.setattr(runs_router, "get_run", lambda run_id: None)

    response = client.get("/api/v1/runs/999999")

    assert response.status_code == 404


def test_run_id_invalido_devuelve_422():
    response = client.get("/api/v1/runs/0")

    assert response.status_code == 422


def test_archivo_demasiado_grande_devuelve_413(monkeypatch):
    import app.routers.reconciliation as reconciliation_router

    monkeypatch.setattr(reconciliation_router, "MAX_FILE_BYTES", 32)

    source = b"id,nombre\n1,Este contenido supera el limite\n"
    target = b"id,nombre\n1,Ana\n"

    response = client.post(
        "/api/v1/reconciliation/files",
        files={
            "source_file": ("origen.csv", source, "text/csv"),
            "target_file": ("destino.csv", target, "text/csv"),
        },
        data={"key_column": "id"},
    )

    assert response.status_code == 413
