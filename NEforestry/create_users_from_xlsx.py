import sqlite3
import hashlib
import csv

# tietokanta tässä
DB_FILE = "users_test.db"
CSV_FILE = "recipients_test_230226.csv"

# ---------------------------
# Helper functions
# ---------------------------

def hash_password(password):
    """Hash password with SHA-256"""
    return hashlib.sha256(str(password).encode()).hexdigest()

def create_users_table():
    """Create users table if it doesn't exist"""
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

def add_user(email, password):
    """Add a user to the database"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (email, hash_password(password))
        )
        conn.commit()
        print(f"Added: {email}")
    except sqlite3.IntegrityError:
        print(f"Already exists: {email}")
    finally:
        conn.close()

# ---------------------------
# Main script
# ---------------------------

if __name__ == "__main__":

    create_users_table()

    # Lue CSV (oletetaan semicolon-separointi Excelistä)
    with open(CSV_FILE, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            email = row.get("email")
            password = row.get("password")

            if email and password:
                add_user(email.strip(), password.strip())

    print("All users processed.")