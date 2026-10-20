from __future__ import annotations

import csv
import io
import math
from decimal import Decimal, InvalidOperation
from typing import Any

from openpyxl import load_workbook


MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_ROWS = 100_000
ALLOWED_EXTENSIONS = {".csv", ".xlsx"}


class ReconciliationError(ValueError):
    """Invalid or unsupported reconciliation input."""


def _read_table(filename: str, content: bytes) -> tuple[list[str], list[dict[str, Any]]]:
    import os

    extension = os.path.splitext(filename.lower())[1]

    if extension not in ALLOWED_EXTENSIONS:
        raise ReconciliationError(
            f"Formato no permitido para {filename}. Usa CSV o XLSX."
        )

    if not content:
        raise ReconciliationError(f"El archivo {filename} está vacío.")

    if len(content) > MAX_FILE_BYTES:
        raise ReconciliationError(
            f"El archivo {filename} supera el límite de 10 MB."
        )

    if extension == ".csv":
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ReconciliationError(
                f"{filename} no está codificado en UTF-8. Guárdalo como CSV UTF-8."
            ) from exc

        try:
            sample = text[:8192]
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
            except csv.Error:
                dialect = csv.excel

            reader = csv.DictReader(io.StringIO(text), dialect=dialect)
            headers = reader.fieldnames

            if not headers:
                raise ReconciliationError(f"{filename} no contiene encabezados.")

            cleaned_headers = [str(h).strip() if h is not None else "" for h in headers]

            if any(not h for h in cleaned_headers):
                raise ReconciliationError(
                    f"{filename} contiene encabezados vacíos."
                )

            if len(set(cleaned_headers)) != len(cleaned_headers):
                raise ReconciliationError(
                    f"{filename} contiene encabezados duplicados."
                )

            rows: list[dict[str, Any]] = []

            for row in reader:
                if len(rows) >= MAX_ROWS:
                    raise ReconciliationError(
                        f"{filename} supera el máximo de {MAX_ROWS} filas."
                    )

                normalized = {}
                for original, cleaned in zip(headers, cleaned_headers):
                    value = row.get(original)
                    normalized[cleaned] = value.strip() if isinstance(value, str) else value

                rows.append(normalized)

            return cleaned_headers, rows

        except csv.Error as exc:
            raise ReconciliationError(f"No se pudo leer el CSV {filename}.") from exc

    try:
        workbook = load_workbook(
            io.BytesIO(content),
            read_only=True,
            data_only=True,
        )
        try:
            sheet = workbook.active
            iterator = sheet.iter_rows(values_only=True)
            first_row = next(iterator, None)

            if not first_row:
                raise ReconciliationError(f"{filename} no contiene datos.")

            headers = [
                str(value).strip() if value is not None else ""
                for value in first_row
            ]

            while headers and headers[-1] == "":
                headers.pop()

            if not headers or any(not header for header in headers):
                raise ReconciliationError(
                    f"{filename} contiene encabezados vacíos."
                )

            if len(set(headers)) != len(headers):
                raise ReconciliationError(
                    f"{filename} contiene encabezados duplicados."
                )

            rows = []
            for values in iterator:
                if values is None or all(v is None for v in values):
                    continue

                if len(rows) >= MAX_ROWS:
                    raise ReconciliationError(
                        f"{filename} supera el máximo de {MAX_ROWS} filas."
                    )

                padded = list(values[:len(headers)])
                padded.extend([None] * (len(headers) - len(padded)))
                rows.append(dict(zip(headers, padded)))

            return headers, rows
        finally:
            workbook.close()

    except ReconciliationError:
        raise
    except Exception as exc:
        raise ReconciliationError(
            f"No se pudo leer {filename} como un archivo Excel XLSX válido."
        ) from exc


def _normalize(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, bool):
        return str(value).lower()

    if isinstance(value, float) and not math.isfinite(value):
        return str(value)

    return str(value).strip()


def _equivalent(left: Any, right: Any) -> bool:
    a = _normalize(left)
    b = _normalize(right)

    if a == b:
        return True

    # Comparar representaciones numéricas equivalentes, por ejemplo 150.0 y 150.00.
    if a and b:
        try:
            da = Decimal(a)
            db = Decimal(b)
            if da.is_finite() and db.is_finite():
                return da == db
        except InvalidOperation:
            pass

    return False


def reconcile_tables(
    source_name: str,
    source_bytes: bytes,
    target_name: str,
    target_bytes: bytes,
    key_column: str = "id",
) -> dict[str, Any]:
    if not key_column or not key_column.strip():
        raise ReconciliationError("Debes indicar la columna clave.")

    key_column = key_column.strip()

    source_headers, source_rows = _read_table(source_name, source_bytes)
    target_headers, target_rows = _read_table(target_name, target_bytes)

    if key_column not in source_headers:
        raise ReconciliationError(
            f"La columna clave '{key_column}' no existe en el archivo de origen."
        )

    if key_column not in target_headers:
        raise ReconciliationError(
            f"La columna clave '{key_column}' no existe en el archivo de destino."
        )

    source_index: dict[str, dict[str, Any]] = {}
    target_index: dict[str, dict[str, Any]] = {}
    source_duplicates: list[str] = []
    target_duplicates: list[str] = []
    source_blank_keys = 0
    target_blank_keys = 0

    for row in source_rows:
        key = _normalize(row.get(key_column))
        if not key:
            source_blank_keys += 1
        elif key in source_index:
            source_duplicates.append(key)
        else:
            source_index[key] = row

    for row in target_rows:
        key = _normalize(row.get(key_column))
        if not key:
            target_blank_keys += 1
        elif key in target_index:
            target_duplicates.append(key)
        else:
            target_index[key] = row

    source_keys = set(source_index)
    target_keys = set(target_index)

    missing = sorted(source_keys - target_keys)
    unexpected = sorted(target_keys - source_keys)

    common_columns = [
        column
        for column in source_headers
        if column in target_headers and column != key_column
    ]

    # Una clave duplicada no identifica un registro de forma univoca.
    # Evitamos comparar arbitrariamente solo su primera aparicion.
    ambiguous_keys = set(source_duplicates) | set(target_duplicates)

    differences = []
    for key in sorted((source_keys & target_keys) - ambiguous_keys):
        source_row = source_index[key]
        target_row = target_index[key]

        for column in common_columns:
            left = source_row.get(column)
            right = target_row.get(column)

            if not _equivalent(left, right):
                differences.append({
                    "key": key,
                    "column": column,
                    "source_value": _normalize(left),
                    "target_value": _normalize(right),
                })

    source_only_columns = sorted(set(source_headers) - set(target_headers))
    target_only_columns = sorted(set(target_headers) - set(source_headers))

    checks = [
        {
            "name": "RECORD_COUNTS",
            "passed": len(source_rows) == len(target_rows),
            "source": len(source_rows),
            "target": len(target_rows),
        },
        {
            "name": "MISSING_RECORDS",
            "passed": len(missing) == 0,
            "count": len(missing),
            "keys": missing[:1000],
        },
        {
            "name": "UNEXPECTED_RECORDS",
            "passed": len(unexpected) == 0,
            "count": len(unexpected),
            "keys": unexpected[:1000],
        },
        {
            "name": "FIELD_DIFFERENCES",
            "passed": len(differences) == 0,
            "count": len(differences),
            "items": differences[:5000],
            "skipped_ambiguous_keys": sorted(ambiguous_keys),
        },
        {
            "name": "DUPLICATE_KEYS",
            "passed": not source_duplicates and not target_duplicates,
            "source_count": len(source_duplicates),
            "target_count": len(target_duplicates),
            "source_keys": source_duplicates[:1000],
            "target_keys": target_duplicates[:1000],
        },
        {
            "name": "BLANK_KEYS",
            "passed": source_blank_keys == 0 and target_blank_keys == 0,
            "source_count": source_blank_keys,
            "target_count": target_blank_keys,
        },
        {
            "name": "SCHEMA",
            "passed": not source_only_columns and not target_only_columns,
            "source_only_columns": source_only_columns,
            "target_only_columns": target_only_columns,
        },
    ]

    passed = sum(1 for check in checks if check["passed"])
    failed = len(checks) - passed

    return {
        "status": "PASS" if failed == 0 else "FAIL",
        "summary": {
            "source_file": source_name,
            "target_file": target_name,
            "key_column": key_column,
            "source_rows": len(source_rows),
            "target_rows": len(target_rows),
            "matched_keys": len(source_keys & target_keys),
            "missing_records": len(missing),
            "unexpected_records": len(unexpected),
            "field_differences": len(differences),
            "checks_passed": passed,
            "checks_failed": failed,
        },
        "checks": checks,
        "column_comparison": {
            "common_columns": common_columns,
            "source_only_columns": source_only_columns,
            "target_only_columns": target_only_columns,
        },
        "limitations": [
            "Los archivos se procesan en memoria y no se almacenan; el resumen, las validaciones y las diferencias de cada ejecución sí se guardan en PostgreSQL.",
            "Las filas con claves duplicadas se reportan; para comparar registros se utiliza la primera aparición de cada clave.",
            "El límite de 10 MB y 100.000 filas aplica a cada archivo.",
        ],
    }

