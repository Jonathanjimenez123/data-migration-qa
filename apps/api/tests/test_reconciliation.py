import pytest

from app.services.reconciliation import (
    ReconciliationError,
    reconcile_tables,
)


SOURCE = b"""id,nombre,email,saldo
1,Ana,ana@ejemplo.com,100000
2,Carlos,carlos@ejemplo.com,200000
3,Laura,laura@ejemplo.com,150000
4,Sofia,sofia@ejemplo.com,300000
"""

TARGET = b"""id,nombre,email,saldo
1,Ana,ana@ejemplo.com,100000
2,Carlos,carlos@ejemplo.com,200000
3,Laura,laura@ejemplo.com,145000
5,Pedro,pedro@ejemplo.com,250000
"""


def run_comparison(source=SOURCE, target=TARGET, key_column="id"):
    return reconcile_tables(
        source_name="origen_aws.csv",
        source_bytes=source,
        target_name="destino_postgresql.csv",
        target_bytes=target,
        key_column=key_column,
    )


def checks_by_name(result):
    return {check["name"]: check for check in result["checks"]}


def test_detects_missing_record():
    result = run_comparison()
    check = checks_by_name(result)["MISSING_RECORDS"]

    assert result["status"] == "FAIL"
    assert check["passed"] is False
    assert check["keys"] == ["4"]


def test_detects_unexpected_record():
    result = run_comparison()
    check = checks_by_name(result)["UNEXPECTED_RECORDS"]

    assert check["passed"] is False
    assert check["keys"] == ["5"]


def test_detects_field_difference():
    result = run_comparison()
    check = checks_by_name(result)["FIELD_DIFFERENCES"]

    assert check["passed"] is False
    assert check["count"] == 1
    assert check["items"][0]["key"] == "3"
    assert check["items"][0]["column"] == "saldo"
    assert check["items"][0]["source_value"] == "150000"
    assert check["items"][0]["target_value"] == "145000"


def test_detects_matching_row_counts():
    result = run_comparison()
    check = checks_by_name(result)["RECORD_COUNTS"]

    assert check["passed"] is True
    assert check["source"] == 4
    assert check["target"] == 4


def test_reports_duplicate_keys():
    source = b"id,nombre\n1,Ana\n1,Otra Ana\n"
    target = b"id,nombre\n1,Ana\n"

    result = run_comparison(source=source, target=target)
    check = checks_by_name(result)["DUPLICATE_KEYS"]

    assert check["passed"] is False
    assert check["source_count"] == 1
    assert check["source_keys"] == ["1"]


def test_rejects_missing_key_column():
    source = b"codigo,nombre\n1,Ana\n"
    target = b"codigo,nombre\n1,Ana\n"

    with pytest.raises(ReconciliationError):
        run_comparison(source=source, target=target, key_column="id")


def test_rejects_unsupported_file_extension():
    with pytest.raises(ReconciliationError):
        reconcile_tables(
            source_name="origen.txt",
            source_bytes=b"id,nombre\n1,Ana\n",
            target_name="destino.csv",
            target_bytes=b"id,nombre\n1,Ana\n",
            key_column="id",
        )


def test_numeric_values_with_different_format_are_equivalent():
    source = b"id,saldo\n1,150000\n"
    target = b"id,saldo\n1,150000.00\n"

    result = run_comparison(source=source, target=target)
    check = checks_by_name(result)["FIELD_DIFFERENCES"]

    assert check["passed"] is True
    assert check["count"] == 0

def test_duplicate_keys_are_not_compared_as_unique_records():
    source = b"id,nombre\n1,Ana\n1,Otra Ana\n2,Carlos\n"
    target = b"id,nombre\n1,Distinto\n2,Carla\n"

    result = run_comparison(source=source, target=target)
    checks = checks_by_name(result)

    duplicate_check = checks["DUPLICATE_KEYS"]
    field_check = checks["FIELD_DIFFERENCES"]

    assert duplicate_check["passed"] is False
    assert field_check["skipped_ambiguous_keys"] == ["1"]
    assert field_check["count"] == 1
    assert field_check["items"][0]["key"] == "2"
    assert field_check["items"][0]["column"] == "nombre"
    assert result["status"] == "FAIL"

