import sqlite3

con = sqlite3.connect("fraud_detection.db")

print("=== tables ===")
for row in con.execute("SELECT name FROM sqlite_master WHERE type=\"table\"").fetchall():
    print(row[0])

print()
print("=== predictions schema ===")
for row in con.execute("PRAGMA table_info(predictions)").fetchall():
    print(row)

print()
print("=== transactions schema ===")
for row in con.execute("PRAGMA table_info(transactions)").fetchall():
    print(row)

print()
print("=== prediction counts by risk_category ===")
for row in con.execute("SELECT risk_category, COUNT(*) FROM predictions GROUP BY risk_category ORDER BY 1").fetchall():
    print(row)

print()
print("=== total predictions ===")
print(con.execute("SELECT COUNT(*) FROM predictions").fetchone()[0])

con.close()