import mysql.connector
from config import DB_CONFIG
import subprocess

SCHEMA_CONTEXT = """
Database schema:
Table: calls(id, timestamp, duration_minutes, origin_country, destination_country, call_type)
"""

def build_sql_prompt(user_question):
    return f"""{SCHEMA_CONTEXT}

Convert the following question into a valid MySQL SQL query:

Question: "{user_question}"
SQL:"""

def run_sql_query(query):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def generate_sql(prompt):
    result = subprocess.run(
        ["ollama", "run", "tinyllama", prompt],
        stdout=subprocess.PIPE,
        text=True
    )
    return result.stdout.strip().split("SQL:")[-1].strip()

def main():
    while True:
        user_input = input("\n What would you like to know? (or 'q' to quit): ")
        if user_input.lower() == 'q':
            break

        prompt = build_sql_prompt(user_input)
        sql_query = generate_sql(prompt)

        print(f"\nGenerated SQL:\n{sql_query}")

        try:
            results = run_sql_query(sql_query)
            print("\nResults:")
            for row in results:
                print(row)
        except Exception as e:
            print("SQL failed:", e)

if __name__ == "__main__":
    main()
