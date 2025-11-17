import sqlite3

def create_database():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        woodlands REAL,
        wildlands REAL,
        lumber REAL,
        paper REAL,
        fuelwood REAL,
        import_lumber REAL,
        import_paper REAL,
        construction_multistory REAL,
        construction_single REAL,
        manufacturing REAL,
        packaging REAL,
        other REAL
    )
    """)

    conn.commit()
    conn.close()
    print("Database and table created successfully.")

if __name__ == "__main__":
    create_database()
