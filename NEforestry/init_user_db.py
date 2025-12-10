import sqlite3
import hashlib

DB_FILE = "users.db"  # new database file

# ---------------------------
# Helper functions
# ---------------------------

def create_users_table():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password_hash TEXT
        )
    """)
    conn.commit()
    conn.close()
    print(f"Users table created in {DB_FILE}.")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(email, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (email, password_hash) VALUES (?, ?)",
                  (email, hash_password(password)))
        conn.commit()
        print(f"User {email} added successfully.")
    except sqlite3.IntegrityError:
        print(f"User {email} already exists.")
    finally:
        conn.close()

# ---------------------------
# Run initialization
# ---------------------------

if __name__ == "__main__":
    create_users_table()

    # Add users here (run once)
    add_user("alice@example.com", "password123")
    add_user("bob@example.com", "securepass")
    add_user("attekosk@gmail.com", "passu")
    add_user("atte.koskivaara@luke.fi", "security")
    add_user("aliisa.koivisto@gmail.com", "HildaHelvi")
    add_user("katja.lahtinen@luke.fi", "umass2025")
    add_user("vision2060@umass.edu", "vision2060")
    add_user("clouston@umass.edu", "mountsugarloaf")
    add_user("tuula.packalen@luke.fi", "luke2025")

