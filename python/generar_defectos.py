

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
REPORTE = RAIZ / "reports" / "reporte_reconciliacion.json"
CARPETA_DEFECTOS = RAIZ / "defects"

ARCHIVO_ACTUAL = CARPETA_DEFECTOS / "defectos_migracion.csv"
ARCHIVO_HISTORIAL = CARPETA_DEFECTOS / "historial_defectos.csv"

CARPETA_DEFECTOS.mkdir(parents=True, exist_ok=True)

COLUMNAS = [
    "defecto_id",
    "ejecucion_id",
    "tipo",
    "id_registro",
    "detalle",
    "severidad",
    "estado",
    "fecha_utc",
    "evidencia",
]


def crear_defecto(
    ejecucion_id,
    tipo,
    identificador,
    detalle,
    severidad,
    evidencia,
):
    return {
        "defecto_id": "",
        "ejecucion_id": ejecucion_id,
        "tipo": tipo,
        "id_registro": identificador,
        "detalle": detalle,
        "severidad": severidad,
        "estado": "ABIERTO",
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "evidencia": json.dumps(evidencia, ensure_ascii=False),
    }


def generar_defectos(datos):
    defectos = []
    ejecucion_id = datos["ejecucion_id"]

    for control in datos.get("controles", []):
        nombre_control = control["control"]

        for hallazgo in control.get("hallazgos", []):
            if nombre_control == "REGISTROS_FALTANTES":
                defectos.append(crear_defecto(
                    ejecucion_id,
                    "REGISTRO_FALTANTE",
                    hallazgo["id"],
                    f"El registro {hallazgo['id']} ({hallazgo['nombre']}) "
                    "existe en origen, pero no en destino.",
                    "ALTA",
                    hallazgo,
                ))

            elif nombre_control == "REGISTROS_INESPERADOS":
                defectos.append(crear_defecto(
                    ejecucion_id,
                    "REGISTRO_INESPERADO",
                    hallazgo["id"],
                    f"El registro {hallazgo['id']} ({hallazgo['nombre']}) "
                    "existe en destino, pero no en origen.",
                    "MEDIA",
                    hallazgo,
                ))

            elif nombre_control == "DIFERENCIAS_DE_CAMPOS":
                for campo, valores in hallazgo["campos"].items():
                    if valores["origen"] != valores["destino"]:
                        defectos.append(crear_defecto(
                            ejecucion_id,
                            "DIFERENCIA_DE_DATOS",
                            hallazgo["id"],
                            f"El campo {campo} del registro "
                            f"{hallazgo['id']} no coincide.",
                            "ALTA" if campo in ("id", "email", "saldo")
                            else "MEDIA",
                            {
                                "campo": campo,
                                "origen": valores["origen"],
                                "destino": valores["destino"],
                            },
                        ))

            elif nombre_control == "CALIDAD_DESTINO":
                defectos.append(crear_defecto(
                    ejecucion_id,
                    "PROBLEMA_CALIDAD",
                    hallazgo["id"],
                    f"El registro {hallazgo['id']} presenta un "
                    "problema de calidad en el destino.",
                    "ALTA",
                    hallazgo,
                ))

            elif nombre_control == "CANTIDAD_REGISTROS":
                defectos.append(crear_defecto(
                    ejecucion_id,
                    "CANTIDAD_REGISTROS",
                    "",
                    "La cantidad de registros del origen y destino no coincide.",
                    "ALTA",
                    hallazgo,
                ))

    for numero, defecto in enumerate(defectos, start=1):
        defecto["defecto_id"] = f"DMQA-{numero:04d}"

    return defectos


def guardar_csv(ruta, filas, modo="w"):
    with ruta.open(
        modo,
        encoding="utf-8-sig",
        newline="",
    ) as archivo:
        escritor = csv.DictWriter(
            archivo,
            fieldnames=COLUMNAS,
            extrasaction="ignore",
        )

        if modo == "w" or archivo.tell() == 0:
            escritor.writeheader()

        escritor.writerows(filas)


def main():
    if not REPORTE.exists():
        raise FileNotFoundError(
            f"No existe el informe: {REPORTE}. "
            "Ejecuta primero motor_reconciliacion.py."
        )

    with REPORTE.open("r", encoding="utf-8-sig") as archivo:
        datos = json.load(archivo)

    ejecucion_id = datos["ejecucion_id"]

    # No duplicar una ejecución si se vuelve a procesar el mismo informe.
    if ARCHIVO_HISTORIAL.exists():
        with ARCHIVO_HISTORIAL.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as archivo:
            historico = list(csv.DictReader(archivo))

        if any(
            fila["ejecucion_id"] == ejecucion_id
            for fila in historico
        ):
            print(
                "Esta ejecución ya existe en el historial. "
                "No se añadieron filas duplicadas."
            )
            defectos = [
                fila for fila in historico
                if fila["ejecucion_id"] == ejecucion_id
            ]
            guardar_csv(ARCHIVO_ACTUAL, defectos)
            return

    defectos = generar_defectos(datos)

    # Informe actual: reemplaza únicamente los resultados actuales.
    guardar_csv(ARCHIVO_ACTUAL, defectos)

    # Historial: agrega los defectos sin borrar ejecuciones anteriores.
    if ARCHIVO_HISTORIAL.exists():
        guardar_csv(ARCHIVO_HISTORIAL, defectos, modo="a")
    else:
        guardar_csv(ARCHIVO_HISTORIAL, defectos)

    print("\n=== GESTIÓN DE DEFECTOS DATA QA ===")
    print(f"Ejecución: {ejecucion_id}")
    print(f"Defectos actuales: {len(defectos)}")
    print(
        "Defectos abiertos: "
        f"{sum(d['estado'] == 'ABIERTO' for d in defectos)}"
    )
    print(f"Informe actual: {ARCHIVO_ACTUAL}")
    print(f"Historial acumulado: {ARCHIVO_HISTORIAL}")


if __name__ == "__main__":
    main()

