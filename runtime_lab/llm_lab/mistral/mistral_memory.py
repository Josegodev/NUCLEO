import sqlite3
from pathlib import Path

# RUTA ESTABLE: absoluta, no relativa al cwd
DB_PATH = Path(__file__).resolve().parent / "memoria.db"

def init_db():
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS mensajes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Base de datos creada/verificada:", DB_PATH)

