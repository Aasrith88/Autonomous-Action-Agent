# Autonomous Enterprise Action Agent

A stateful, production-ready ReAct agent built with **LangGraph** and **FastAPI**. This microservice functions as an autonomous customer support worker capable of querying SQL databases and executing hard-coded mutations while strictly adhering to enterprise business guardrails.

## 🏗️ Architectural Engineering Highlights

Unlike standard read-only RAG pipelines, this agent safely executes real-world actions. It was engineered to solve three specific production challenges:

1. **Prompt Injection Prevention (Deterministic Guardrails):**
   Business logic (e.g., "Do not refund shipped orders") is not enforced via LLM system prompts, which are vulnerable to injection attacks. Instead, guardrails are hard-coded directly into the Python SQLite tools. The database physically rejects invalid LLM requests before execution.
2. **High-Availability LLM Routing (Fault Tolerance):**
   Configured with multi-model fallback routing (`gemini-3.5-flash-lite` primary $\rightarrow$ `gemini-3.5-flash` backup). If the primary API endpoint experiences a `503 Service Unavailable` spike, LangGraph automatically fails over to the backup model mid-execution without dropping the user's graph state.
3. **Stateful Session Memory (`MemorySaver`):**
   Utilizes LangGraph checkpointing to maintain multi-turn conversational context. The agent remembers specific entity IDs and transaction details across a `thread_id` without requiring redundant SQL tool calls.

## 🛠️ Tech Stack
* **Framework:** LangGraph, LangChain
* **Backend:** FastAPI, Uvicorn, Python 3.12+
* **Database:** SQLite (Parameterized queries to prevent SQL injection)
* **LLM Engine:** Google Gemini (Generative AI SDK)

## 📂 Repository Structure
* `main.py` - The FastAPI production server and endpoints.
* `langgraph_agent.py` - The cyclic ReAct state machine and MemorySaver checkpointer.
* `agent_tools.py` - Deterministic Python tools (`get_order_status`, `process_refund`) interfacing with SQLite.
* `setup_db.py` - Initialization script to generate the local enterprise database.

## 🚀 Quickstart Guide

**1. Clone the repository and install dependencies:**
```bash
git clone [https://github.com/Aasrith88/autonomous-action-agent.git](https://github.com/Aasrith88/autonomous-action-agent.git)
cd autonomous-action-agent
pip install -r requirements.txt