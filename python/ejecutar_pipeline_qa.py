import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTHON_DIR = ROOT / "python"

PASOS = [
    {
        "nombre": "Reconciliacion de origen y destino",
        "script": PYTHON_DIR / "motor_reconciliacion.py",
    },
    {
        "nombre": "Generacion de defectos",
        "script": PYTHON_DIR / "generar_defectos.py",
    },
    {
        "nombre": "Calculo de metricas",
        "script": PYTHON_DIR / "generar_metricas_qa.py",
    },
]


def ejecutar_paso(nombre, script):
    print("\n" + "=" * 65)
    print(f"PASO: {nombre}")
    print(f"Archivo: {script.name}")
    print("=" * 65)

    if not script.exists():
        print(f"ERROR: no existe el archivo {script}")
        return False

    resultado = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(ROOT),
        check=False,
    )

    if resultado.returncode != 0:
        print(f"ERROR: el paso termino con codigo {resultado.returncode}")
        return False

    print(f"OK: {nombre}")
    return True


def main():
    inicio = datetime.now(timezone.utc)

    print("=" * 65)
    print("PIPELINE INTEGRAL - DATA MIGRATION QA")
    print(f"Inicio UTC: {inicio.isoformat()}")
    print("=" * 65)

    for paso in PASOS:
        if not ejecutar_paso(paso["nombre"], paso["script"]):
            print("\nPIPELINE INTERRUMPIDO.")
            print("Corrige el error indicado antes de volver a ejecutarlo.")
            raise SystemExit(1)

    fin = datetime.now(timezone.utc)

    print("\n" + "=" * 65)
    print("PIPELINE FINALIZADO CORRECTAMENTE")
    print(f"Inicio UTC: {inicio.isoformat()}")
    print(f"Fin UTC:    {fin.isoformat()}")
    print(f"Duracion:   {round((fin - inicio).total_seconds(), 2)} segundos")
    print("=" * 65)
    print("Informes:")
    print(ROOT / "reports" / "reporte_reconciliacion.json")
    print(ROOT / "reports" / "metricas_qa.json")
    print(ROOT / "reports" / "evolucion_ejecuciones.csv")
    print(ROOT / "defects" / "defectos_migracion.csv")
    print(ROOT / "defects" / "historial_defectos.csv")


if __name__ == "__main__":
    main()
