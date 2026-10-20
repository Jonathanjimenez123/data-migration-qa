
import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from getpass import getpass
from pathlib import Path

import psycopg


# ============================================================
# CONFIGURACIÓN DEL PROYECTO
# ============================================================

RAIZ = Path(__file__).resolve().parent.parent
CARPETA_REPORTES = RAIZ / "reports"
CARPETA_HISTORIAL = CARPETA_REPORTES / "historial"

ARCHIVO_ACTUAL = CARPETA_REPORTES / "reporte_reconciliacion.json"

CARPETA_REPORTES.mkdir(parents=True, exist_ok=True)
CARPETA_HISTORIAL.mkdir(parents=True, exist_ok=True)


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def ejecutar_conteo(cursor, consulta, parametros=None):
    cursor.execute(consulta, parametros or ())
    return cursor.fetchone()[0]


def registrar_control(nombre, hallazgos, detalle):
    return {
        "control": nombre,
        "estado": "PASS" if not hallazgos else "FAIL",
        "cantidad_hallazgos": len(hallazgos),
        "detalle": detalle,
        "hallazgos": hallazgos,
    }


def convertir_valor(valor):
    if isinstance(valor, Decimal):
        return str(valor)
    return valor


def guardar_json(ruta, datos):
    contenido = json.dumps(
        datos,
        indent=4,
        ensure_ascii=False,
    )
    ruta.write_text(contenido + "\n", encoding="utf-8")


# ============================================================
# RECONCILIACIÓN DE DATOS
# ============================================================

def ejecutar_reconciliacion(conexion):
    with conexion.cursor() as cursor:

        # 1. Comparar cantidades
        total_origen = ejecutar_conteo(
            cursor,
            "SELECT COUNT(*) FROM origen_aws",
        )

        total_destino = ejecutar_conteo(
            cursor,
            "SELECT COUNT(*) FROM destino_postgresql",
        )

        # 2. Encontrar registros faltantes
        cursor.execute("""
            SELECT o.id, o.nombre
            FROM origen_aws AS o
            LEFT JOIN destino_postgresql AS d ON d.id = o.id
            WHERE d.id IS NULL
            ORDER BY o.id
        """)

        faltantes = [
            {"id": fila[0], "nombre": fila[1]}
            for fila in cursor.fetchall()
        ]

        # 3. Encontrar registros inesperados
        cursor.execute("""
            SELECT d.id, d.nombre
            FROM destino_postgresql AS d
            LEFT JOIN origen_aws AS o ON o.id = d.id
            WHERE o.id IS NULL
            ORDER BY d.id
        """)

        inesperados = [
            {"id": fila[0], "nombre": fila[1]}
            for fila in cursor.fetchall()
        ]

        # 4. Comparar los campos de registros coincidentes
        cursor.execute("""
            SELECT
                o.id,
                o.nombre, d.nombre,
                o.email, d.email,
                o.saldo, d.saldo
            FROM origen_aws AS o
            INNER JOIN destino_postgresql AS d ON d.id = o.id
            WHERE o.nombre IS DISTINCT FROM d.nombre
               OR o.email IS DISTINCT FROM d.email
               OR o.saldo IS DISTINCT FROM d.saldo
            ORDER BY o.id
        """)

        diferencias = []

        for fila in cursor.fetchall():
            campos = {}

            for nombre_campo, valor_origen, valor_destino in [
                ("nombre", fila[1], fila[2]),
                ("email", fila[3], fila[4]),
                ("saldo", fila[5], fila[6]),
            ]:
                campos[nombre_campo] = {
                    "origen": convertir_valor(valor_origen),
                    "destino": convertir_valor(valor_destino),
                }

            diferencias.append({
                "id": fila[0],
                "campos": campos,
            })

        # 5. Comprobar calidad de los datos de destino
        cursor.execute(r"""
            SELECT id, nombre, email, saldo
            FROM destino_postgresql
            WHERE email IS NULL
               OR BTRIM(email) = ''
               OR email !~* '^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$'
               OR saldo IS NULL
               OR saldo < 0
            ORDER BY id
        """)

        problemas_calidad = []

        for fila in cursor.fetchall():
            problemas_calidad.append({
                "id": fila[0],
                "nombre": fila[1],
                "email": fila[2],
                "saldo": convertir_valor(fila[3]),
            })

    # Construir resultados de los controles
    controles = [
        registrar_control(
            "CANTIDAD_REGISTROS",
            [] if total_origen == total_destino else [{
                "origen": total_origen,
                "destino": total_destino,
            }],
            "Compara el número de registros de ambas tablas.",
        ),
        registrar_control(
            "REGISTROS_FALTANTES",
            faltantes,
            "Registros del origen que no existen en el destino.",
        ),
        registrar_control(
            "REGISTROS_INESPERADOS",
            inesperados,
            "Registros del destino que no existen en el origen.",
        ),
        registrar_control(
            "DIFERENCIAS_DE_CAMPOS",
            diferencias,
            "Compara nombre, email y saldo por identificador.",
        ),
        registrar_control(
            "CALIDAD_DESTINO",
            problemas_calidad,
            "Detecta emails inválidos o vacíos y saldos nulos o negativos.",
        ),
    ]

    controles_fallidos = sum(
        control["estado"] == "FAIL"
        for control in controles
    )

    # Identificar esta ejecución
    ejecucion_id = str(uuid.uuid4())
    fecha_utc = datetime.now(timezone.utc).isoformat()

    reporte = {
        "proyecto": "Data Migration QA",
        "ejecucion_id": ejecucion_id,
        "fecha_utc": fecha_utc,
        "origen": "origen_aws",
        "destino": "destino_postgresql",
        "total_origen": total_origen,
        "total_destino": total_destino,
        "controles_ejecutados": len(controles),
        "controles_aprobados": len(controles) - controles_fallidos,
        "controles_fallidos": controles_fallidos,
        "resultado_general": (
            "PASS" if controles_fallidos == 0 else "FAIL"
        ),
        "controles": controles,
    }

    return reporte


# ============================================================
# GUARDAR INFORME ACTUAL E HISTÓRICO
# ============================================================

def guardar_informes(reporte):
    # Informe actual: se actualiza en cada ejecución
    guardar_json(ARCHIVO_ACTUAL, reporte)

    # Informe histórico: nombre único por ejecución
    nombre_historico = (
        f"reconciliacion_{reporte['ejecucion_id']}.json"
    )

    archivo_historico = CARPETA_HISTORIAL / nombre_historico

    # Modo exclusivo: evita sobrescribir un informe histórico existente
    with archivo_historico.open("x", encoding="utf-8") as archivo:
        json.dump(
            reporte,
            archivo,
            indent=4,
            ensure_ascii=False,
        )
        archivo.write("\n")

    return archivo_historico


# ============================================================
# EJECUCIÓN PRINCIPAL
# ============================================================

def main():
    password = getpass("Contraseña de PostgreSQL (postgres): ")

    try:
        with psycopg.connect(
            host="localhost",
            port=5432,
            dbname="data_migration_qa",
            user="postgres",
            password=password,
        ) as conexion:
            reporte = ejecutar_reconciliacion(conexion)

        archivo_historico = guardar_informes(reporte)

        print("\n=== MOTOR DE RECONCILIACIÓN DATA QA ===")
        print(f"Ejecución: {reporte['ejecucion_id']}")
        print(f"Fecha UTC: {reporte['fecha_utc']}")
        print(f"Registros origen: {reporte['total_origen']}")
        print(f"Registros destino: {reporte['total_destino']}")

        print("\n--- RESULTADO DE LOS CONTROLES ---")

        for control in reporte["controles"]:
            print(
                f"{control['estado']} | {control['control']} | "
                f"Hallazgos: {control['cantidad_hallazgos']}"
            )

        print("\n--- RESUMEN ---")
        print(f"Controles ejecutados: {reporte['controles_ejecutados']}")
        print(f"Controles aprobados: {reporte['controles_aprobados']}")
        print(f"Controles fallidos: {reporte['controles_fallidos']}")
        print(f"Resultado general: {reporte['resultado_general']}")

        print("\n--- INFORMES GENERADOS ---")
        print(f"Informe actual: {ARCHIVO_ACTUAL}")
        print(f"Informe histórico: {archivo_historico}")

    except psycopg.OperationalError as error:
        print("\nERROR: No fue posible conectar con PostgreSQL.")
        print(f"Detalle: {error}")

    except FileExistsError as error:
        print("\nERROR: Ya existe el archivo histórico de esta ejecución.")
        print(f"Detalle: {error}")


if __name__ == "__main__":
    main()

