"""Builds inventory.db -- the SQLite database file the MCP server reads.

Run once:  python make_db.py
Creates inventory.db in this folder with 4 bearings. Run it again any
time to reset the database back to these values.
"""

import os
import sqlite3

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventory.db")

conn = sqlite3.connect(DB)
conn.execute("DROP TABLE IF EXISTS inventory")
conn.execute("""CREATE TABLE inventory (
    sku TEXT PRIMARY KEY,
    description TEXT,
    stock INTEGER,
    price REAL)""")

rows = [
    ("BRG-6205-2RS", "Deep groove ball bearing 25x52x15", 4200, 4.80),
    ("BRG-UCF205", "Flange bearing, 4-bolt, 25mm bore", 850, 99.99),
    ("BRG-UCF206", "Flange bearing, 4-bolt, 30mm bore", 1200, 21.75),
    ("BRG-UC205", "Insert bearing 25mm bore", 3000, 9.20),
]
conn.executemany("INSERT INTO inventory VALUES (?,?,?,?)", rows)
conn.commit()

count = conn.execute("SELECT COUNT(*) FROM inventory").fetchone()[0]
conn.close()
print(f"Done. inventory.db created with {count} rows.")
