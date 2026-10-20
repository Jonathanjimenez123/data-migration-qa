import csv
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
ARCHIVO_ORIGEN = RAIZ / "test-data" / "origen_aws.csv"
ARCHIVO_DESTINO = RAIZ / "test-data" / "destino_postgresql.csv"


def cargar_csv(ruta):
    with ruta.open("r", encoding="utf-8", newline="") as archivo:
        return list(csv.DictReader(archivo))


@pytest.fixture
def datos_origen():
    return cargar_csv(ARCHIVO_ORIGEN)


@pytest.fixture
def datos_destino():
    return cargar_csv(ARCHIVO_DESTINO)


def test_archivos_csv_existen():
    assert ARCHIVO_ORIGEN.exists()
    assert ARCHIVO_DESTINO.exists()


def test_origen_tiene_registros(datos_origen):
    assert len(datos_origen) > 0


def test_ids_del_origen_son_unicos(datos_origen):
    ids = [fila["id"] for fila in datos_origen]
    assert len(ids) == len(set(ids)), "Hay IDs duplicados en el origen"


def test_cantidad_registros_coincide(datos_origen, datos_destino):
    assert len(datos_origen) == len(datos_destino), (
        f"Origen: {len(datos_origen)}; destino: {len(datos_destino)}"
    )


def test_ids_coinciden(datos_origen, datos_destino):
    ids_origen = {fila["id"] for fila in datos_origen}
    ids_destino = {fila["id"] for fila in datos_destino}

    faltantes = ids_origen - ids_destino
    inesperados = ids_destino - ids_origen

    assert not faltantes and not inesperados, (
        f"IDs faltantes: {sorted(faltantes)}; "
        f"IDs inesperados: {sorted(inesperados)}"
    )


def test_saldos_coinciden(datos_origen, datos_destino):
    origen = {fila["id"]: fila["saldo"] for fila in datos_origen}
    destino = {fila["id"]: fila["saldo"] for fila in datos_destino}

    ids_comunes = origen.keys() & destino.keys()
    diferencias = {
        id_cliente: (origen[id_cliente], destino[id_cliente])
        for id_cliente in ids_comunes
        if origen[id_cliente] != destino[id_cliente]
    }

    assert not diferencias, f"Saldos diferentes: {diferencias}"


def test_emails_no_estan_vacios(datos_origen, datos_destino):
    for ambiente, registros in (
        ("origen", datos_origen),
        ("destino", datos_destino),
    ):
        vacios = [
            fila["id"]
            for fila in registros
            if not fila.get("email", "").strip()
        ]
        assert not vacios, (
            f"Emails vacíos en {ambiente}, IDs: {vacios}"
        )
