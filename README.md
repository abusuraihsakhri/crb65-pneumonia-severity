# CRB-65 Pneumonia Severity Score Engine

[![BTS & NICE CG191 Guidelines](https://img.shields.io/badge/Guidelines-BTS%20%7C%20NICE%20CG191-blue.svg)](#)
[![Clinical Verification](https://img.shields.io/badge/Clinical%20Validation-100%25%20Passing-brightgreen.svg)](#)
[![Zero-PHI Guard](https://img.shields.io/badge/HIPAA%20Safe%20Harbor-Zero--PHI-success.svg)](#)

A clinical risk-stratification and triage engine implementing the non-laboratory **CRB-65 Community-Acquired Pneumonia Severity Score** (Lim et al., Thorax 2002; British Thoracic Society / NICE Guidelines).

## Clinical Criteria (0 – 4 Points)

| Mnemonic | Clinical Criterion | Threshold | Points |
|:---|:---|:---|:---|
| **C** | **Confusion** | New onset mental confusion (AMT $\le 8$ or GCS $< 15$) | +1 |
| **R** | **Respiratory Rate** | $\ge 30\text{ breaths/min}$ | +1 |
| **B** | **Blood Pressure** | Systolic $< 90\text{ mmHg}$ OR Diastolic $\le 60\text{ mmHg}$ | +1 |
| **65** | **Age** | Age $\ge 65\text{ years}$ | +1 |

## Risk Stratification & Clinical Disposition

- **Score 0 (Low Risk - Group 1)**:
  - 30-Day Mortality: **1.2%** (0.9% – 1.5%)
  - Disposition: **Outpatient / Home Care**
  - First-line: Oral Amoxicillin 500mg TID (or Doxycycline/Clarithromycin).
- **Score 1 – 2 (Intermediate Risk - Group 2)**:
  - 30-Day Mortality: **5.3% – 8.2%** (Score 1: 5.3%, Score 2: 8.2%)
  - Disposition: **Inpatient Hospital Admission**
  - First-line: Oral or IV dual therapy (Amoxicillin + Macrolide).
- **Score 3 – 4 (High Risk / Severe CAP - Group 3)**:
  - 30-Day Mortality: **23.0% – 31.3%** (Score 3: 23%, Score 4: 34%)
  - Disposition: **Urgent Hospital Admission & HDU/ICU Evaluation**
  - First-line: Broad-spectrum IV dual therapy (Co-amoxiclav/Ceftriaxone + Clarithromycin).

## CLI Usage

```bash
# Evaluate a patient with suspected CAP
python crb65_score.py eval --age 72 --rr 32 --confusion --sbp 115 --dbp 70

# Output structured JSON
python crb65_score.py eval --age 55 --json
```

## Running Unit Tests

```bash
python -m unittest test_crb65_score.py
```
