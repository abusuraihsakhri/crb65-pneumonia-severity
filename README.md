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

  CRB-65 Criteria (1 point each):
    C: Confusion (AMT <= 8, GCS < 15, or new disorientation)
    R: Respiratory Rate >= 30 breaths/min
    B: Blood Pressure (Systolic < 90 mmHg OR Diastolic <= 60 mmHg)
    65: Age >= 65 years

  Risk Stratification:
    Score 0:     Low Risk (Group 1)       ~1.2% 30-day mortality  → Outpatient
    Score 1-2:   Intermediate Risk (Group 2)  ~5-12% mortality    → Inpatient
    Score 3-4:   High Risk (Group 3)       ~23-31% mortality     → Urgent/ICU
```

---

## 💻 CLI Quickstart & Usage

### 1. Evaluate a Single Patient
```bash
python crb65_score.py eval --age 72 --rr 32 --confusion
```

### 2. JSON Output
```bash
python crb65_score.py eval --age 68 --json
```

### 3. Batch Process CSV
```bash
python crb65_score.py batch -i sample.csv -o results.csv
```

### 4. Clinical Q&A
```bash
python crb65_score.py chat "What are the CRB-65 criteria?"
```

### Parameter Reference
| Parameter | Description | Default |
|:----------|:------------|:--------|
| `--patient-id` | Patient identifier | `PT-2026-001` |
| `--confusion` | New onset confusion / AMT <=8 / GCS <15 | `False` |
| `--rr` | Respiratory Rate (breaths/min) | `18` |
| `--sbp` | Systolic Blood Pressure (mmHg) | `120` |
| `--dbp` | Diastolic Blood Pressure (mmHg) | `80` |
| `--age` | Age in years (required) | — |
| `--json` | Output JSON format | `False` |

### Input Data Schema (Batch CSV)

| Field | Description | Requirement |
|:------|:------------|:------------|
| `patient_id` | Patient identifier | Required |
| `confusion` | Confusion present (1/true/yes) | Optional (default: 0) |
| `rr` | Respiratory Rate (breaths/min) | Optional (default: 18) |
| `sbp` | Systolic Blood Pressure (mmHg) | Optional (default: 120) |
| `dbp` | Diastolic Blood Pressure (mmHg) | Optional (default: 80) |
| `age` | Age in years | Required |

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
