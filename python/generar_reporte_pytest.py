
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARCHIVO_XML = RAIZ / "reports" / "resultados_pytest.xml"
ARCHIVO_JSON = RAIZ / "reports" / "reporte_pytest.json"


def main():
    if not ARCHIVO_XML.exists():
        print(f"No se encontró el reporte XML: {ARCHIVO_XML}")
        print("Ejecuta primero pytest con --junitxml.")
        return

    raiz_xml = ET.parse(ARCHIVO_XML).getroot()

    pruebas = []
    for caso in raiz_xml.iter("testcase"):
        fallo = caso.find("failure")
        error = caso.find("error")
        problema = fallo if fallo is not None else error

        if problema is not None:
            resultado = "FAIL"
            detalle = problema.get("message", "Prueba fallida")
        elif caso.find("skipped") is not None:
            resultado = "SKIP"
            detalle = "Prueba omitida"
        else:
            resultado = "PASS"
            detalle = "Sin errores"

        pruebas.append({
            "prueba": caso.get("name", "desconocida"),
            "archivo": caso.get("file", ""),
            "resultado": resultado,
            "detalle": detalle,
        })

    aprobadas = sum(p["resultado"] == "PASS" for p in pruebas)
    fallidas = sum(p["resultado"] == "FAIL" for p in pruebas)
    omitidas = sum(p["resultado"] == "SKIP" for p in pruebas)

    reporte = {
        "proyecto": "Data Migration QA",
        "fecha_ejecucion": datetime.now().isoformat(timespec="seconds"),
        "total_pruebas": len(pruebas),
        "aprobadas": aprobadas,
        "fallidas": fallidas,
        "omitidas": omitidas,
        "resultado_general": "PASS" if fallidas == 0 else "FAIL",
        "pruebas": pruebas,
    }

    ARCHIVO_JSON.write_text(
        json.dumps(reporte, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\n=== REPORTE DE QA ===")
    print(f"Total de pruebas: {len(pruebas)}")
    print(f"Aprobadas: {aprobadas}")
    print(f"Fallidas: {fallidas}")
    print(f"Omitidas: {omitidas}")
    print(f"Resultado general: {reporte['resultado_general']}")
    print(f"Reporte JSON: {ARCHIVO_JSON}")


if __name__ == "__main__":
    main()
