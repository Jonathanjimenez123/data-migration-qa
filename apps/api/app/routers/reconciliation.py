"""Endpoints para reconciliar archivos y registrar ejecuciones de QA."""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.database import save_run
from app.services.reconciliation import (
    MAX_FILE_BYTES,
    ReconciliationError,
    reconcile_tables,
)

router = APIRouter(
    prefix="/api/v1/reconciliation",
    tags=["Reconciliation"],
)


async def _read_limited(file: UploadFile) -> bytes:
    """Lee un archivo sin superar el límite establecido."""
    content = await file.read(MAX_FILE_BYTES + 1)

    if len(content) > MAX_FILE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"El archivo {file.filename} supera el límite de 10 MB.",
        )

    return content


@router.post("/files")
async def compare_files(
    source_file: UploadFile = File(
        ...,
        description="Archivo de origen CSV o XLSX",
    ),
    target_file: UploadFile = File(
        ...,
        description="Archivo de destino CSV o XLSX",
    ),
    key_column: str = Form(
        "id",
        description="Columna que identifica cada registro",
    ),
):
    source_name = source_file.filename or "origen.csv"
    target_name = target_file.filename or "destino.csv"

    try:
        source_content = await _read_limited(source_file)
        target_content = await _read_limited(target_file)

        try:
            result = reconcile_tables(
                source_name=source_name,
                source_bytes=source_content,
                target_name=target_name,
                target_bytes=target_content,
                key_column=key_column,
            )
        except ReconciliationError as exc:
            raise HTTPException(
                status_code=422,
                detail=str(exc),
            ) from exc

        try:
            saved_run = save_run(
                result=result,
                source_file=source_name,
                target_file=target_name,
                key_column=key_column,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail=(
                    "La comparación se calculó, pero no se pudo guardar "
                    "en PostgreSQL. Verifica la conexión y las tablas."
                ),
            ) from exc

        if not isinstance(saved_run, dict) or saved_run.get("id") is None:
            raise HTTPException(
                status_code=503,
                detail="PostgreSQL no devolvió un identificador válido para la ejecución.",
            )

        return {
            **result,
            "run_id": saved_run["id"],
            "created_at": saved_run.get("created_at"),
        }

    finally:
        await source_file.close()
        await target_file.close()
