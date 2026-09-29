# CRB-65 Pneumonia Severity

### [Open the Live Application →](https://abusuraihsakhri.github.io/crb65-pneumonia-severity/)

A small CRB-65 calculator for adults with clinically diagnosed community-acquired pneumonia (CAP) in primary care. The calculator implements the NICE NG250 CRB-65 criteria and current 30-day mortality risk bands.

## What it calculates

CRB-65 assigns 1 point for each of:

- **C** — confusion: abbreviated Mental Test score 8 or less, or new disorientation
- **R** — respiratory rate **≥30 breaths/min**
- **B** — systolic blood pressure **<90 mmHg** or diastolic blood pressure **≤60 mmHg**
- **65** — age **≥65 years**

NICE NG250 stratifies 30-day mortality risk as:

| Score | Risk band | Place-of-care guidance |
|---:|---|---|
| 0 | Low, **<1%** | Primary care-led services with safety-netting advice, subject to clinical judgement |
| 1 | Intermediate, **1%–10%** | Shared decision: primary care-led care with safety-netting or referral to virtual ward, SDEC, hospital-at-home, or hospital |
| 2 | Intermediate, **1%–10%** | Consider referral to hospital |
| 3–4 | High, **>10%** | Consider hospital referral; determine urgency and place of care from the full clinical picture |

CRB-65 supports rather than replaces clinical judgement. Refer to hospital regardless of score when features suggest a more serious illness such as cardiorespiratory failure or sepsis. The calculator does not prescribe a specific antimicrobial regimen.

Reference: [NICE NG250 — Pneumonia: diagnosis and management](https://www.nice.org.uk/guidance/ng250/chapter/recommendations).

## Browser application

The GitHub Pages application is a static HTML/JavaScript calculator. All calculations run locally in the browser; the page does not send or store entered clinical values and does not require a backend or Python runtime.

## Command line

Python 3.10+ is supported.

```bash
python -m pip install -e .
crb65 eval --age 72 --rr 32 --sbp 118 --dbp 74 --confusion
```

JSON output:

```bash
crb65 eval --age 68 --rr 22 --sbp 128 --dbp 76 --json
```

Batch CSV processing:

```bash
crb65 batch -i sample.csv -o results.csv
```

Required CSV fields are `confusion`, `rr` (or `respiratory_rate`), `sbp` (or `systolic_bp`), `dbp` (or `diastolic_bp`), and `age` (or `age_years`). `patient_id` is optional.

## REST API

Install server dependencies and launch FastAPI:

```bash
python -m pip install -e '.[server]'
crb65-service serve --host 127.0.0.1 --port 8000
```

The clinical endpoint is `POST /api/crb65`; interactive OpenAPI documentation is available at `/docs` while the server is running. Auxiliary audit endpoints from earlier versions are retained for compatibility.

## Development and testing

```bash
python -m pip install -e '.[dev]'
ruff check .
pytest -q
python -m build
```

CI tests Python 3.10, 3.11, and 3.12, runs dependency consistency and vulnerability checks, builds Python distributions, and builds the container image.

## Docker

Copy `.env.example` to `.env` and provide a strong `AUDIT_SECRET_KEY` if the auxiliary audit endpoints are used:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
docker compose up --build
```

No production secret is committed to the repository.

## Browser compatibility

The Pages calculator uses standard HTML, CSS, and JavaScript and is intended for current desktop and mobile versions of Chrome, Firefox, Safari, and Edge. No WebAssembly or Pyodide runtime is required.

## License

MIT. See [LICENSE](LICENSE).
