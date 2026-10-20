
"""Persistencia PostgreSQL para Data Migration QA."""

import json
import os
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


# ---------------------------------------------------------
# CONFIGURACION
# ---------------------------------------------------------

API_DIR = Path(__file__).resolve().parents[1]
load_dotenv(API_DIR / ".env")


# ---------------------------------------------------------
# CONEXION A POSTGRESQL
# ---------------------------------------------------------

def get_connection():
    """Abre una conexion PostgreSQL con variables de entorno."""

    required = (
        "DB_HOST",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
    )

    missing = [key for key in required if not os.getenv(key)]

    if missing:
        raise RuntimeError(
            "Faltan variables de entorno de PostgreSQL: "
            + ", ".join(missing)
        )

    try:
        port = int(os.getenv("DB_PORT", "5432"))
    except ValueError as exc:
        raise RuntimeError(
            "DB_PORT debe ser un numero entero."
        ) from exc

    sslmode = os.getenv("DB_SSLMODE", "prefer").strip().lower()

    valid_sslmodes = {
        "disable",
        "allow",
        "prefer",
        "require",
        "verify-ca",
        "verify-full",
    }

    if sslmode not in valid_sslmodes:
        raise RuntimeError(
            "DB_SSLMODE debe ser un modo SSL valido de PostgreSQL."
        )

    return psycopg.connect(
        host=os.environ["DB_HOST"],
        port=port,
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        sslmode=sslmode,
        row_factory=dict_row,
        connect_timeout=10,
    )


# ---------------------------------------------------------
# CONVERSION DE VALORES A JSON
# ---------------------------------------------------------

def _json_default(value: Any):
    """Convierte tipos comunes de Python a valores JSON."""

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")

    if hasattr(value, "item"):
        return value.item()

    return str(value)


def _json_safe(value: Any):
    """Devuelve un valor compatible con JSON y PostgreSQL JSONB."""

    return json.loads(
        json.dumps(
            value,
            default=_json_default,
            ensure_ascii=False,
        )
    )


def _get_value(data: dict, *keys, default=None):
    """Busca el primer campo disponible en un diccionario."""

    for key in keys:
        if key in data:
            return data[key]

    return default


def _normalize_status(value):
    """Normaliza los estados de las ejecuciones y comprobaciones."""

    if isinstance(value, bool):
        return "PASS" if value else "FAIL"

    status = str(value or "").strip().upper()

    if status in {"PASS", "FAIL", "WARN", "SKIP", "INFO"}:
        return status

    return "INFO"


# ---------------------------------------------------------
# CREACION DE TABLAS E INDICES
# ---------------------------------------------------------

def init_db():
    """Crea las tablas del historial si todavia no existen."""

    statements = [
        """
        CREATE TABLE IF NOT EXISTS qa_runs (
            id BIGSERIAL PRIMARY KEY,
            status TEXT NOT NULL,
            source_file TEXT,
            target_file TEXT,
            key_column TEXT NOT NULL DEFAULT 'id',
            summary JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS qa_checks (
            id BIGSERIAL PRIMARY KEY,
            run_id BIGINT NOT NULL
                REFERENCES qa_runs(id) ON DELETE CASCADE,
            check_name TEXT NOT NULL,
            status TEXT NOT NULL,
            details JSONB NOT NULL DEFAULT '{}'::jsonb
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS qa_differences (
            id BIGSERIAL PRIMARY KEY,
            run_id BIGINT NOT NULL
                REFERENCES qa_runs(id) ON DELETE CASCADE,
            difference_type TEXT NOT NULL,
            record_key TEXT,
            source_value JSONB,
            target_value JSONB,
            details JSONB NOT NULL DEFAULT '{}'::jsonb
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_qa_runs_created_at
        ON qa_runs(created_at DESC)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_qa_checks_run_id
        ON qa_checks(run_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_qa_differences_run_id
        ON qa_differences(run_id)
        """,
    ]

    with get_connection() as conn:
        with conn.cursor() as cur:
            for statement in statements:
                cur.execute(statement)


# ---------------------------------------------------------
# PREPARACION DE COMPROBACIONES
# ---------------------------------------------------------

def _prepare_checks(result: dict):
    """Prepara las comprobaciones para guardarlas en PostgreSQL."""

    checks = result.get("checks", [])

    if not isinstance(checks, list):
        return []

    prepared = []

    for check in checks:
        if not isinstance(check, dict):
            continue

        passed = check.get("passed")

        if passed is not None:
            status = _normalize_status(passed)
        else:
            status = _normalize_status(check.get("status"))

        prepared.append(
            {
                "name": str(check.get("name", "UNKNOWN")),
                "status": status,
                "details": _json_safe(check),
            }
        )

    return prepared


# ---------------------------------------------------------
# PREPARACION DE DIFERENCIAS
# ---------------------------------------------------------

def _prepare_differences(result: dict):
    """Extrae diferencias conocidas de las comprobaciones."""

    prepared = []
    checks = result.get("checks", [])

    if not isinstance(checks, list):
        return prepared

    difference_names = {
        "FIELD_DIFFERENCES",
        "MISSING_RECORDS",
        "UNEXPECTED_RECORDS",
        "DUPLICATE_KEYS",
        "BLANK_KEYS",
        "SCHEMA",
    }

    for check in checks:
        if not isinstance(check, dict):
            continue

        name = str(check.get("name", "UNKNOWN")).upper()

        if name not in difference_names:
            continue

        items = check.get("items", [])

        if isinstance(items, dict):
            items = [items]

        if not isinstance(items, list):
            continue

        if not items:
            keys = check.get("keys", [])

            if isinstance(keys, list):
                items = [{"key": key} for key in keys]

        for item in items:
            if not isinstance(item, dict):
                item = {"value": item}

            record_key = _get_value(
                item,
                "id",
                "key",
                "record_key",
                default=None,
            )

            column_name = _get_value(
                item,
                "column",
                "column_name",
                "field",
                default=None,
            )

            source_value = _get_value(
                item,
                "source",
                "source_value",
                "origen",
                default=None,
            )

            target_value = _get_value(
                item,
                "target",
                "target_value",
                "destino",
                default=None,
            )

            details = dict(item)

            if column_name is not None:
                details["column_name"] = str(column_name)

            prepared.append(
                {
                    "difference_type": name,
                    "record_key": (
                        str(record_key)
                        if record_key is not None
                        else None
                    ),
                    "source_value": _json_safe(source_value),
                    "target_value": _json_safe(target_value),
                    "details": _json_safe(details),
                }
            )

    return prepared


# ---------------------------------------------------------
# GUARDAR UNA EJECUCION
# ---------------------------------------------------------

def save_run(
    result,
    source_file=None,
    target_file=None,
    key_column="id",
):
    """Guarda una reconciliacion y devuelve el detalle registrado."""

    if not isinstance(result, dict):
        raise ValueError(
            "El resultado de la reconciliacion debe ser un diccionario."
        )

    safe_result = _json_safe(result)

    summary = safe_result.get("summary", {})

    if not isinstance(summary, dict):
        summary = {}

    status = _normalize_status(safe_result.get("status", "INFO"))

    checks = _prepare_checks(safe_result)
    differences = _prepare_differences(safe_result)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO qa_runs (
                    status,
                    source_file,
                    target_file,
                    key_column,
                    summary
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    status,
                    source_file,
                    target_file,
                    str(key_column or "id"),
                    Jsonb(_json_safe(summary)),
                ),
            )

            row = cur.fetchone()
            run_id = row["id"]

            for check in checks:
                cur.execute(
                    """
                    INSERT INTO qa_checks (
                        run_id,
                        check_name,
                        status,
                        details
                    )
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        run_id,
                        check["name"],
                        check["status"],
                        Jsonb(check["details"]),
                    ),
                )

            for difference in differences:
                cur.execute(
                    """
                    INSERT INTO qa_differences (
                        run_id,
                        difference_type,
                        record_key,
                        source_value,
                        target_value,
                        details
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        run_id,
                        difference["difference_type"],
                        difference["record_key"],
                        Jsonb(difference["source_value"]),
                        Jsonb(difference["target_value"]),
                        Jsonb(difference["details"]),
                    ),
                )

    return get_run(run_id)


# ---------------------------------------------------------
# CONSULTAR HISTORIAL
# ---------------------------------------------------------

def list_runs(limit=20, offset=0):
    """Lista las ejecuciones mas recientes."""

    limit = max(1, min(int(limit), 100))
    offset = max(0, int(offset))

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    status,
                    source_file,
                    target_file,
                    key_column,
                    summary,
                    created_at
                FROM qa_runs
                ORDER BY created_at DESC, id DESC
                LIMIT %s OFFSET %s
                """,
                (limit, offset),
            )

            return cur.fetchall()


# ---------------------------------------------------------
# CONSULTAR DETALLE DE UNA EJECUCION
# ---------------------------------------------------------

def get_run(run_id):
    """Consulta una ejecucion con sus comprobaciones y diferencias."""

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM qa_runs
                WHERE id = %s
                """,
                (run_id,),
            )

            run = cur.fetchone()

            if run is None:
                return None

            cur.execute(
                """
                SELECT
                    id,
                    check_name AS name,
                    status,
                    details
                FROM qa_checks
                WHERE run_id = %s
                ORDER BY id
                """,
                (run_id,),
            )

            run["checks"] = cur.fetchall()

            cur.execute(
                """
                SELECT
                    id,
                    difference_type,
                    record_key,
                    details->>'column_name' AS column_name,
                    source_value,
                    target_value,
                    details
                FROM qa_differences
                WHERE run_id = %s
                ORDER BY id
                """,
                (run_id,),
            )

            run["differences"] = cur.fetchall()

            return run

