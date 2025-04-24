import ollama
import mysql.connector
import sys

try:
    from config import DB_CONFIG
except ImportError:
    print("Error: config.py not found.", file=sys.stderr)
    print("Make sure config.py exists in the same directory.", file=sys.stderr)
    sys.exit(1)
from typing import List, Tuple, Any, Optional

ollama_host = "http://localhost:11434"
ollama_model = "sqlcoder:latest" # change this to the model you want to use

## Make sure to change this schema to reflect the database you would like to query ##
db_schema = """
-- Database Schema for MySQL
-- Table structure for table `calls`

CREATE TABLE calls (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME,
    duration_minutes FLOAT,
    origin_country VARCHAR(50),
    destination_country VARCHAR(50),
    call_type ENUM('incoming', 'outgoing')
);

-- Relevant indexes might exist, e.g.:
-- CREATE INDEX idx_origin_country ON calls(origin_country);
-- CREATE INDEX idx_call_type ON calls(call_type);

-- Important Notes for SQL Generation:
-- 1. Columns are: id, timestamp, duration_minutes, origin_country, destination_country, call_type.
-- 2. Available countries in 'origin_country' and 'destination_country' include: 'Germany', 'France', 'USA', 'Canada', 'Spain', 'Brazil', 'Japan'. Ensure correct capitalisation and spelling.
-- 3. 'call_type' can only be 'incoming' or 'outgoing'.
-- 4. Use standard MySQL syntax. Do not use table aliases unless necessary for complex joins (not needed here).
-- 5. Do not use backticks around standard column or table names unless they are reserved words (none are here).
"""

## defining the prompt structure 
def build_prompt(user_question: str) -> str:
    # we only want the sql query!!.
    return f"""You are an expert MySQL database assistant.
Based SOLELY on the database schema provided below, convert the user's question into a single, valid MySQL query.

Database Schema:
```sql
{db_schema}
User Question:
"{user_question}"
MySQL Query:
"""

## configuring ollama + cleaning the response
def generate_sql_with_ollama(prompt: str) -> Optional[str]:
    try:
        print(f"\n🤖 Sending request to Ollama (model: {ollama_model})...")
        response = ollama.generate(
            model=ollama_model,
            prompt=prompt,
            stream=False, # get full response
            options={
                "temperature": 0.0, # the lower the value the more deterministic the response is
                "stop": ["--", ";", "\n\n", "```", "</s>"] # a stop just in case
            }
        )

        generated_text = response['response'].strip()
        # print(f"raw: '{generated_text}'")

        # cleaning the sql
        if generated_text.lower().startswith("<s>"):
             generated_text = generated_text[len("<s>"):].strip()

        if generated_text.lower().startswith(("```sql", "```mysql")):
            generated_text = generated_text.split('\n', 1)[-1] # remove first line
        if generated_text.startswith("```"):
             generated_text = generated_text[len("```"):].strip()
        if generated_text.endswith("```"):
            generated_text = generated_text[:-len("```")].strip()

        # removing the standard phrasing at the beginning
        phrases_to_remove = [
            "MySQL Query:", "SQL Query:", "Here is the SQL query:",
            "Here's the SQL query:"
        ]
        for phrase in phrases_to_remove:
            if generated_text.lower().startswith(phrase.lower()):
                generated_text = generated_text[len(phrase):].strip()
                break

        # find the most likely keyword
        sql_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "WITH"]
        lines = generated_text.splitlines()
        sql_query = ""
        start_found = False
        cleaned_lines = []

        # looking for the start of the SQL query
        for l in lines:
            stripped_line = l.strip()
            if not start_found and (not stripped_line or stripped_line.startswith('--')):
                continue
            if not start_found:
                for keyword in sql_keywords:
                    if stripped_line.upper().startswith(keyword):
                        start_found = True
                        break
            if start_found:
                if stripped_line.startswith("Explanation:") or stripped_line.startswith("Note:"):
                    break
                if stripped_line == "```":
                    break
                cleaned_lines.append(l)

        if cleaned_lines:
            sql_query = "\n".join(cleaned_lines).strip()
        else:
            # if no keyword is found it just falls back on this formatting
            sql_query = generated_text.split('--')[0].strip() 

        # prevent from ; interrupting 
        if sql_query.endswith(';'):
            sql_query = sql_query[:-1].strip()

        if not sql_query:
            print("⚠️ Warning: Model returned empty or a weird SQL response.")
            return None

        # add the ; at the end
        sql_query += ';'

        return sql_query

    except Exception as e:
        print(f"\n❌ Error interacting with Ollama: {e}")
        print(f"   Is the Ollama server running and model '{ollama_model}' downloaded?")
        return None


# executing query and returning result
def run_sql_query(query: str) -> Optional[List[Tuple[Any, ...]]]:
    results: Optional[List[Tuple[Any, ...]]] = None
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print(f"Executing SQL: {query}")
        cursor.execute(query)

        if cursor.description:
            results = cursor.fetchall()
            print(f"Query returned {len(results)} rows")
        else:
            # if you wanted to manipulate database
            print(f"You're not allowed to edit the db.")

        return results 

    except mysql.connector.Error as err:
        print(f"❌ SQL Execution Error: {err}")
        print(f"   Query: {query}")
        return None
    except Exception as e:
        print(f"❌ Error occurred during SQL execution: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

## function for user interaction
def main():
    print("--- AIQL SQL Query Generator ---\n")
    print(f"Using Ollama model: {ollama_model}\n")
    print("Type your question about the call data, or 'q' to quit.")

    try:
        ollama.list()
        print("✅ Ollama connected.")
    except Exception as e:
        print(f"❌ Error connecting to Ollama at {ollama_host}: {e}", file=sys.stderr)
        print("   Make sure you have ollama installed.", file=sys.stderr)
        sys.exit(1)

    try:
        conn_test = mysql.connector.connect(**DB_CONFIG, connection_timeout=5)
        conn_test.close()
        print("✅ Database connected.")
    except mysql.connector.Error as err:
        print(f"❌ Database Connection Error: {err}", file=sys.stderr)
        print("   Check config.py is correct and ensure MySQL is running,", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during DB check: {e}", file=sys.stderr)
        sys.exit(1)

## main loop
    while True:
        try:
            user_input = input("\nWhat would you like to know? > ")
            if user_input.lower() == 'q':
                print("👋 Bye...")
                break
            if not user_input.strip():
                continue

            # build the prompt
            prompt = build_prompt(user_input)

            # generating the sql
            sql_query = generate_sql_with_ollama(prompt)

            if sql_query:
                print("\n✨ Generated SQL Query:")
                print("-" * 20)
                print(sql_query)
                print("-" * 20)

                # confirm the query
                confirm = input("Execute this query? (y/n): ")
                if confirm.lower() != 'y':
                    print("Query not executed.")
                    continue

                results = run_sql_query(sql_query) 

                
                if results is not None:
                    print("\n📊 Results:")
                    if results:
                        # pretty print
                        for row in results:
                            print(row)
                    else:
                        print("Empty")


            else:
                print("Could not generate SQL query try rephrasing.")

        except KeyboardInterrupt:
            print("\n👋 Bye...")
            break

        # handling the loop in case of input issues or something
        except Exception as e:
            print(f"\n❌ Error in the main loop: {e}")

if __name__ == "__main__":
    main()
