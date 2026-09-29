#!/usr/bin/env python3
"""CRB-65 score for adults with community-acquired pneumonia in primary care.

The scoring criteria and risk bands follow NICE NG250. CRB-65 supports, but does not
replace, clinical judgement. It is not intended for children or for determining a
specific antimicrobial regimen.
"""

import argparse
import csv
import json
import sys
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple


class ClinicalValueError(ValueError):
    """Raised when required clinical inputs are missing or outside accepted bounds."""


def _validate_clinical_params(
    respiratory_rate: int,
    systolic_bp: int,
    diastolic_bp: int,
    age_years: int,
) -> None:
    """Validate adult CRB-65 inputs before scoring."""
    if not isinstance(age_years, int) or not 18 <= age_years <= 120:
        raise ClinicalValueError(f"Age must be an integer between 18 and 120 years, got {age_years}")
    if not isinstance(respiratory_rate, int) or not 1 <= respiratory_rate <= 100:
        raise ClinicalValueError(
            f"Respiratory rate must be an integer between 1 and 100 breaths/min, got {respiratory_rate}"
        )
    if not isinstance(systolic_bp, int) or not 1 <= systolic_bp <= 300:
        raise ClinicalValueError(f"Systolic BP must be an integer between 1 and 300 mmHg, got {systolic_bp}")
    if not isinstance(diastolic_bp, int) or not 1 <= diastolic_bp <= 200:
        raise ClinicalValueError(f"Diastolic BP must be an integer between 1 and 200 mmHg, got {diastolic_bp}")
    if diastolic_bp > systolic_bp:
        raise ClinicalValueError(
            f"Diastolic BP ({diastolic_bp}) cannot exceed systolic BP ({systolic_bp})"
        )


@dataclass
class CRB65CriteriaBreakdown:
    """Individual CRB-65 criterion evaluations."""

    confusion_present: bool
    confusion_points: int
    respiratory_rate_bpm: int
    respiratory_rate_points: int
    systolic_bp_mmhg: int
    diastolic_bp_mmhg: int
    blood_pressure_points: int
    age_years: int
    age_points: int


@dataclass
class CRB65Result:
    """Complete CRB-65 evaluation using current NICE risk bands."""

    patient_id: str
    total_score: int
    risk_tier: str
    thirty_day_mortality_percent: Optional[float]
    mortality_range_text: str
    recommended_disposition: str
    antibiotic_guidance: str
    criteria_breakdown: CRB65CriteriaBreakdown
    risk_factors_present: List[str]
    clinical_note: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


class CRB65Engine:
    """CRB-65 scoring engine for adults with clinically diagnosed CAP in primary care."""

    @staticmethod
    def evaluate_confusion(confusion: bool) -> Tuple[int, Optional[str]]:
        """C: AMT <= 8 or new disorientation in person, place, or time."""
        if confusion:
            return 1, "Confusion present (AMT <= 8 or new disorientation, +1 pt)"
        return 0, None

    @staticmethod
    def evaluate_respiratory_rate(rr_bpm: int) -> Tuple[int, Optional[str]]:
        """R: respiratory rate >= 30 breaths/min."""
        if rr_bpm >= 30:
            return 1, f"Respiratory rate {rr_bpm} >= 30 breaths/min (+1 pt)"
        return 0, None

    @staticmethod
    def evaluate_blood_pressure(sbp_mmhg: int, dbp_mmhg: int) -> Tuple[int, Optional[str]]:
        """B: systolic BP < 90 mmHg or diastolic BP <= 60 mmHg."""
        if sbp_mmhg < 90 or dbp_mmhg <= 60:
            return 1, f"Low blood pressure: {sbp_mmhg}/{dbp_mmhg} mmHg (+1 pt)"
        return 0, None

    @staticmethod
    def evaluate_age(age_years: int) -> Tuple[int, Optional[str]]:
        """65: age >= 65 years."""
        if age_years >= 65:
            return 1, f"Age {age_years} >= 65 years (+1 pt)"
        return 0, None

    @classmethod
    def evaluate(
        cls,
        patient_id: str = "ANON",
        confusion: bool = False,
        respiratory_rate: Optional[int] = None,
        systolic_bp: Optional[int] = None,
        diastolic_bp: Optional[int] = None,
        age_years: Optional[int] = None,
    ) -> CRB65Result:
        """Calculate CRB-65 and return NICE-aligned risk/disposition guidance."""
        _validate_clinical_params(respiratory_rate, systolic_bp, diastolic_bp, age_years)
        factors: List[str] = []

        pts_c, desc_c = cls.evaluate_confusion(confusion)
        if desc_c:
            factors.append(desc_c)
        pts_r, desc_r = cls.evaluate_respiratory_rate(respiratory_rate)
        if desc_r:
            factors.append(desc_r)
        pts_b, desc_b = cls.evaluate_blood_pressure(systolic_bp, diastolic_bp)
        if desc_b:
            factors.append(desc_b)
        pts_65, desc_65 = cls.evaluate_age(age_years)
        if desc_65:
            factors.append(desc_65)

        total_score = pts_c + pts_r + pts_b + pts_65

        if total_score == 0:
            tier = "Low Risk (Group 1)"
            mortality_range = "<1%"
            disposition = "PRIMARY_CARE_WITH_SAFETY_NETTING"
        elif total_score == 1:
            tier = "Intermediate Risk (Group 2)"
            mortality_range = "1% to 10%"
            disposition = "SHARED_DECISION_COMMUNITY_OR_REFERRAL"
        elif total_score == 2:
            tier = "Intermediate Risk (Group 2)"
            mortality_range = "1% to 10%"
            disposition = "CONSIDER_HOSPITAL_REFERRAL"
        else:
            tier = "High Risk (Group 3)"
            mortality_range = ">10%"
            disposition = "CONSIDER_HOSPITAL_REFERRAL_HIGH_RISK"

        breakdown = CRB65CriteriaBreakdown(
            confusion_present=confusion,
            confusion_points=pts_c,
            respiratory_rate_bpm=respiratory_rate,
            respiratory_rate_points=pts_r,
            systolic_bp_mmhg=systolic_bp,
            diastolic_bp_mmhg=diastolic_bp,
            blood_pressure_points=pts_b,
            age_years=age_years,
            age_points=pts_65,
        )

        return CRB65Result(
            patient_id=patient_id,
            total_score=total_score,
            risk_tier=tier,
            thirty_day_mortality_percent=None,
            mortality_range_text=mortality_range,
            recommended_disposition=disposition,
            antibiotic_guidance=(
                "CRB-65 alone does not determine a specific antimicrobial regimen. "
                "Use current local/NICE antimicrobial guidance and account for allergy, pregnancy, "
                "comorbidity, disease severity, microbiology, and local resistance patterns."
            ),
            criteria_breakdown=breakdown,
            risk_factors_present=factors,
            clinical_note=(
                "Use CRB-65 together with clinical judgement. Refer to hospital regardless of score "
                "when there are signs of a more serious illness such as cardiorespiratory failure or sepsis."
            ),
        )


def _required_row_value(row: Dict[str, str], *names: str) -> str:
    for name in names:
        value = row.get(name)
        if value is not None and str(value).strip() != "":
            return str(value).strip()
    raise ClinicalValueError(f"Missing required CSV field; expected one of: {', '.join(names)}")


def _parse_bool(value: Any) -> bool:
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y"}:
        return True
    if normalized in {"0", "false", "no", "n"}:
        return False
    raise ClinicalValueError(f"Boolean value must be one of true/false, yes/no, or 1/0; got {value!r}")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="crb65-pneumonia-severity",
        description="CRB-65 community-acquired pneumonia severity calculator",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_eval = subparsers.add_parser("eval", help="Evaluate CRB-65 score")
    p_eval.add_argument("--patient-id", default="ANON")
    p_eval.add_argument("--confusion", action="store_true", help="AMT <=8 or new disorientation")
    p_eval.add_argument("--rr", type=int, required=True, help="Respiratory rate (breaths/min)")
    p_eval.add_argument("--sbp", type=int, required=True, help="Systolic blood pressure (mmHg)")
    p_eval.add_argument("--dbp", type=int, required=True, help="Diastolic blood pressure (mmHg)")
    p_eval.add_argument("--age", type=int, required=True, help="Age in years (18-120)")
    p_eval.add_argument("--json", action="store_true", help="Output JSON")

    p_chat = subparsers.add_parser("chat", help="Show CRB-65 criteria/risk summary")
    p_chat.add_argument("query", nargs="+")

    p_batch = subparsers.add_parser("batch", help="Batch-evaluate CSV records")
    p_batch.add_argument("-i", "--input", required=True)
    p_batch.add_argument("-o", "--output", default="crb65_results.csv")

    args = parser.parse_args(argv)

    if args.command == "eval":
        result = CRB65Engine.evaluate(
            patient_id=args.patient_id,
            confusion=args.confusion,
            respiratory_rate=args.rr,
            systolic_bp=args.sbp,
            diastolic_bp=args.dbp,
            age_years=args.age,
        )
        if args.json:
            print(result.to_json())
        else:
            bd = result.criteria_breakdown
            print("=" * 72)
            print(f"CRB-65 report — {result.patient_id}")
            print("=" * 72)
            print(f"Score: {result.total_score}/4")
            print(f"Risk: {result.risk_tier} ({result.mortality_range_text} 30-day mortality risk)")
            print(f"Place-of-care guidance: {result.recommended_disposition}")
            print(f"C confusion: {bd.confusion_points} | R >=30: {bd.respiratory_rate_points} | "
                  f"B low BP: {bd.blood_pressure_points} | age >=65: {bd.age_points}")
            print(result.clinical_note)
        return 0

    if args.command == "chat":
        query = " ".join(args.query).lower()
        if "criteria" in query or "variable" in query:
            print("CRB-65: confusion, respiratory rate >=30/min, SBP <90 or DBP <=60 mmHg, age >=65; 1 point each.")
        else:
            print("NICE NG250 risk bands: score 0 <1%; score 1-2 1-10%; score 3-4 >10%. Use clinical judgement with the score.")
        return 0

    if args.command == "batch":
        with open(args.input, mode="r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))

        out_rows: List[Dict[str, Any]] = []
        for row_number, row in enumerate(rows, start=2):
            try:
                result = CRB65Engine.evaluate(
                    patient_id=row.get("patient_id", "ANON") or "ANON",
                    confusion=_parse_bool(_required_row_value(row, "confusion")),
                    respiratory_rate=int(_required_row_value(row, "rr", "respiratory_rate")),
                    systolic_bp=int(_required_row_value(row, "sbp", "systolic_bp")),
                    diastolic_bp=int(_required_row_value(row, "dbp", "diastolic_bp")),
                    age_years=int(_required_row_value(row, "age", "age_years")),
                )
            except (ValueError, ClinicalValueError) as exc:
                raise ClinicalValueError(f"Invalid data on CSV row {row_number}: {exc}") from exc

            out_rows.append(
                {
                    **row,
                    "crb65_score": result.total_score,
                    "risk_tier": result.risk_tier,
                    "mortality_risk": result.mortality_range_text,
                    "recommended_disposition": result.recommended_disposition,
                }
            )

        if out_rows:
            with open(args.output, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
                writer.writeheader()
                writer.writerows(out_rows)
        print(f"Batch processed {len(out_rows)} rows -> {args.output}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
