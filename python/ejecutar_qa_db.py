
import json
from datetime import datetime
from pathlib import Path
from getpass import getpass

import psycopg

RAIZ = Path(__file__).resolve().parent.parent
CARPETA_REPORTES = RAIZ / "reports"
CARPETA_REPORTES.mkdir(parents=True, exist_ok=True)

def ejecutar_prueba(cursor, nombre, consulta):
    cursor.execute(consulta)
    cantidad = cursor.fetchone()[0]

    return {
        "prueba": nombre,
        "resultado": "PASS" if cantidad == 0 else "FAIL",
        "hallazgos": cantidad,
    }

def main():
    contrasena = getpass("Contraseña de PostgreSQL (postgres): ")

    try:
        with psycopg.connect(
            host="localhost",
            port=5432,
            dbname="data_migration_qa",
            user="postgres",
            password=contrasena,
        ) as conexion:
            with conexion.cursor() as cursor:
                pruebas = []

                # La diferencia de cantidades debe ser cero.
                cursor.execute("""
                    SELECT ABS(
                        (SELECT COUNT(*) FROM origen_aws) -
                        (SELECT COUNT(*) FROM destino_postgresql)
                    )
                """)
                diferencia_total = cursor.fetchone()[0]
                pruebas.append({
                    "prueba": "CANTIDAD_REGISTROS",
                    "resultado": "PASS" if diferencia_total == 0 else "FAIL",
                    "hallazgos": diferencia_total,
                })

                pruebas.append(ejecutar_prueba(
                    cursor,
                    "REGISTROS_FALTANTES",
                    """
                    SELECT COUNT(*)
                    FROM origen_aws o
                    LEFT JOIN destino_postgresql d ON d.id = o.id
                    WHERE d.id IS NULL
                    """
                ))

                pruebas.append(ejecutar_prueba(
                    cursor,
                    "REGISTROS_INESPERADOS",
                    """
                    SELECT COUNT(*)
                    FROM destino_postgresql d
                    LEFT JOIN origen_aws o ON o.id = d.id
                    WHERE o.id IS NULL
                    """
                ))

                pruebas.append(ejecutar_prueba(
                    cursor,
                    "SALDOS_DIFERENTES",
                    """
                    SELECT COUNT(*)
                    FROM origen_aws o
                    JOIN destino_postgresql d ON d.id = o.id
                    WHERE o.saldo IS DISTINCT FROM d.saldo
                    """
                ))

                cursor.execute("SELECT COUNT(*) FROM origen_aws")
                total_origen = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM destino_postgresql")
                total_destino = cursor.fetchone()[0]

        aprobadas = sum(p["resultado"] == "PASS" for p in pruebas)
        fallidas = sum(p["resultado"] == "FAIL" for p in pruebas)

        reporte = {
            "proyecto": "Data Migration QA",
            "fecha": datetime.now().isoformat(timespec="seconds"),
            "base_datos": "data_migration_qa",
            "registros_origen": total_origen,
            "registros_destino": total_destino,
            "pruebas_aprobadas": aprobadas,
            "pruebas_fallidas": fallidas,
            "resultado_general": "PASS" if fallidas == 0 else "FAIL",
            "resultados": pruebas,
        }

        archivo = CARPETA_REPORTES / "reporte_qa_postgresql.json"
        archivo.write_text(
            json.dumps(reporte, indent=4, ensure_ascii=False),
            encoding="utf-8",
        )

        print("\n" + "=" * 45)
        print("DATA QA - RESULTADOS AUTOMATIZADOS")
        print("=" * 45)
        print(f"Registros en origen: {total_origen}")
        print(f"Registros en destino: {total_destino}")

        for prueba in pruebas:
            print(
                f"{prueba['resultado']} | {prueba['prueba']} "
                f"| Hallazgos: {prueba['hallazgos']}"
            )

        print(f"\nPruebas aprobadas: {aprobadas}")
        print(f"Pruebas fallidas: {fallidas}")
        print(f"Resultado general: {reporte['resultado_general']}")
        print(f"Informe guardado en: {archivo}")

    except psycopg.OperationalError as error:
        print("No se pudo conectar a PostgreSQL.")
        print("Comprueba que el servicio esté activo y la contraseña sea correcta.")
        print(f"Detalle: {error}")

if __name__ == "__main__":
    main()

