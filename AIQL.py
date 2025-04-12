from flask import Flask, request, jsonify, render_template
import mysql.connector
import subprocess
from config import DB_CONFIG

app = Flask(__name__)

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

@app.route('/')
def home():
    """Render the home page (index.html)"""
    return render_template('index.html')

@app.route('/query', methods=['POST'])
def handle_query():
    """Handles the query and returns the results"""
    try:
        user_question = request.json['question']
        prompt = build_sql_prompt(user_question)
        sql_query = generate_sql(prompt)
        
        results = run_sql_query(sql_query)

        formatted_results = [{"row": row} for row in results]

        return jsonify({"sql_query": sql_query, "results": formatted_results})

    except Exception as e:
        return jsonify({"error": f"SQL Query failed: {str(e)}"}), 400

if __name__ == "__main__":
    app.run(debug=True)
