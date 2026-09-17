# NutriPure AI 🌿
### Know What’s Really Inside Your Food
**Autonomous Food Truth, Chemical Deconstructor & Deceptive Marketing Auditor**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.2.11-orange.svg)](https://github.com/langchain-ai/langgraph)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-green.svg)](https://www.trychroma.com/)
[![MCP](https://img.shields.io/badge/Protocol-Model_Context_Protocol_(MCP)-purple.svg)](https://modelcontextprotocol.io/)
[![HITL](https://img.shields.io/badge/Human--in--the--Loop-SqliteSaver-red.svg)](https://langchain-ai.github.io/langgraph/)

An enterprise-grade autonomous AI system designed to audit packaged food labels, expose deceptive front-of-pack marketing claims, decode cryptic INS/E-number additives, and enforce personalized medical constraints (Diabetes, Allergies, Pediatric safety) using **LangGraph**, **ChromaDB Regulatory RAG**, and Anthropic's **Model Context Protocol (MCP)**.

---

## 🎯 The Problem Solved
Packaged food brands regularly deceive consumers by printing bold claims on the front of packages—such as **"100% Atta / Whole Wheat"**, **"No Added Sugar"**, or **"100% Natural"**—while concealing refined flour (Maida), high-glycemic disguised starches (Maltodextrin, Invert Sugar), and toxic preservatives (Sodium Benzoate, Caramel Color IV) on the back.

Generic LLMs fail at auditing food products because they hallucinate regulatory standards, miss disguised chemical synonyms, and cannot safely account for individual medical conditions.

**NutriPure AI solves this through a 5-tier grounded architecture:**
1. **Perception & QUID Extraction:** Extracts ingredient percentages (e.g., *Maida 62%, Atta 24%*) using a nested-bracket tokenizer and Pydantic v2 schemas.
2. **Regulatory Grounding (RAG):** Ingests the **32-page official Government of India FSSAI Gazette Notification PDF** and WHO standards across **670 chunks** in ChromaDB.
3. **Tool Protocol (MCP):** Connects to external chemical registries (PubChem / OpenFoodFacts) and live government recall feeds via standardized **Model Context Protocol (MCP)** tools.
4. **Agentic Brain (LangGraph):** Executes a cyclic state machine with contradiction grading, NOVA ultra-processed classification, and reflection loops.
5. **Human-in-the-Loop (HITL):** Uses `SqliteSaver` and LangGraph's `interrupt()` primitive to halt execution and adapt verdicts to individual medical profiles.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph Layer1["1. Ingestion & Perception Layer"]
        Label[Packaging Text / Label] --> Tokenizer[Nested-Bracket Tokenizer & QUID Parser]
        Tokenizer --> PydanticSchema["Pydantic v2 Schema\n(ExtractedIngredient, NutritionalFacts)"]
    end

    subgraph Layer2["2. Grounding & Knowledge Layer"]
        subgraph InternalRAG["ChromaDB Regulatory RAG (670 Chunks)"]
            FSSAI_PDF[Official 32-Page FSSAI Gazette PDF] --> Embeddings[Sentence-Transformer Embeddings]
            WHO_Docs[WHO Sugar & Additive Codices] --> Embeddings
            Embeddings --> ChromaDB[(ChromaDB Vector Store)]
        end

        subgraph ExternalMCP["Model Context Protocol (MCP) Registry"]
            MCP_Client[MCP Client] <--> Tool_Chem[Tool: query_chemical_toxicity]
            MCP_Client <--> Tool_Alert[Tool: check_fssai_product_alerts]
        end
    end

    subgraph Layer3["3. LangGraph Cyclic Orchestration Engine"]
        PydanticSchema --> Node1[Node 1: Chemical Decoder & Disguised Sugar Hunter]
        Node1 <--> ExternalMCP
        Node1 --> Node2[Node 2: Regulatory RAG Compliance Engine]
        Node2 <--> InternalRAG
        Node2 --> Node3[Node 3: Marketing Claim Contradiction Grader]
        Node3 --> Node4[Node 4: Toxicity & NOVA Group Scorer]
        Node4 --> ReflectionCheck{Self-Consistency Reflection?}
        ReflectionCheck -->|Needs More Evidence| Node2
        ReflectionCheck -->|Passed| Node5[Node 5: HITL Gate & Synthesis]
    end

    subgraph Layer4["4. Human-in-the-Loop & Presentation Layer"]
        Node5 --> InterruptGate["interrupt() Gate:\nHalts Graph Execution"]
        InterruptGate --> SQLiteCheckpointer[(SqliteSaver Checkpointer)]
        SQLiteCheckpointer <--> UserUI[Streamlit Web Dashboard]
        UserUI -->|Human Medical Input| ResumeGraph[Resume Execution]
        ResumeGraph --> FinalReport[Personalized Consumer Audit Report]
    end
```

---

## 🔬 Benchmark Dataset & Verification Results

NutriPure AI was evaluated against a benchmark test suite of real-world food formulations modeled after commercial Indian market products:

| Product Name | Front Marketing Claim | Back-of-Pack Reality | LangGraph Verdict | Legal / Health Citation |
| :--- | :--- | :--- | :---: | :--- |
| **VitaWheat Digestives** | *"100% Whole Wheat Atta"* | Maida 62%, Atta 24%, Palm Oil | **UNHEALTHY / MISLEADING** (NOVA 4) | **FSSAI Section 7** (Mandatory $\ge 60\%$ Whole Wheat threshold). |
| **ChocoMalt Power Drink** | *"No Added Sugar"* | 26% Maltodextrin (GI > 110), Sucralose | **UNHEALTHY / MISLEADING** (NOVA 4) | **FSSAI Schedule II, Section 4** (Maltodextrin bulking prohibition). |
| **RealBerry Fruit Nectar** | *"100% Natural & No Preservatives"* | 12% Fruit, Sodium Benzoate, Carmoisine | **UNHEALTHY / MISLEADING** (NOVA 4) | **FSSAI Regulation 4** & WHO Benzene formation carcinogen alert. |
| **ProMax Keto Protein Bar** | *"Clean Nutrition, Keto Friendly"* | Palm Kernel Oil, Caramel IV (INS 150d) | **UNHEALTHY / MISLEADING** (NOVA 4) | Contains **INS 150d** with trace 4-MEI carcinogen. |
| **PureGrain Rolled Oats** | *"100% Whole Oats, Single Ingredient"* | 100% Whole Grain Oats | **CLEAN** (NOVA 1) | Zero violations, zero false alarms. |

---

## ⚡ Key Engineering Innovations

### 1. Nested-Bracket Negative Lookahead Tokenizer
Standard `text.split(',')` crashes on complex labels like `Raising Agents [INS 503(ii), INS 500(ii)]`. We engineered a regex negative lookahead pattern `r',\s*(?![^(\[]*[)\]])'` that splits only at ingredient boundaries while keeping nested additive groups intact.

### 2. Dual-Format RAG with Page-Level Citations
Ingests both cleaned Markdown guidelines and an authentic **32-page official Government of India Gazette PDF** using `pypdf`. Every chunk maintains metadata enabling citations like:
> *"FSSAI Advertising and Claims Regulation 2020, Section 7, Page 14."*

### 3. Model Context Protocol (MCP) Standard
Standardized tool execution over JSON-RPC contracts for external chemical lookups (`query_chemical_toxicity`) and live government advisories (`check_fssai_product_alerts`), decoupling the agent from external APIs.

### 4. Human-in-the-Loop (HITL) with `SqliteSaver`
Uses LangGraph's `interrupt()` primitive to freeze execution before report synthesis. When a user supplies their medical profile (e.g., *Diabetic = True, Allergies = ['Gluten']*), the state machine resumes from the SQLite database to generate personalized medical warnings.

---

## 🚀 Quickstart Guide

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/yourusername/nutri_audit_agent.git
cd nutri_audit_agent

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Automated Verification Tests
```bash
# Day 2: Test Pydantic schemas & QUID extraction
python tests/test_day2.py

# Day 3: Test ChromaDB regulatory RAG & 32-page PDF ingestion
python tests/test_day3.py

# Day 4: Test Model Context Protocol (MCP) tool catalog
python tests/test_day4.py

# Day 5: Test LangGraph multi-node state machine
python tests/test_day5.py

# Day 6: Test Human-in-the-Loop (HITL) interrupt & state resumption
python tests/test_day6.py
```

### 3. Launch the Interactive Web Dashboard
```bash
streamlit run app.py
```
Open `http://localhost:8501` in your browser.

---

## 💼 Resume Bullet Points (ATS-Optimized)

> **NutriPure AI | Autonomous Packaged Food Auditor & Chemical Deconstructor**  
> *Python, LangGraph, ChromaDB, Model Context Protocol (MCP), Pydantic v2, Streamlit*
> * Architected an end-to-end multimodal agentic auditor using **LangGraph**, **ChromaDB**, and **MCP** to detect deceptive marketing claims on packaged foods with zero false-positives across benchmark datasets.
> * Built a **Regulatory RAG pipeline indexing 670 chunks** from the official **32-page Government of India FSSAI Gazette PDF** and WHO standards, producing exact legal clause citations for compliance violations.
> * Implemented **Human-in-the-Loop (HITL) checkpointing via `SqliteSaver` and `interrupt()`**, freezing state to gate verdicts against personalized medical profiles (Diabetes, Celiac, Pediatric) before resuming graph execution.
> * Developed an **MCP tool registry** for standardized external chemical toxicity discovery and live government recall notice querying over JSON-RPC schemas.

---

## 🎯 Technical Interview Q&A Preparation

#### Q1: "Why did you use LangGraph instead of standard LangChain chains?"
> *"Standard LangChain chains are strictly linear (DAGs) and stateless. Food safety auditing requires multi-step reasoning, cyclic reflection loops (re-retrieving context if evidence is weak), and state persistence. LangGraph provides first-class support for cyclical graphs, conditional edge routing, and state checkpointing via `interrupt()`."*

#### Q2: "How do you prevent hallucinations when checking food laws?"
> *"I implemented a dual-grounding mechanism: First, all legal clauses are retrieved from a ChromaDB vector index loaded with the official 32-page FSSAI Gazette Notification. Second, claim verification is separated from report synthesis into dedicated grading nodes, requiring explicit citations before a contradiction item can be formed."*

#### Q3: "Why did you use SQLite for checkpointing instead of PostgreSQL?"
> *"For this demonstration, `SqliteSaver` was chosen because it is serverless, single-file, and completely portable with zero external database dependencies. However, because LangGraph checkpointers inherit from `BaseCheckpointSaver`, the system is fully decoupled—swapping `SqliteSaver` for `PostgresSaver` in a multi-user Kubernetes environment requires only a single connection string change."*

---

## 📄 License
MIT License. Built for educational and demonstration purposes.
