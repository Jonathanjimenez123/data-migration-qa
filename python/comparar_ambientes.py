
import csv
import json
from pathlib import Path
from datetime import datetime

RAIZ = Path(__file__).resolve().parent.parent
CARPETA_DATOS = RAIZ / "test-data"
CARPETA_REPORTES = RAIZ / "reports"

def cargar_csv(nombre_archivo):
    ruta = CARPETA_DATOS / nombre_archivo

    with ruta.open("r", encoding="utf-8-sig", newline="") as archivo:
        return {
            fila["id"]: fila
            for fila in csv.DictReader(archivo)
        }

origen = cargar_csv("origen_aws.csv")
destino = cargar_csv("destino_postgresql.csv")

ids_origen = set(origen)
ids_destino = set(destino)

faltantes = sorted(ids_origen - ids_destino)
inesperados = sorted(ids_destino - ids_origen)
diferencias = []

for identificador in sorted(ids_origen & ids_destino):
    for campo in ("nombre", "email", "saldo"):
        valor_origen = origen[identificador][campo]
        valor_destino = destino[identificador][campo]

        if valor_origen != valor_destino:
            diferencias.append({
                "id": identificador,
                "campo": campo,
                "valor_origen": valor_origen,
                "valor_destino": valor_destino,
            })

reporte = {
    "fecha": datetime.now().isoformat(timespec="seconds"),
    "registros_origen": len(origen),
    "registros_destino": len(destino),
    "registros_faltantes": faltantes,
    "registros_inesperados": inesperados,
    "diferencias_de_campos": diferencias,
    "resultado": (
        "PASS"
        if not faltantes and not inesperados and not diferencias
        else "FAIL"
    ),
}

CARPETA_REPORTES.mkdir(parents=True, exist_ok=True)
archivo_reporte = CARPETA_REPORTES / "reconciliacion.json"
archivo_reporte.write_text(
    json.dumps(reporte, indent=4, ensure_ascii=False),
    encoding="utf-8",
)

print("=" * 45)
print("DATA QA - RECONCILIACION DE AMBIENTES")
print("=" * 45)
print(f"Registros en origen: {len(origen)}")
print(f"Registros en destino: {len(destino)}")
print(f"Registros faltantes: {faltantes}")
print(f"Registros inesperados: {inesperados}")
print(f"Diferencias de campos: {len(diferencias)}")

for diferencia in diferencias:
    print(
        f"ID {diferencia['id']} | {diferencia['campo']}: "
        f"{diferencia['valor_origen']} -> "
        f"{diferencia['valor_destino']}"
    )

print(f"\nRESULTADO GENERAL: {reporte['resultado']}")
print(f"Reporte JSON: {archivo_reporte}")
