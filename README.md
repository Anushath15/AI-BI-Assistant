# AI BI Assistant
### AI-Powered Business Intelligence Platform

An internship project demonstrating production-quality AI Engineering —
not a chatbot, not a dashboard, but a structured AI Planning system
that lets non-technical business users query any CSV dataset using
plain English.

---

## What Makes This Different

Most "AI + data" projects send raw data to an LLM and print the response.

This project does not.

**The AI is never allowed to touch the data.**

Instead, the system follows a strict two-phase architecture:

**Phase 1 — AI Planning**
The LLM receives the dataset schema and the user's question.
It returns a structured JSON Execution Plan — a sequence of
operations like filter, group_by, aggregate, sort, limit.
It never sees the actual data rows.

**Phase 2 — Deterministic Execution**
A Python execution engine reads the plan and executes each step
against the DataFrame using Pandas.
Only after execution does the AI receive the result —
to generate a business-language explanation.

This separation means the system is safe, auditable, and testable.
The AI plans. The engine executes. Never the other way around.

---

## Architecture
User Question
│
▼
PromptBuilder        ← builds structured prompt from dataset schema
│
▼
AIClient (Groq)      ← LLM returns JSON ExecutionPlan only
│
▼
CommandValidator     ← validates column names, operations, types
│
▼
AnalysisEngine       ← executes plan step by step using Pandas
│
▼
ChartEngine          ← renders Plotly chart from result
│
▼
ExplanationEngine    ← LLM generates business explanation from result
│
▼
Streamlit UI         ← chat interface with history

---

## Example

**User asks:**
> What are the top 5 products by total sales?

**AI returns (ExecutionPlan):**
```json
{
  "steps": [
    {"operation": "group_by", "column": "Product Name"},
    {"operation": "aggregate", "metric": "Sales", "aggregation": "sum"},
    {"operation": "sort", "column": "Sales", "order": "descending"},
    {"operation": "limit", "n": 5}
  ],
  "visualization": {
    "chart_type": "bar",
    "x_axis": "Product Name",
    "y_axis": "Sales",
    "title": "Top 5 Products by Total Sales"
  }
}
```

**Engine executes. AI explains:**
> The top-selling product is the Canon imageCLASS 2200 Advanced Copier,
> generating $61,599 in total sales — significantly ahead of the next
> four products combined.

The user wrote no SQL. No Python. No code.

---

## Project Structure
AI BI Assistant/
│
├── app.py                   # Streamlit chat interface
│
├── core/
│   ├── ai_client.py         # Groq/LLM API wrapper
│   ├── prompt_builder.py    # Builds structured AI planning prompt
│   ├── command_validator.py # Validates AI response against dataset
│   ├── analysis_engine.py   # Executes ExecutionPlan via Pandas
│   ├── chart_engine.py      # Renders Plotly charts from results
│   ├── explanation_engine.py# Generates business explanation via AI
│   ├── data_loader.py       # CSV ingestion with encoding detection
│   ├── data_cleaner.py      # Missing values, duplicates, date parsing
│   ├── data_profiler.py     # Schema and statistics extraction
│   └── session_manager.py   # Conversation memory (in progress)
│
├── models/
│   ├── analysis_step.py     # Pydantic model for a single plan step
│   ├── execution_plan.py    # Pydantic model for the full AI plan
│   ├── dataset_profile.py   # Pydantic model for dataset schema
│   └── analysis_result.py   # Pydantic model for execution output
│
├── utils/
│   └── constants.py         # Supported operations, aggregations, charts
│
├── tests/
│   └── test_data_loader.py  # Unit tests for data loader
│
└── data/
└── samplesuperstore.csv # Sample dataset for testing

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| AI Planning | Groq API — LLaMA 3.3 70B |
| Data Processing | Pandas |
| Visualisation | Plotly |
| Data Contracts | Pydantic v2 |
| Language | Python 3.11+ |

---

## Supported Operations

The AI Planner can generate plans using these operations:

`filter` `group_by` `aggregate` `sort` `limit` `top_n` `bottom_n`
`distribution` `correlation` `kpi` `time_series` `compare`

Supported aggregations: `sum` `mean` `count` `min` `max` `median` `std`

Supported charts: `bar` `line` `pie` `scatter` `histogram` `box` `table`

---

## How to Run

**1. Clone the repository**
```bash
git clone https://github.com/Anushath15/AI-BI-Assistant.git
cd AI-BI-Assistant
```

**2. Create and activate virtual environment**
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Add your API key**

Create a `.env` file in the project root:
GROQ_API_KEY=your_groq_api_key_here

Get a free key at https://console.groq.com

**5. Run the app**
```bash
streamlit run app.py
```

**6. Upload any CSV and start asking questions**

---

## Design Principles

- **Single Responsibility** — every module does exactly one thing
- **Separation of Concerns** — AI planning is completely decoupled from data execution
- **Pydantic contracts** — all data flowing between modules is typed and validated
- **Dispatch pattern** — AnalysisEngine and ChartEngine use method dispatch, not if-elif chains
- **Provider agnostic** — switching from Groq to any other LLM requires changing one file

---

## Developed By

Anushath
AI/ML Internship Project — Sri Lakshmi Technology