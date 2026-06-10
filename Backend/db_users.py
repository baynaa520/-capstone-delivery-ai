import uuid
import psycopg2
import psycopg2.extras
from database import get_connection


def init_users_table():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS app_users (
            id         VARCHAR(36)  PRIMARY KEY,
            google_id  VARCHAR(255) UNIQUE,
            email      VARCHAR(255) UNIQUE NOT NULL,
            name       VARCHAR(255),
            role       VARCHAR(20),
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    conn.close()
    print("[DB] ✅ app_users хүснэгт бэлэн")


def get_or_create_user(google_id: str, email: str, name: str) -> dict:
    conn = get_connection()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM app_users WHERE google_id = %s", (google_id,))
    user = cur.fetchone()
    if not user:
        uid = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO app_users (id, google_id, email, name)
            VALUES (%s, %s, %s, %s) RETURNING *
        """, (uid, google_id, email, name))
        conn.commit()
        user = cur.fetchone()
        print(f"[DB] ✅ Шинэ хэрэглэгч: {email}")
    else:
        print(f"[DB] ✅ Нэвтэрлээ: {email}  role={user.get('role')}")
    conn.close()
    return dict(user)


def update_user_role(user_id: str, role: str):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("UPDATE app_users SET role = %s WHERE id = %s", (role, user_id))
    conn.commit()
    conn.close()
    print(f"[DB] ✅ Role: {user_id[:8]}... → {role}")


def get_user_by_id(user_id: str) -> dict | None:
    conn = get_connection()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM app_users WHERE id = %s", (user_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None
