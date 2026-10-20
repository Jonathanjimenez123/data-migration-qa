@'
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
HISTORIAL_REPORTES = RAIZ / "reports" / "historial"
HISTORIAL_DEFECTOS = RAIZ / "defects" / "historial_defectos.csv"

SALIDA_JSON = RAIZ / "reports" / "metricas_qa.json"
SALIDA_CSV = RAIZ / "reports" / "evolucion_ejecuciones.csv"


def cargar_reportes():
    reportes = []

    if not HISTORIAL_REPORTES.exists():
        return reportes

    for ruta in HISTORIAL_REPORTES.glob("reconciliacion_*.json"):
        try:
            with ruta.open("r", encoding="utf-8-sig") as archivo:
                reporte = json.load(archivo)

            if "ejecucion_id" in reporte and "controles" in reporte:
                reportes.append(reporte)

        except (OSError, json.JSONDecodeError) as error:
            print(f"AVISO: no se pudo leer {ruta.name}: {error}")

    # Orden cronológico por fecha UTC
    reportes.sort(key=lambda r: r.get("fecha_utc", ""))

    return reportes


def cargar_defectos():
    if not HISTORIAL_DEFECTOS.exists():
        return []

    with HISTORIAL_DEFECTOS.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as archivo:
        return list(csv.DictReader(archivo))


def construir_metricas(reportes, defectos):
    ejecuciones_aprobadas = sum(
        r.get("resultado_general") == "PASS" for r in reportes
    )
    ejecuciones_fallidas = sum(
        r.get("resultado_general") == "FAIL" for r in reportes
    )

    controles_ejecutados = sum(
        r.get("controles_ejecutados", len(r.get("controles", [])))
        for r in reportes
    )

    controles_aprobados = sum(
        c.get("estado") == "PASS"
        for r in reportes
        for c in r.get("controles", [])
    )

    controles_fallidos = sum(
        c.get("estado") == "FAIL"
        for r in reportes
        for c in r.get("controles", [])
    )

    tasa_aprobacion = (
        round(controles_aprobados / controles_ejecutados * 100, 2)
        if controles_ejecutados else 0
    )

    # Contar defectos históricos sin confundir ejecuciones distintas
    por_severidad = Counter(
        d.get("severidad", "SIN_SEVERIDAD") for d in defectos
    )
    por_estado = Counter(
        d.get("estado", "SIN_ESTADO") for d in defectos
    )
    por_tipo = Counter(
        d.get("tipo", "SIN_TIPO") for d in defectos
    )

    evolucion = []

    for reporte in reportes:
        controles = reporte.get("controles", [])
        aprobados = sum(c.get("estado") == "PASS" for c in controles)
        fallidos = sum(c.get("estado") == "FAIL" for c in controles)

        defectos_ejecucion = [
            d for d in defectos
            if d.get("ejecucion_id") == reporte.get("ejecucion_id")
        ]

        evolucion.append({
            "ejecucion_id": reporte.get("ejecucion_id"),
            "fecha_utc": reporte.get("fecha_utc"),
            "resultado_general": reporte.get("resultado_general"),
            "controles_ejecutados": len(controles),
            "controles_aprobados": aprobados,
            "controles_fallidos": fallidos,
            "defectos_registrados": len(defectos_ejecucion),
        })

    return {
        "proyecto": "Data Migration QA",
        "fecha_generacion_utc": datetime.now(timezone.utc).isoformat(),
        "total_ejecuciones": len(reportes),
        "ejecuciones_aprobadas": ejecuciones_aprobadas,
        "ejecuciones_fallidas": ejecuciones_fallidas,
        "controles_ejecutados": controles_ejecutados,
        "controles_aprobados": controles_aprobados,
        "controles_fallidos": controles_fallidos,
        "tasa_aprobacion_controles_pct": tasa_aprobacion,
        "total_defectos_historicos": len(defectos),
        "defectos_por_severidad": dict(sorted(por_severidad.items())),
        "defectos_por_estado": dict(sorted(por_estado.items())),
        "defectos_por_tipo": dict(sorted(por_tipo.items())),
        "evolucion": evolucion,
    }


def guardar_resultados(metricas):
    SALIDA_JSON.parent.mkdir(parents=True, exist_ok=True)

    with SALIDA_JSON.open("w", encoding="utf-8") as archivo:
        json.dump(
            metricas,
            archivo,
            indent=4,
            ensure_ascii=False,
        )
        archivo.write("\n")

    columnas = [
        "ejecucion_id",
        "fecha_utc",
        "resultado_general",
        "controles_ejecutados",
        "controles_aprobados",
        "controles_fallidos",
        "defectos_registrados",
    ]

    with SALIDA_CSV.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=columnas)
        escritor.writeheader()
        escritor.writerows(metricas["evolucion"])


def main():
    reportes = cargar_reportes()
    defectos = cargar_defectos()

    if not reportes:
        print("No hay informes históricos para calcular métricas.")
        print(f"Carpeta consultada: {HISTORIAL_REPORTES}")
        print("Ejecuta primero motor_reconciliacion.py.")
        return

    metricas = construir_metricas(reportes, defectos)
    guardar_resultados(metricas)

    print("\n=== MÉTRICAS DE DATA MIGRATION QA ===")
    print(f"Ejecuciones: {metricas['total_ejecuciones']}")
    print(f"Ejecuciones PASS: {metricas['ejecuciones_aprobadas']}")
    print(f"Ejecuciones FAIL: {metricas['ejecuciones_fallidas']}")
    print(f"Controles ejecutados: {metricas['controles_ejecutados']}")
    print(f"Controles PASS: {metricas['controles_aprobados']}")
    print(f"Controles FAIL: {metricas['controles_fallidos']}")
    print(
        "Tasa de aprobación: "
        f"{metricas['tasa_aprobacion_controles_pct']}%"
    )
    print(f"Defectos históricos: {metricas['total_defectos_historicos']}")

    print("\nDefectos por severidad:")
    for severidad, cantidad in metricas["defectos_por_severidad"].items():
        print(f"  {severidad}: {cantidad}")

    print("\nDefectos por estado:")
    for estado, cantidad in metricas["defectos_por_estado"].items():
        print(f"  {estado}: {cantidad}")

    print(f"\nInforme JSON: {SALIDA_JSON}")
    print(f"Evolución CSV: {SALIDA_CSV}")


if __name__ == "__main__":
    main()
'@ | Set-Content -Path .\python\generar_metricas_qa.py -Encoding utf8
