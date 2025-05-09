import sqlite3
from tabulate import tabulate

# Path to the database file
db_path = "results.db"

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Fetch table contents
cursor.execute("SELECT * FROM submissions;")
rows = cursor.fetchall()
columns = [description[0] for description in cursor.description]

# Display table using tabulate
print(tabulate(rows, headers=columns, tablefmt="pretty"))

# Close connection
conn.close()
