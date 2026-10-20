
import sys
from pathlib import Path

print("=" * 40)
print("DATA QA - PRIMERA PRUEBA")
print("=" * 40)

print(f"Python instalado: PASS ({sys.version.split()[0]})")

proyecto = Path.cwd()
print(f"Carpeta del proyecto: {proyecto}")

carpetas = ["sql", "python", "reports", "test-data", "defects"]

for carpeta in carpetas:
    ruta = proyecto / carpeta
    resultado = "PASS" if ruta.is_dir() else "FAIL"
    print(f"Carpeta {carpeta}: {resultado}")

print("=" * 40)