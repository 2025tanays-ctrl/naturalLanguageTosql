# QueryCraft — Natural Language to SQL Query Assistant

**Student:** Tanay Siddharth Shelar  
**Student ID:** 150096725092  
**Category:** AI-Assisted Coding  

---

## 🌟 Overview

**QueryCraft** is a lightweight, modular, and portable AI-assisted application that translates natural-language questions into safe, executable SQLite SQL queries.

It features an end-to-end **trigger-action automation workflow**:
1. Validates the natural-language question.
2. Injects schema grounding through customizable prompt versions (`v1_basic`, `v2_structured`, `v3_refined`).
3. Enforces strict read-only structural validation via AST analysis (`sqlglot`).
4. Executes approved queries in read-only mode (`PRAGMA query_only = ON`).
5. Verifies query results against reference test benchmarks to distinguish execution success from semantic correctness.
6. Persists every run in SQLite storage with a unique Run ID.
7. Displays interactive results, query history, and prompt comparisons.

---

## 🛠 Tech Stack

- **Frontend:** Streamlit (`>=1.28.0`)
- **Backend / Language:** Python 3.10+
- **AI Integration:** OpenAI API (`>=1.0.0`)
- **SQL Parsing & AST Validation:** `sqlglot` (`>=19.0.0`)
- **Database & Persistence:** SQLite3 (standard library)
- **Data Manipulation:** `pandas` (`>=2.0.0`)
- **Configuration:** `python-dotenv` (`>=1.0.0`)
- **Testing:** `pytest` (`>=7.4.0`)

---

## 📁 Project Structure

```text
querycraft/
├── .env.example              # Environment variables template
├── .gitignore                 # Standard exclusions (secrets, databases, caches)
├── README.md                  # Comprehensive documentation and setup guide
├── requirements.txt           # Python package dependencies
├── app.py                     # Streamlit web application
├── prompts/                   # Three progressive prompt engineering templates
│   ├── v1_basic.txt           # Baseline: minimal question-to-SQL translation
│   ├── v2_structured.txt      # Schema grounding, dialect constraints, output format
│   └── v3_refined.txt         # Full safety, ambiguity rules, CANNOT_ANSWER fallback
├── src/                       # Modular source code
│   ├── __init__.py
│   ├── ai_generator.py        # OpenAI API integration and token extraction
│   ├── automation.py          # Trigger-action orchestrator and pipeline execution
│   ├── database.py            # SQLite schema initialization, seed data, execution
│   ├── evaluator.py           # 5 reference test cases & semantic verification
│   ├── storage.py             # SQLite persistence for runs and test history
│   └── validator.py           # Structural SQL AST parsing and keyword guardrails
├── tests/                     # 28 automated pytest unit and integration tests
│   ├── test_ai_generator.py   # Prompt loading, parsing, sanitized error handling
│   ├── test_automation.py     # End-to-end pipeline, empty input, CANNOT_ANSWER
│   ├── test_database.py       # Seed data, read-only pragmas, error handling
│   ├── test_evaluator.py      # Reference tests, execution vs correctness check
│   ├── test_storage.py        # Run persistence and history retrieval
│   └── test_validator.py      # AST validation, blocked keywords, SQL injection
└── docs/                      # Technical artifacts
    ├── test_report.md         # Actual test execution results and comparison
    ├── viva_questions.md      # 10 comprehensive viva questions and model answers
    └── workflow.mmd           # Mermaid diagram of the end-to-end processing pipeline
```

---

## 🚀 Quickstart & Installation

QueryCraft is designed to run locally on **Windows**, **macOS**, and **Linux** without external database servers.

### 1. Prerequisites
- Python 3.10 or later installed on your system.
- Git (optional, for cloning).

### 2. Clone or Extract Project
Navigate into the project directory:
```bash
cd querycraft
```

### 3. Create and Activate a Virtual Environment

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Copy `.env.example` to `.env`:

**macOS / Linux:**
```bash
cp .env.example .env
```

**Windows:**
```cmd
copy .env.example .env
```

Open `.env` in any text editor and add your Google Gemini API key (or OpenAI key):
```ini
# Google Gemini API Key (Recommended - Free Tier Available at https://aistudio.google.com/app/apikey)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash

# Optional: OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

> [!NOTE]
> You can obtain a free Gemini API key in 10 seconds at [Google AI Studio](https://aistudio.google.com/app/apikey). An API key is **only required for live AI generation**. The reference test suite, schema preview, database execution, and all 30 automated tests work completely without an API key!

---

## 💻 Running the Application

Launch the Streamlit web app:
```bash
streamlit run app.py
```

The browser will open automatically at `http://localhost:8501`.

### App Features:
1. **💬 Query Tab:**
   - Type custom questions or choose from preloaded examples.
   - Select prompt versions (`v1`, `v2`, `v3`).
   - Click **Generate SQL** to trigger the 7-step automated pipeline.
   - Inspect AI token consumption, AST validation logs, results table, and the unique Run ID.
2. **🧪 Reference Tests Tab:**
   - Run the 5 benchmark reference test cases with one click.
   - Compare expected outcomes vs actual database responses without needing an API key.
3. **📜 Query History Tab:**
   - Audit trail of previous runs stored in SQLite, showing timestamp, question, generated SQL, status, and returned rows.
4. **⚖️ Prompt Comparison Tab:**
   - Side-by-side comparison of `v1_basic`, `v2_structured`, and `v3_refined` outputs for any question.

---

## 🧪 Running Automated Tests

Run the complete pytest test suite (28 tests across all modules):

```bash
pytest tests/ -v
```

All 28 tests run in under 1 second:
- ✅ Safe query execution
- ✅ Prohibited keywords (`DROP`, `DELETE`, `INSERT`, `ALTER`, etc.)
- ✅ Semicolon injection / multi-statement rejection
- ✅ Unknown / hallucinated table prevention
- ✅ Empty / malformed question input handling
- ✅ Sanitized API error handling (never exposing secrets)
- ✅ Semantic correctness vs execution success distinction
- ✅ SQLite persistence and retrieval

---

## 🔒 SQL Safety & Defense-in-Depth

AI-generated queries are untrusted input. QueryCraft protects the database through 4 layers of defense:

1. **Keyword Boundary Blocking:** Rejects `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `PRAGMA`, `ATTACH`, `DETACH`.
2. **AST Structural Parsing (`sqlglot`):**
   - Verifies the query consists of exactly **one** statement.
   - Ensures the root statement is an instance of `exp.Select`.
   - Inspects table references against the whitelist: `{"employees", "departments"}`.
   - Rejects subqueries containing write expressions.
3. **Engine-Level Enforcements:**
   - Enables `PRAGMA query_only = ON` on the SQLite connection.
   - Uses URI read-only connections (`mode=ro`).
4. **Execution Boundaries:**
   - Result row truncation (default: `100` rows maximum).
   - Strict query execution timeout (`5.0` seconds).

---

## 🧠 Prompt Engineering Comparison

| Feature | `v1_basic` | `v2_structured` | `v3_refined` |
|:---|:---:|:---:|:---:|
| **Schema Included** | ❌ (Guesses tables) | ✅ Full schema provided | ✅ Full schema + data types |
| **SQL Dialect Specified** | ❌ Generic SQL | ✅ SQLite explicit | ✅ SQLite explicit |
| **Output Constraints** | ❌ Freeform text | ✅ Markdown code block | ✅ Strict code block + explanation |
| **Write Prevention** | ❌ None | ⚠️ "SELECT only" rule | 🛡️ Strict zero-modification rules |
| **Ambiguity Handling** | ❌ Unhandled | ❌ Unhandled | ✅ Conservative literal interpretation |
| **Schema Grounding / Fallback** | ❌ Hallucinates columns | ❌ May guess columns | 🛡️ Outputs `CANNOT_ANSWER: <reason>` |

---

## 📋 Demonstration Script (3–5 Minutes)

1. **Introduction (0:00 - 0:30):**
   - Launch `streamlit run app.py`.
   - Show the left sidebar: database schema inspector (`departments` and `employees` tables) and active configuration.
2. **Safe Query Generation (0:30 - 1:15):**
   - In the **Query** tab, select question *"Show the five highest paid employees"*.
   - Select prompt `v3_refined`. Click **🚀 Generate SQL**.
   - Show the generated SQLite query, AST validation confirmation, rendered data table, and unique **Run ID** (e.g. `RUN-A4F19B8C`).
3. **Safety & Refusal Verification (1:15 - 2:00):**
   - Select the edge case: *"Show employee phone numbers"*.
   - Click **Generate SQL**.
   - Show how `v3_refined` correctly refuses hallucinating nonexistent columns with `CANNOT_ANSWER`, flagging validation errors and preventing database execution.
4. **Semantic Verification vs Execution (2:00 - 2:45):**
   - Navigate to the **Reference Tests** tab.
   - Click **▶️ Run All Reference Tests**.
   - Show all 5 reference test cases passing (TC001 to TC005).
   - Explain why semantic correctness differs from syntactic execution (e.g. returning 3 rows instead of 5 executes cleanly in SQLite but fails semantic verification).
5. **Audit Trail & Prompt Comparison (2:45 - 3:30):**
   - Navigate to **History** tab: highlight that every run is saved into SQLite with timestamps, status, and full result JSON.
   - Navigate to **Prompt Comparison** tab: show the side-by-side comparison table explaining why `v3_refined` prevents hallucinations compared to `v1_basic`.
6. **Automated Testing (3:30 - 4:00):**
   - Switch to terminal and run `pytest tests/ -v`.
   - Point out 28 passing unit tests covering safety, parser, and pipeline components.

---

## 📄 License
Educational project developed for AI-Assisted Coding coursework.
Student: Tanay Siddharth Shelar (150096725092).

