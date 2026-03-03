import sqlite3

# tuotannossa lienee users_main.db
DB_FILE = "users_test_030326.db"

def add_has_responded_column():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    try:
        c.execute("""
            ALTER TABLE users
            ADD COLUMN has_responded INTEGER DEFAULT 0
        """)
        print("has_responded column added.")
    except sqlite3.OperationalError:
        print("has_responded column already exists.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_has_responded_column()