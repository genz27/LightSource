import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), os.pardir, "lightsource.db")
db_path = os.path.normpath(db_path)
if not os.path.exists(db_path):
    print("sqlite db not found")
    raise SystemExit(1)

conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("PRAGMA table_info(users)")
cols = [r[1] for r in cur.fetchall()]
if "username" not in cols:
    cur.execute("ALTER TABLE users ADD COLUMN username TEXT")
    cur.execute("UPDATE users SET username = substr(email, 1, instr(email, '@')-1) WHERE username IS NULL OR username = ''")
    try:
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users(username)")
    except Exception:
        pass
    conn.commit()
    print("added username column")
else:
    print("username exists")
conn.close()