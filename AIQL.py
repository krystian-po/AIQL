import mysql.connector
from config import DB_CONFIG
import subprocess

SCHEMA_CONTEXT = """
Database schema:
Table: calls(id, timestamp, duration_minutes, origin_country, destination_country, call_type)

Common questions to ask:
- What is the average duration of calls from a specific country?
- How many calls were made from a specific country?
- What is the total call duration for a given call type and country?
- Which country has the most outgoing calls?

Inside the database the countries are Germany, France, Japan, France, Spain, USA, Canada, Brazil.
For the country names make sure you capitalise, not make any typos or shortcuts for the countries.

Do not take shortcuts for SQL commands.

"""

def build_sql_prompt(user_question):
    """Builds the prompt to send to TinyLlama."""
    return f"""{SCHEMA_CONTEXT}

Convert the following question into a valid MySQL SQL query:

Question: "{user_question}"
SQL:"""

def run_sql_query(query):
    """Executes the SQL query on the MySQL database and returns the results."""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

### I have tried tinyllama, deepseek 1b. tinyllama kinda works but sqlcoder is very good
def generate_sql(prompt):
    """Generates the SQL query from the prompt using TinyLlama."""
    result = subprocess.run(
        ["ollama", "run", "sqlcoder", prompt],
        stdout=subprocess.PIPE,
        text=True
    )
    
    response = result.stdout.strip()
    
    if "SQL:" in response:
        sql_query = response.split("SQL:")[-1].strip()
    else:
        sql_query = response
    
    return sql_query

def main():
    """Main function to interact with the user and generate SQL queries."""
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
