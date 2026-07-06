# 🧠 AI BI Assistant
### Enterprise AI Business Intelligence Platform

<div align="center">

![Python](https://img.shields.io/badge/Python-3.14-blue?style=flat-square&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.58-red?style=flat-square&logo=streamlit)
![Groq](https://img.shields.io/badge/LLM-Groq%20LLaMA%203.3%2070B-orange?style=flat-square)
![scikit-learn](https://img.shields.io/badge/ML-scikit--learn-yellow?style=flat-square&logo=scikitlearn)
![Pydantic](https://img.shields.io/badge/Contracts-Pydantic%20v2-green?style=flat-square)
![Tests](https://img.shields.io/badge/Tests-39%20passing-brightgreen?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square)

**🚀 Live Demo:** https://ai-bi-assistant-ujl3vewuaeixr8jongabql.streamlit.app/

*Ask business questions in plain English. Get charts, insights, and forecasts — no SQL, no code.*

</div>

---

## 📌 Overview

AI BI Assistant is an **Enterprise AI Business Intelligence Platform** built for internal company use. It allows non-technical employees to query business datasets using natural language and receive structured analysis, visualizations, and ML-powered forecasts.

This is **not a chatbot wrapper**. It is a structured AI Planning system with a strict separation between AI reasoning and deterministic data execution — a design principle used in production AI systems at scale.

---

## 🎯 Business Problem

Business analysts and non-technical employees need answers from data — but they cannot write SQL or Python. Traditional BI tools require training. LLM-based tools that generate and execute code are unsafe and unpredictable.

**The gap:** There is no safe, explainable, conversational interface for business data that non-technical users can trust.

---

## 💡 Solution

AI BI Assistant introduces a two-phase architecture:

**Phase 1 — AI Planning**
The LLM receives only the dataset schema and the user's question. It returns a structured JSON Execution Plan — never code, never direct answers.

**Phase 2 — Deterministic Execution**
A Python engine executes the plan step by step using Pandas. The AI never touches raw data. Only after execution does the AI receive the result to generate a business explanation.

> *"The AI plans. The engine executes. Never the other way around."*

---

## ✨ Key Features

- **Natural Language Queries** — Ask any business question in plain English
- **AI Execution Planning** — LLM generates structured multi-step plans, not code
- **Conversation Memory** — Follow-up questions understood in context
- **Business Knowledge Layer** — Auto-discovers KPIs, dimensions, and measures
- **Dataset Registry** — Persistent datasets; employees select, not upload
- **ML Forecasting** — Linear Regression forecasts next 3 months from time series
- **Multi-step Analysis** — Filter, group, aggregate, sort, limit — all chained
- **7 Chart Types** — Bar, line, pie, scatter, histogram, box, table
- **Explainable Results** — AI generates business-language explanations
- **39 Unit Tests** — Three test suites covering core modules
- **Production Deployed** — Live on Streamlit Cloud

---

## 🏗️ AI Architecture

```
User Question
     │
     ▼
PromptBuilder ──────────────── BusinessKnowledgeLayer
     │                              (semantic schema)
     │◄── ConversationContext ──── (follow-up memory)
     │
     ▼
AIClient (Groq LLaMA 3.3 70B)
     │
     ▼
ExecutionPlan (JSON) ◄── CommandValidator (schema check)
     │
     ▼
AnalysisEngine (Pandas) ── ExecutionContext
     │
     ├── ChartEngine (Plotly)
     ├── ForecastEngine (scikit-learn)
     └── ExplanationEngine (Groq)
     │
     ▼
Streamlit UI ← SessionManager (chat history)
```

### Why This Architecture?

| Design Decision | Reason |
|---|---|
| AI returns JSON plan, not code | Safe, auditable, testable |
| CommandValidator between AI and engine | Prevents hallucinated column names from reaching data |
| Dispatch pattern in AnalysisEngine | Adding operations requires one new method, no existing changes |
| Pydantic for all data contracts | Validation at every boundary, not just at the UI |
| BusinessKnowledgeLayer | AI reasons about business semantics, not raw column names |
| ConversationContext capped at 5 turns | Prevents token overflow while enabling follow-up questions |

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| UI | Streamlit 1.58 |
| AI Planning | Groq API — LLaMA 3.3 70B Versatile |
| Data Processing | Pandas 3.0 |
| ML Forecasting | scikit-learn (Linear Regression) |
| Visualisation | Plotly 6.8 |
| Data Contracts | Pydantic v2 |
| Testing | pytest |
| Language | Python 3.14 |

---

## 📁 Project Structure

```
AI BI Assistant/
│
├── app.py                        # Streamlit chat interface
│
├── core/
│   ├── ai_client.py              # Groq API wrapper (provider-agnostic)
│   ├── prompt_builder.py         # Builds AI planning prompt with context
│   ├── command_validator.py      # Validates AI plan against real dataset
│   ├── analysis_engine.py        # Executes ExecutionPlan via Pandas
│   ├── chart_engine.py           # Renders Plotly charts from results
│   ├── explanation_engine.py     # Generates business explanation via AI
│   ├── forecast_engine.py        # Linear Regression forecasting (ML)
│   ├── business_knowledge.py     # Auto-builds semantic schema from data
│   ├── conversation_context.py   # Manages multi-turn conversation memory
│   ├── dataset_registry.py       # Persistent dataset management
│   ├── data_loader.py            # CSV ingestion with encoding detection
│   ├── data_cleaner.py           # Missing values, duplicates, dates
│   ├── data_profiler.py          # Schema and statistics extraction
│   └── session_manager.py        # UI chat history management
│
├── models/
│   ├── analysis_step.py          # Pydantic: single execution step
│   ├── execution_plan.py         # Pydantic: complete AI plan
│   ├── dataset_profile.py        # Pydantic: dataset schema
│   ├── analysis_result.py        # Pydantic: execution output
│   └── business_schema.py        # Pydantic: semantic business model
│
├── utils/
│   ├── constants.py              # Supported operations, charts, aggregations
│   ├── exceptions.py             # Structured exception hierarchy
│   └── logger.py                 # Centralized logging configuration
│
├── tests/
│   ├── test_data_loader.py       # 20 tests for data ingestion
│   ├── test_business_knowledge.py # 9 tests for semantic schema builder
│   └── test_conversation_context.py # 10 tests for conversation memory
│
└── data/
    └── samplesuperstore.csv      # Sample business dataset
```

---

## ⚙️ Installation

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

**4. Configure API key**

Create `.env` in the project root:
```
GROQ_API_KEY=your_groq_api_key_here
```

Get a free key at https://console.groq.com

**5. Run**
```bash
streamlit run app.py
```

---

## 🔧 Configuration

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | Yes | Groq API key for LLaMA 3.3 70B |

For Streamlit Cloud deployment, add secrets under **App Settings → Secrets**:
```toml
GROQ_API_KEY = "your_key_here"
```

---

## 📖 Usage

1. Launch the app and select a dataset from the sidebar
2. Ask any business question in plain English:

```
What are the top 5 products by total sales?
Which region has the highest profit margin?
Show me monthly sales trend for 2023
Which one performed worst?  ← follow-up question
Now compare with 2022      ← conversational follow-up
```

3. View the chart, expand the data table, read the AI explanation
4. For time series results, click **📈 Show 3-Month Forecast** for ML predictions

---

## 🔄 Example Workflow

**Question:** *"What are the top 10 customers by sales in the West region?"*

**AI generates this ExecutionPlan:**
```json
{
  "steps": [
    {"operation": "filter", "column": "Region", "operator": "=", "value": "West"},
    {"operation": "group_by", "column": "Customer Name"},
    {"operation": "aggregate", "metric": "Sales", "aggregation": "sum"},
    {"operation": "sort", "column": "Sales", "order": "descending"},
    {"operation": "limit", "n": 10}
  ],
  "visualization": {
    "chart_type": "bar",
    "x_axis": "Customer Name",
    "y_axis": "Sales",
    "title": "Top 10 Customers by Sales in West Region"
  }
}
```

**Engine executes. AI explains:**
> *"Raymond Buch leads the West region with $14,345 in total sales, significantly ahead of the next customer. The top 10 collectively account for over $73,000 in regional revenue."*

---

## 🗺️ Future Roadmap

- [ ] Multi-dataset cross-analysis
- [ ] Anomaly detection (Isolation Forest)
- [ ] Customer segmentation (K-Means clustering)
- [ ] PDF executive report export
- [ ] Authentication and multi-user support
- [ ] Database persistence for session history
- [ ] RAG over uploaded documents
- [ ] Multi-agent AI workflows
- [ ] REST API layer for programmatic access
- [ ] Docker containerisation

---

## 🧪 Testing

```bash
pytest tests/ -v
```

```
39 passed in 3.23s
```

Test coverage includes:
- Data ingestion (20 tests) — encoding, size limits, binary detection
- Business Knowledge Layer (9 tests) — KPI detection, dimension classification
- Conversation Context (10 tests) — filter accumulation, rolling window, clear

---

## 🤔 Challenges Solved

**Challenge 1 — LLM hallucinating column names**
Solution: `CommandValidator` validates every column reference in the plan against the actual dataset schema before execution.

**Challenge 2 — Pandas `df.attrs` lost after operations**
Solution: Replaced `df.attrs` with explicit `ExecutionContext` dataclass passed through every dispatch call.

**Challenge 3 — Follow-up questions losing context**
Solution: `ConversationContext` accumulates filters and tracks active grouping/metric, injected into every prompt.

**Challenge 4 — Windows PowerShell encoding issues**
Solution: Explicit UTF-8 encoding in all file writes, BOM detection in `data_loader.py`.

---

## 📚 Lessons Learned

- LLMs should plan, not execute — separating reasoning from execution is the key architectural insight
- Pydantic validation at every module boundary catches more bugs than any amount of defensive coding
- Context management for conversational AI is harder than the AI itself
- Streamlit's rerun model requires careful session state design for stateful features

---

## 👤 Author

**Anushath**
AI/ML Internship — Sri Lakshmi Technology
GitHub: [@Anushath15](https://github.com/Anushath15)

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.