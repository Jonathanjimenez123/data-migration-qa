
import psycopg
from getpass import getpass

print("DATA QA - CONEXION A POSTGRESQL")

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
            cursor.execute("""
                SELECT
                    current_database(),
                    current_user,
                    version()
            """)
            base, usuario, version = cursor.fetchone()

            print("\nCONEXION EXITOSA")
            print(f"Base de datos: {base}")
            print(f"Usuario: {usuario}")
            print(f"Servidor: {version.split(',')[0]}")

except psycopg.OperationalError as error:
    print("\nERROR DE CONEXION")
    print("Revisa la contraseña, el servicio y los datos de conexión.")
    print(f"Detalle: {error}")

