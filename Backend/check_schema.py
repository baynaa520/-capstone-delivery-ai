from database import get_connection

conn = get_connection()
cur  = conn.cursor()

for schema in ['baynaa']:
    for table in ['users', 'sessions', 'messages', 'llm_logs']:
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """, (schema, table))
        rows = cur.fetchall()
        print(f"\n=== {schema}.{table} ===")
        for r in rows:
            print(f"  {r[0]} ({r[1]})")

conn.close()