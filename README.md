<div align="center">
  <img src="frontend/public/assets/loomflow_icon.svg" width="80" alt="Loomflow Logo">
  
  # ⛵ Loomflow (Beta: Local AI Branch)
  
  **A self-hosted, visual ETL and workflow synthesizer built on Polars, React Flow, and Local LLMs.**

  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)
  [![Made with Polars](https://img.shields.io/badge/Engine-Polars-blue)](https://pola.rs/)
</div>

> [!WARNING]
> **🚧 ACTIVE DEVELOPMENT (`beta` branch)**
> You are currently viewing the `beta` branch. This branch is dedicated to our transition to a **100% local, private, and self-hostable AI architecture**. 
> 
> We are decoupling all agentic synthesis features from proprietary cloud APIs. Our primary objective here is building native support for **local open-weights models** (via Ollama, LM Studio, llama.cpp) using standardized OpenAI-compatible local endpoints. Your data and schemas should never leave your machine.

---

## 🎯 The Vision: Autonomous, Local-First Data Engineering

Loomflow brings the drag-and-drop visual pipeline building of massive enterprise tools directly to your local machine, powered by the sub-millisecond execution of **Polars**. 

On this branch, we are building the **Autonomous Workflow Synthesizer**. Instead of manually dragging nodes, you give a local LLM a natural language objective. The agent uses an **In-Memory Sandbox** to profile data slices, test transformations, catch its own exceptions, and then automatically compile the verified execution trace into a React Flow DAG on your canvas.

### Why Local?
If you are dealing with company logs, CRM support tickets, or lab data, sending your schema and data to cloud LLMs is a non-starter. Loomflow's synthesizer is being built to run entirely on local consumer hardware (Llama 3, Qwen, Gemma) so you retain complete data sovereignty.

---

## 🛠️ Beta Roadmap & How to Contribute

We are actively looking for contributors to help us build out the multi-domain sandbox and local model orchestration. Pick a task below and open a PR!

### 1. Provider-Agnostic LLM Orchestrator (`backend/agent/`)
- [ ] Implement the ReAct loop supporting local OpenAI-compatible endpoints (`http://localhost:1234/v1`).
- [ ] Map Python Pydantic tool definitions to standard JSON schema for local model function calling.
- [ ] Build the self-healing error loop (catching Polars exceptions and feeding the stack trace back to the LLM).

### 2. The Sandbox Engine (`backend/agent/sandbox/`)
- [ ] `SandboxSession`: In-memory `pl.LazyFrame` micro-cache (max 200 rows) for zero-latency agent iterations.
- [ ] `inspect_source_metadata()`: Tool for the LLM to read columns, dtypes, and null ratios.
- [ ] `test_polars_transformation()`: Safe execution environment for the LLM to test its generated nodes before committing them to the canvas.

### 3. Multi-Domain Canvas Nodes
We are expanding Loomflow beyond basic ETL. Help us build the execution logic for:
- **Business & CRM:** `SLATimerNode`, `RuleRouterNode` (multi-port branching), `LocalTextClassificationNode`.
- **STEM & Math:** `SymbolicFormulaNode` (integrating `sympy` for calculus and equation solving with KaTeX rendering).
- **Predictive ML:** `WindowFeaturesNode`, `MLPredictorNode` (XGBoost/Poisson).

*(Developers do **NOT** need to write React to build nodes! Build a Python class in `backend/app/tools/`, define a `MANIFEST` dictionary, and the platform auto-generates the UI).*

---

## 🚀 Quick Start (Development)

Run both the backend and frontend simultaneously with our automated scripts:

**Windows (PowerShell)**
```powershell
.\run.ps1

macOS / Linux (Bash)

Bash
chmod +x run.sh
./run.sh
For manual startup, run uvicorn in the /backend and npm run dev in the /frontend.

🧩 Architecture
Code snippet
graph TD
    A[React Canvas UI] -->|Prompt + Data Source| B[Local LLM / LM Studio]
    B -->|Tool Call| C[Agent Sandbox Engine]
    C -->|Test on 100-row slice| D[Polars In-Memory Eval]
    D -->|Error Trace| B
    D -->|Verified Trace| E[DAG Layout Compiler]
    E -->|JSON Nodes & Edges| A
