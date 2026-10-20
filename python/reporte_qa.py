
from pathlib import Path
import json
from datetime import datetime

# Datos ficticios para nuestras pruebas
clientes = [
    {"id": 1, "nombre": "Ana", "email": "ana@gmail.com"},
    {"id": 2, "nombre": "Carlos", "email": None},
    {"id": 3, "nombre": "Laura", "email": "laura@gmail.com"},
    {"id": 3, "nombre": "Pedro", "email": "pedro@gmail.com"},
    {"id": 5, "nombre": "Sofia", "email": "sofia@gmail.com"},
]

# Ejecutar validaciones
emails_vacios = [
    c for c in clientes if not c["email"]
]

ids = [c["id"] for c in clientes]
ids_duplicados = sorted({
    identificador for identificador in ids
    if ids.count(identificador) > 1
})

pruebas = [
    {
        "prueba": "EMAIL_OBLIGATORIO",
        "estado": "FAIL" if emails_vacios else "PASS",
        "defectos": [
            f"Cliente ID {c['id']}: {c['nombre']} sin email"
            for c in emails_vacios
        ],
    },
    {
        "prueba": "ID_UNICO",
        "estado": "FAIL" if ids_duplicados else "PASS",
        "defectos": [
            f"ID duplicado: {identificador}"
            for identificador in ids_duplicados
        ],
    },
]

aprobadas = sum(p["estado"] == "PASS" for p in pruebas)
fallidas = sum(p["estado"] == "FAIL" for p in pruebas)

reporte = {
    "fecha": datetime.now().isoformat(timespec="seconds"),
    "total_registros": len(clientes),
    "pruebas_aprobadas": aprobadas,
    "pruebas_fallidas": fallidas,
    "resultados": pruebas,
}

# Guardar el reporte en la carpeta reports
carpeta = Path(__file__).resolve().parent.parent / "reports"
carpeta.mkdir(parents=True, exist_ok=True)

archivo = carpeta / "reporte_qa.json"
archivo.write_text(
    json.dumps(reporte, indent=4, ensure_ascii=False),
    encoding="utf-8",
)

print("REPORTE DATA QA")
print("-" * 30)
print(f"Registros analizados: {len(clientes)}")
print(f"PASS: {aprobadas}")
print(f"FAIL: {fallidas}")

for prueba in pruebas:
    print(f"\n{prueba['prueba']}: {prueba['estado']}")
    for defecto in prueba["defectos"]:
        print(f"  - {defecto}")

print(f"\nReporte guardado en: {archivo}")
