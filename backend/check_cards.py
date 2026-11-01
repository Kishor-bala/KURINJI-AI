import sqlite3

conn = sqlite3.connect('backend/data/vocabulary.db')
c = conn.cursor()
tables = [row[0] for row in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Tables:", tables)

for t in tables:
    count = c.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
    cols = [col[1] for col in c.execute(f"PRAGMA table_info({t})").fetchall()]
    print(f"Table {t} ({count} rows): {cols}")

print("\nSample recordings with words:")
query = """
SELECT r.clip_id, r.word_id, v.english_meaning, v.tamil_meaning, v.optional_romanised_pronunciation, r.clip_file 
FROM recordings r 
LEFT JOIN vocabulary v ON r.word_id = v.word_id 
LIMIT 30
"""
try:
    for row in c.execute(query).fetchall():
        clean_row = [str(x).encode('ascii', 'backslashreplace').decode('ascii') for x in row]
        print(" | ".join(clean_row))
except Exception as e:
    print("Error:", e)

conn.close()
