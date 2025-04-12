import random
import datetime
import mysql.connector
from faker import Faker

fake = Faker()
countries = ['France', 'Germany', 'USA', 'Canada', 'Spain', 'Brazil', 'Japan']
call_types = ['incoming', 'outgoing']

conn = mysql.connector.connect(
    host='localhost',
    user='super',
    password='root',
    database='aiql'
)
cursor = conn.cursor()

cursor.execute("DELETE FROM calls")

for i in range(500):
    timestamp = fake.date_time_between(start_date='-60d', end_date='now')
    duration = round(random.uniform(1, 30), 2)
    origin = random.choice(countries)
    dest = random.choice([c for c in countries if c != origin])
    ctype = random.choice(call_types)

    cursor.execute("""
        INSERT INTO calls (timestamp, duration_minutes, origin_country, destination_country, call_type)
        VALUES (%s, %s, %s, %s, %s)
    """, (timestamp, duration, origin, dest, ctype))

conn.commit()
cursor.close()
conn.close()
print("Inserted 500 fake call records.")
