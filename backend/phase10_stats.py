import sqlite3

con = sqlite3.connect("fraud_detection.db")

# Basic stats
total = con.execute('SELECT COUNT(*) FROM transactions').fetchone()[0]
total_pred = con.execute('SELECT COUNT(*) FROM predictions').fetchone()[0]
print(f'transactions: {total}, predictions: {total_pred}')

# Fraud-related stats
print()
print('=== predictions by predicted_class ===')
for row in con.execute('SELECT predicted_class, COUNT(*) FROM predictions GROUP BY predicted_class').fetchall():
    print(row)

print()
print('=== predictions by risk_category ===')
for row in con.execute('SELECT risk_category, COUNT(*) FROM predictions GROUP BY risk_category').fetchall():
    print(row)

print()
print('=== fraud predictions count ===')
print(con.execute("SELECT COUNT(*) FROM predictions WHERE predicted_class='fraud'").fetchone()[0])

print()
print('=== score range ===')
print(con.execute('SELECT MIN(risk_score), MAX(risk_score) FROM predictions').fetchone())

con.close()