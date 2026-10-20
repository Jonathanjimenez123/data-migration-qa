from app.database import get_connection

conn = get_connection()
try:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name IN ('qa_runs', 'qa_checks', 'qa_differences')
            ORDER BY table_name, ordinal_position
        """)
        rows = cur.fetchall()

        if not rows:
            print("No se encontraron las tablas esperadas en el esquema public.")
        else:
            for row in rows:
                print(row)
finally:
    conn.close()
