import sqlite3

DB_PATH = "data.db"

# Kaikki lisättävät sarakkeet {nimi: SQL-tyyppi}
NEW_COLUMNS = {
    "state_checklist": "TEXT",
    "organization_type": "TEXT",
    "organization_type_other": "TEXT",
    "prof_position": "TEXT",
    "prof_position_other": "TEXT",
    "years_experience": "INTEGER"
}

def column_exists(cursor, table, column):
    """Check if a column already exists in a table."""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns

def alter_database():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    print("🔍 Checking for missing columns...")

    for col, col_type in NEW_COLUMNS.items():
        if not column_exists(c, "responses", col):
            print(f"➡️ Adding column: {col} ({col_type})")
            c.execute(f"ALTER TABLE responses ADD COLUMN {col} {col_type}")
        else:
            print(f"✔️ Column already exists: {col}")

    conn.commit()
    conn.close()

    print("\n✅ Database altered successfully!")

if __name__ == "__main__":
    alter_database()
