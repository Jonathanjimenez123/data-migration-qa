
# Proyecto: Data Migration QA Automation
# Leccion 2: Validacion de calidad de datos

clientes = [
    {"id": 1, "nombre": "Ana", "email": "ana@gmail.com"},
    {"id": 2, "nombre": "Carlos", "email": None},
    {"id": 3, "nombre": "Laura", "email": "laura@gmail.com"},
    {"id": 3, "nombre": "Pedro", "email": "pedro@gmail.com"},
    {"id": 5, "nombre": "Sofia", "email": "sofia@gmail.com"},
]

print("=" * 45)
print("DATA QA - VALIDACION DE CLIENTES")
print("=" * 45)

# Prueba 1: detectar emails vacios
emails_vacios = [
    cliente for cliente in clientes
    if not cliente["email"]
]

print("\nTEST 1: EMAILS OBLIGATORIOS")
if emails_vacios:
    print("FAIL - Se encontraron emails vacios:")
    for cliente in emails_vacios:
        print(f"  Cliente ID {cliente['id']}: {cliente['nombre']}")
else:
    print("PASS - Todos los clientes tienen email")

# Prueba 2: detectar IDs duplicados
ids = [cliente["id"] for cliente in clientes]
ids_duplicados = sorted({
    identificador for identificador in ids
    if ids.count(identificador) > 1
})

print("\nTEST 2: IDS UNICOS")
if ids_duplicados:
    print(f"FAIL - IDs duplicados: {ids_duplicados}")
else:
    print("PASS - No hay IDs duplicados")

# Resumen
pruebas = [bool(emails_vacios), bool(ids_duplicados)]
fallidas = sum(pruebas)
aprobadas = len(pruebas) - fallidas

print("\n" + "=" * 45)
print(f"RESUMEN: {aprobadas} PASS / {fallidas} FAIL")
print("=" * 45)