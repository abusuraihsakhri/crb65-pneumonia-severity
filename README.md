# CRB65 Pneumonia Severity

> **Domain:** Clinical Decision Support & Biomedical Computing  
> **Reference Guidelines & Standards:** `Standard Clinical Formulations & ISO/IEC Quality Frameworks`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

CRB-65 Outpatient & Inpatient Community-Acquired Pneumonia Severity Score
-------------------------------------------------------------------------
Calculates the non-laboratory CRB-65 score (0-4 points) for community-acquired pneumonia (CAP)
to stratify 30-day mortality risk and guide outpatient vs inpatient vs ICU triage decisions.

Reference: Lim WS et al. Thorax 2002; 57:1005-1011 (British Thoracic Society BTS / NICE CG191)
Domain: Pulmonology / Infectious Diseases / Primary Care

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Core Algorithmic & Evaluation Engines

- **`CRB65CriteriaBreakdown`**: Individual criteria evaluations for CRB-65.
- **`CRB65Result`**: Complete CRB-65 Pneumonia Severity Score evaluation.
- **`CRB65Engine`**: Computational engine for BTS / NICE CRB-65 CAP assessment.

---

## 📐 Mathematical Formulation & Logic

```text
  total_score = pts_c + pts_r + pts_b + pts_65
  if total_score == 0:
  mortality = 8.2 if total_score == 2 else 5.3
  mortality = 31.3 if total_score == 4 else 23.0
```

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --task-id <value> --target <value> --primary <value> --secondary <value>
```

### Parameter Reference
- `--task-id`: Specifies input measurement or parameter value.
- `--target`: Specifies input measurement or parameter value.
- `--primary`: Specifies input measurement or parameter value.
- `--secondary`: Specifies input measurement or parameter value.
- `--critical`: Specifies input measurement or parameter value.
- `--status`: Specifies input measurement or parameter value.
- `--input`: Specifies input measurement or parameter value.
- `--output`: Specifies input measurement or parameter value.

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `Patient_ID` | Parameter / observation metric | Required |
| `v1` | Parameter / observation metric | Required |
| `v2` | Parameter / observation metric | Required |
| `v3` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t crb65-pneumonia-severity .
docker run -p 8000:8000 crb65-pneumonia-severity
```
