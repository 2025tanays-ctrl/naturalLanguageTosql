# QueryCraft — Viva Questions & Answers

**Student:** Tanay Siddharth Shelar | **ID:** 150096725092

---

## Q1. What does this application do?

**A:** QueryCraft converts natural language questions into SQL queries using the OpenAI API. A user types a question like "Show the five highest-paid employees," and the app generates a valid SQLite SELECT query, validates it for safety, executes it against a sample database, and displays the results — along with a unique run ID proving the workflow completed.

---

## Q2. What is prompt engineering, and how did you use it?

**A:** Prompt engineering means crafting the text instructions sent to an AI model to influence the quality and format of its output. I created three versions: **v1_basic** (minimal — just asks for SQL), **v2_structured** (adds the schema, dialect, and format rules), and **v3_refined** (adds safety constraints, ambiguity handling, and a strict structured output format). Each version produces noticeably different SQL quality.

---

## Q3. Why is SQL safety validation necessary?

**A:** AI models can generate any text, including dangerous SQL commands like `DROP TABLE` or `DELETE FROM employees`. The application treats all AI-generated SQL as untrusted input. It checks for blocked keywords (INSERT, UPDATE, DELETE, DROP, etc.), parses the SQL into an abstract syntax tree using `sqlglot`, verifies that exactly one SELECT statement is present, and confirms all referenced tables exist in the schema. Only queries that pass all checks are executed.

---

## Q4. What is the difference between execution success and semantic correctness?

**A:** Execution success means the SQL ran without a database error. Semantic correctness means the results actually answer the intended question. For example, `SELECT * FROM employees ORDER BY salary LIMIT 5` executes successfully but returns employees in arbitrary order — not the top five earners. The evaluator compares actual results against reference answers to catch this distinction.

---

## Q5. How does the automation workflow work?

**A:** When a user submits a question, the `automation.py` module orchestrates a trigger-action pipeline: (1) validate the question, (2) load the prompt, (3) get the schema, (4) call the AI, (5) validate the SQL, (6) execute it, (7) compare with reference answers if available, (8) save all data to the `runs` database table, and (9) return a unique run ID. Every step's outcome is recorded regardless of success or failure.

---

## Q6. Why use SQLite for both the main database and storage?

**A:** SQLite is file-based, requires no installation, and works identically on Windows, macOS, and Linux. This makes the project fully portable — another person can clone the repo, install Python dependencies, and run the app without setting up any database server.

---

## Q7. How do you prevent the AI from inventing tables or columns?

**A:** The v2 and v3 prompts explicitly include the database schema and instruct the model to use only the listed tables and columns. The v3 prompt further instructs the model to respond with `CANNOT_ANSWER:` if the question references non-existent schema elements. Additionally, the SQL validator parses the generated query and rejects any reference to tables outside the approved set.

---

## Q8. How are the five reference test cases used?

**A:** Each test case has a known correct SQL query, an expected row count, and sometimes column checks. The test runner executes the reference SQL directly (bypassing the AI), compares the actual database results to the expected values, and marks each case as PASS or FAIL. This gives a deterministic baseline that works without an API key.

---

## Q9. How is sensitive data like the API key protected?

**A:** The API key is stored only in a `.env` file that is excluded from version control via `.gitignore`. The application loads it using `python-dotenv`. Error messages and logs never print the key value — if the key is missing, the app shows `OPENAI_API_KEY not set in environment` without revealing any credential.

---

## Q10. How would you scale this application?

**A:** Currently it uses SQLite and a single Streamlit process. To scale: replace SQLite with PostgreSQL for concurrent access, use an async API client, add Redis caching for repeated questions, deploy with Docker and a reverse proxy, and add authentication for multi-user support. The modular design (separate `database.py`, `validator.py`, `ai_generator.py`) makes each component replaceable independently.
