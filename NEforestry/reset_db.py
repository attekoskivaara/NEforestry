import sqlite3

conn = sqlite3.connect("data.db")
cursor = conn.cursor()

# Empty a single table
cursor.execute("DELETE FROM responses")

# Reset auto-increment
cursor.execute("DELETE FROM sqlite_sequence WHERE name='responses'")

conn.commit()
conn.close()
