# AIQL
Repo for AIQL, attempting to use ollama for a database querying chatbot.
** Note: if using large model like sqlcoder(7 billion parameters)(very large 4.1gb download) it requires a lot of compute so best to do on large VM or run it locally. For reference a 6 core 16 GB VM takes anywhere from 10-40 seconds depending on query complexity.

Instructions:

1. Install pre-requisites in requirements.txt.

2. Once ollama is installed, type "ollama" into terminal to confirm it's installed and download the model you want using "ollama run {model name}".
The model used for this example is sqlcoder: (https://ollama.com/library/sqlcoder) ~ feel free to test with other models: (https://ollama.com/search).
For this example, do "ollama run sqlcoder", this one is around a 4.1GB download.

4. Set up MySQL, create a database, create relevant tables and populate config.py or enter credentials for an existing database. I recommend that you create a user with SELECT privileges only just in case.

5. If you want to synthesise some data use data_synth.py, it creates 500 fake rows of call data but you can change it however you like. Otherwise skip this step.

6. Inside AIQL.py change the db_schema starting line 16 to match the tables you want to query and add relevant info that clarifies database details for the model (have a look to see what that may be).

7. If nothing weird happens, you should be good to ask you first question.

For best results I recommend making clear prompts, some example prompts that work for my specific example:
   ~ How many outgoing calls were made from Germany?
   ~ How many times was Japan a destination?
   ~ What is the average call duration from Brazil?
   ~ Which country received the most incoming calls?
   * Depending on the model, it's size and the data it is fine-tuned on, the results will vary *

If you have any issues/improvements, let me know.

