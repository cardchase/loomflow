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

> [!IMPORTANT]
> **🚀 ENTERPRISE READY (v1.5):** Loomflow has reached its enterprise readiness milestone! Featuring global secure cloud authentication (OAuth 2.0 / Service Accounts) with **Native Windows Certificate Store integration** for bypassing corporate MITM proxies (like Zscaler), auto-healing crash recovery, unrestricted Nvidia GPU background processing, and massive database integrations (PostgreSQL, MySQL, SQLite). The latest v1.5 release introduces O(1) Polars vectorization for advanced analytics, machine learning pipelines, and predictive sports nodes!

<div align="center">
  <img src="docs/screenshot_workflow.png?v=1.5.0" width="100%" alt="Loomflow Interactive Canvas Showcase">
  <br>
  <i>Build lightning-fast Polars data pipelines visually via an interactive React Flow DAG canvas.</i>
</div>

<br>

<div align="center">
  <img src="docs/screenshot_ui.png" width="100%" alt="Loomflow Tabular UI Configuration">
  <br>
  <i>Configure tools effortlessly using enterprise-grade, compact spreadsheet-like UI panels.</i>
</div>

---

> [!NOTE]
> **🤖 An AI + Human Community Collaboration**
>
> Loomflow is a modern, visual data engineering platform co-created in partnership between **Advanced AI Coding Agents** and the **Human Developer Community**! Built completely from scratch, this project represents the future of agentic development. 

Welcome to the **Loomflow** open-source community! 🌍 Our mission is to build a vibrant, exciting, and beautiful platform where data engineers and analysts can effortlessly create, share, and manage a vast ecosystem of custom data processing tools. Let your imagination go wild! 🚀

Loomflow brings the drag-and-drop visual pipeline building of massive enterprise tools directly to your local machine. Visually construct your data workflows, connect nodes with wires, and execute pipelines in-memory utilizing the lightning-fast Rust-based **Polars** engine. Whether you're dealing with a tiny CSV or millions of rows from a massive SQL warehouse, Loomflow handles it with absolute elegance.

---

## 🎯 Core Philosophy

Loomflow bridges the gap between complex code-based data preparation and heavy enterprise ETL licensing.

- **Interactive Canvas**: Drag-and-drop tools to build Directed Acyclic Graphs (DAGs) of your data pipeline.
- **In-Memory Executions**: Process data locally using **Polars** yielding sub-millisecond execution times.
- 🐘 **Big Data Ready**: Connect directly to massive SQL Databases (PostgreSQL, MySQL, SQLite, etc.) via highly-parallelized `connectorx` Arrow drivers.
- 🧠 **Smart DAG Pruning & Persistent Disk Caching**: Fully integrated node-caching capabilities. Click the Cache button to **Freeze** a node's output directly to highly compressed Parquet files on your hard drive. This survives server restarts and instantly bypasses expensive upstream computations (like ML predictions) in milliseconds!
- 🏗️ **Union & Deduplication**: Stack datasets seamlessly or isolate distinct entries.
- 📊 **Interactive Web Visuals**: Dynamically generate rich, interactive Scatter, Line, Bar, and Box plots using the integrated `Plotly` HTML backend. Hover, zoom, and pan directly inside your results grid!
- ✨ **Multimodal Generative AI**: Seamlessly process Text, Images, Video, and Audio using the integrated **Gemini AI** node! Throw files and prompts at the node and watch it dynamically extract data into a new column.
- 🐍 **Advanced Python Scripting**: A built-in Python tool featuring a beautifully integrated **native syntax-aware IDE**, complete with column-aware autocompletion (just type `df["`). Contains pre-built templates for hitting external APIs or running custom LLMs directly inside your pipeline!
- 🤖 **Agent-Ready Architecture**: Export your complex mathematical workflows into an ultra-clean, machine-readable YAML file in one click. Send this single file to any AI Agent or LLM to automate, improve, or instantly orchestrate your intelligence platform from scratch!
- 💾 **Workflow Save/Load**: Never lose your progress. Export your complete ETL pipeline architecture to JSON and restore it at any time directly from the visual canvas.
- 🤝 **Share & Collaborate**: Because workflows are saved as ultra-lightweight JSON files, you can instantly share them over Slack, Discord, or GitHub! The community can load your exact pipeline to help you debug errors, build custom visualizations, or extend your data models.
- 🛡️ **Zero Data-Loss Auto-Recover**: Loomflow features an enterprise-grade, two-tier autosave system. Workflows are instantly cached to your browser locally, while a debounced network process physically streams rolling `.autosave` increments to your backend server to protect you against catastrophic cache-wipes!
- 🗂️ **Multi-Tabbed Workspaces**: Work on multiple isolated DAGs simultaneously, just like a modern IDE! Open, swap, and execute multiple independent pipelines via a seamless tab bar without ever overwriting your progress.
- 📂 **Flexible I/O**: Ingest CSVs, Excel files, Text files, Word Documents, Database files (SQLite, Microsoft Access), parse tables directly out of PDFs, or write out fully interactive HTML visualizations.
- ☁️ **Global Cloud Integrations**: Loomflow features a unified authentication system for cloud providers. Upload a Google Cloud `Service Account JSON` or `OAuth 2.0 Client Secret` exactly once in the global toolbar to instantly and securely authenticate all downstream cloud nodes simultaneously!
- 📁 **Massive Batch Processing**: Use `Folder Input` to recursively scan directories and `Dynamic Input` to merge hundreds of heterogeneous CSV/Excel files diagonally, bypassing the need for identical schemas.
- 🛑 **Interactive Workflow Cancellation**: Stop run-away pipelines or infinitely looping nodes instantly! Hit the global Stop button, or hover over any running node's spinner to surgically abort its execution mid-loop without losing upstream data.
- **Self-Hosted & Privacy-First**: Run both the web UI and the execution engine entirely on your local machine. No external APIs required (unless explicitly using the Gemini node).

## 🎨 Enterprise UI & Semantic Intelligence

Loomflow brings the dense, hyper-productive feel of professional enterprise suites into the open-source era:

- 📊 **Alteryx-Inspired Configuration Panels**: We've replaced bulky forms with compact, spreadsheet-like tabular grids. Manage hundreds of columns in a single dense view using intuitive checkboxes, dropdowns, and text fields—all while maintaining a gorgeous glassmorphic aesthetic.
- 📦 **Tool Containers**: Seamlessly group workflows into bounded, resizable visual containers. Disable entire containers with a single click to instantly bypass massive chunks of logic during execution!
- ⚡ **Multi-Rule Sorting & Summarization**: Build incredibly complex group-by chains and sequential sorting rules seamlessly. Our native Polars backend engine rips through multi-column aggregations instantly!
- 🧠 **Semantic Type Profiling**: Loomflow's execution engine automatically profiles incoming data to detect logical semantic types (like `currency_usd`, `percentage`, `email`).
- 💎 **Semantic Propagation**: When a semantic type is detected, the Engine maps it directly through the computational DAG! This metadata drives intelligent UI rendering—displaying `$` badges in your preview grid, formatting Plotly axes dynamically into currency layouts, and guiding users seamlessly.
- ⭐ **Dynamic Tool Favorites**: Fully customize your workspace! Pin any tool to your exclusive "Favorites" group by clicking its Star badge, completely eliminating scrolling and searching when building workflows. Your preferences are instantly saved to your browser's local storage and flawlessly restored across sessions!
- 🔢 **True Sequential Numbering & Find**: Navigating massive workflows is incredibly easy with true, clean sequential Node IDs (`node_1`, `node_2`) that make hitting the "Find" bar extremely powerful and accurate.
- ✨ **Intelligent Canvas Branching**: Build complex, multi-path workflows effortlessly. The canvas dynamically preserves all existing edge connections when dropping new tools, allowing you to seamlessly branch a single output into multiple downstream tools simultaneously.
- 🧲 **Smart Canvas Mechanics**: Magnetic wire snapping, node-collision detection, cascading auto-drops, and a dedicated "Clear All Cache" tool keep the canvas incredibly responsive and visually flawless!

---

## 🛠️ Architecture at a Glance

Loomflow is decoupled into a hyper-fast frontend and a robust backend engine.

```mermaid
graph TD
    A[React Canvas UI / @xyflow/react] -->|JSON DAG Payload| B[FastAPI Engine / uvicorn]
    B -->|Topological Sort| C[Execution Planner]
    C -->|Executes In-Memory| E[Polars DataFrames]
    E -->|JSON Data Preview| A
```

---

## 🤖 AI Workflow Synthesizer & Local LLM Integration

Loomflow features a highly advanced, fully integrated **Autonomous AI Pipeline Synthesizer**. You can now simply chat with the AI right inside your workspace, and it will magically build, rewire, and configure complex data pipelines on your canvas in real-time!

### Using Local Models (LM Studio & Qwen)
We strongly support privacy-first, fully local setups! Currently, our recommended configuration utilizes **LM Studio** running uncensored or advanced instruction-tuned models. 
* **Tested & Recommended Model:** `empero-ai/Qwen3.8-2B-Distill-GGUF` (specifically the `Qwen3.8-2B-Q5_K_M.gguf` quantization). 
  > *Note: Our orchestration logic is highly optimized so that even very small ~2B parameter models can succeed. Larger models will naturally perform even better!*
* **Setup:**
  1. Boot up LM Studio.
  2. Download your preferred `Qwen` GGUF model.
  3. Start the Local Inference Server (OpenAI-compatible) on `http://localhost:1234/v1`.
  4. In Loomflow's UI, select `Local (OpenAI Compatible)` as the provider, and the backend orchestrator will instantly bridge the gap.

### Engine-Side Hallucination Reduction
Since local models (even powerful ones like Qwen) can occasionally drift off-schema, Loomflow's `orchestrator.py` engine features bulletproof, state-of-the-art **hallucination reduction** mechanics:
- **Argument Order Healing:** Automatically intercepts and fixes swapped Regex parameters (e.g., `Regex_Extract("pattern", [Column])` is silently corrected to the required Polars syntax `Regex_Extract([Column], "pattern")`).
- **Target Column Binding:** Intelligently maps AI-generated alias variables to the strict React UI bindings (`newColumn`, `outputColumn`, `isNew`), dynamically rendering the UI accurately whether it targets an existing dataset column or writes to a brand new one!
- **Single-Input Invariants:** Protects the workflow DAG from illegal multi-edge connections (like plugging two separate streams into a `Formula` tool).
- **Graceful Error Recovery:** When execution fails, the orchestrator automatically bounces the Python traceback error to the LLM to recursively reflect and repair the node logic autonomously.

---

## 📦 Extensive Built-in Tool Palette

Loomflow comes pre-loaded with an extensive suite of data engineering nodes, elegantly categorized into pipelines.

| Category | Color | Included Tools |
| :--- | :--- | :--- |
| **In / Out** | Green 🟢 | `Folder Input`, `Dynamic Input`, `File Input`, `Database Input`, `Browse`, `File Output`, `Database Output`, `Image Ingest` |
| **Cloud** | Cyan 🩵 | `Google Sheets In`, `Google Sheets Out`, `GCS Input`, `GCS Output` |
| **Preparation** | Blue 🔵 | `Filter`, `Sort`, `Cleanse`, `Formula Compute`, `Unique`, `Regex`, `Record ID`, `Sample Records`, `Field Info` |
| **Transform** | Orange 🟠 | `Select`, `Pivot`, `Unpivot`, `Summarize`, `Date Time` |
| **Join** | Purple 🟣 | `Union`, `Join` |
| **Analysis** | Pink 🦩 | `Gemini AI (Multimodal LLM)`, `Visualization`, `Python Code`, `LLM Chunker`, `Football Engine`, `ML Predictor` |

> 🚀 **More Tools on the Horizon!**
> We are continuously expanding the Loomflow ecosystem! We have recently launched the **Cloud Connectors** suite, meaning `Google Sheets` and `Google Cloud Storage (GCS)` nodes are now partially ready for community use and testing! Expect more advanced integrations like Machine Learning predictors and geospatial transformers very soon.
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
