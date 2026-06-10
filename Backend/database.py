import os
import uuid
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host":            os.getenv("PGHOST",     "ep-icy-silence-aq70iajz.c-8.us-east-1.aws.neon.tech"),
    "database":        os.getenv("PGDATABASE", "neondb"),
    "user":            os.getenv("PGUSER",     "neondb_owner"),
    "password":        os.getenv("PGPASSWORD", "npg_4yXJFPikOV2u"),
    "sslmode":         "require",
    "connect_timeout": 10,
}


def get_connection():
    print(f"[DB] Neon холбогдож байна...")
    conn = psycopg2.connect(**DB_CONFIG)
    print(f"[DB] ✅ Холболт амжилттай")
    return conn


def check_connection():
    try:
        get_connection().close()
        return True
    except Exception as e:
        print(f"[DB] ❌ Холболт амжилтгүй: {e}")
        return False


def get_schema():
    print(f"[DB] Schema уншиж байна...")
    conn = get_connection()
    cur  = conn.cursor()
    # public schema-н БҮГД хүснэгтийг автоматаар уншина
    cur.execute("""
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position;
    """)
    rows = cur.fetchall()
    conn.close()
    schema = {}
    for table, col, dtype in rows:
        schema.setdefault(table, []).append(f"{col} ({dtype})")
    print(f"[DB] ✅ Schema: {list(schema.keys())}")
    return "\n".join(
        f"Table: {t}\n  Columns: {', '.join(c)}"
        for t, c in schema.items()
    )


def run_query(sql):
    import re
    if re.search(r'\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER)\b', sql.upper()):
        raise ValueError("Зөвхөн SELECT query зөвшөөрнө!")
    print(f"[DB] SQL ажиллуулж байна:\n     {sql[:150]}")
    conn = get_connection()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(sql)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    print(f"[DB] ✅ {len(rows)} мөр буцаалаа")
    return rows


def ensure_user(user_id):
    print(f"[DB] User шалгаж байна: {user_id[:8]}...")
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT id FROM baynaa.users WHERE id = %s", (user_id,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO baynaa.users (id, name, email, role, password, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, f"User {user_id[:8]}", f"{user_id[:8]}@app.com", "user", "hashed", True))
        conn.commit()
        print(f"[DB] ✅ Шинэ user үүслээ: {user_id[:8]}...")
    else:
        print(f"[DB] ✅ User байна: {user_id[:8]}...")
    conn.close()


def get_session_by_user(user_id):
    print(f"[DB] Session хайж байна → user={user_id[:8]}...")
    conn = get_connection()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT id, title, started_at, msg_count
        FROM baynaa.sessions
        WHERE user_id = %s
        ORDER BY started_at DESC
        LIMIT 1
    """, (user_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        print(f"[DB] ✅ Session олдлоо: {row['id'][:8]}... ({row['msg_count']} мессеж)")
    else:
        print(f"[DB] Session олдсонгүй → шинэ үүсгэнэ")
    return dict(row) if row else None


def create_session(user_id, channel='web', title='New Chat'):
    ensure_user(user_id)
    sid  = str(uuid.uuid4())
    conn = get_connection()
    cur  = conn.cursor()
    full_title = f"[{channel.upper()}] {title[:240]}"
    cur.execute("""
        INSERT INTO baynaa.sessions (id, user_id, title, started_at, msg_count)
        VALUES (%s, %s, %s, NOW(), 0)
    """, (sid, user_id, full_title))
    conn.commit()
    conn.close()
    print(f"[DB] ✅ Session үүслээ: {sid[:8]}...  title='{full_title[:40]}'")
    return sid


def get_sessions(user_id, limit=20):
    conn = get_connection()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT id, title, started_at, msg_count
        FROM baynaa.sessions
        WHERE user_id = %s
        ORDER BY started_at DESC
        LIMIT %s
    """, (user_id, limit))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def save_message(session_id, role, content, token_count=0):
    mid  = str(uuid.uuid4())
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        INSERT INTO baynaa.messages (id, session_id, role, content, token_count, created_at)
        VALUES (%s, %s, %s, %s, %s, NOW())
    """, (mid, session_id, role, content, token_count))
    cur.execute(
        "UPDATE baynaa.sessions SET msg_count = msg_count + 1 WHERE id = %s",
        (session_id,)
    )
    conn.commit()
    conn.close()
    print(f"[DB] ✅ Message хадгалагдлаа [{role}]: {content[:50]}...")
    return mid


def get_messages(session_id, limit=50):
    print(f"[DB] Messages татаж байна → session={session_id[:8]}... limit={limit}")
    conn = get_connection()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT role, content, created_at
        FROM baynaa.messages
        WHERE session_id = %s
        ORDER BY created_at ASC
        LIMIT %s
    """, (session_id, limit))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    print(f"[DB] ✅ {len(rows)} мессеж буцаалаа")
    return rows


def save_llm_log(message_id, model, prompt_tokens, completion_tokens, latency_ms, use_case="chat"):
    lid  = str(uuid.uuid4())
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        INSERT INTO baynaa.llm_logs
            (id, message_id, model, prompt_tokens, completion_tokens, cost_usd, latency_ms, use_case)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        lid, message_id, model,
        prompt_tokens, completion_tokens,
        round((prompt_tokens * 0.00000015) + (completion_tokens * 0.0000006), 8),
        latency_ms, use_case
    ))
    conn.commit()
    conn.close()
    print(f"[DB] ✅ LLM log хадгалагдлаа  use_case={use_case}  latency={latency_ms}ms")
