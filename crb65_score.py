#!/usr/bin/env python3
"""
CRB-65 Outpatient & Inpatient Community-Acquired Pneumonia Severity Score
-------------------------------------------------------------------------
Calculates the non-laboratory CRB-65 score (0-4 points) for community-acquired pneumonia (CAP)
to stratify 30-day mortality risk and guide outpatient vs inpatient vs ICU triage decisions.

Reference: Lim WS et al. Thorax 2002; 57:1005-1011 (British Thoracic Society BTS / NICE CG191)
Domain: Pulmonology / Infectious Diseases / Primary Care
"""

import argparse
import csv
import json
import math
import sys
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Tuple


@dataclass
class CRB65CriteriaBreakdown:
    """Individual criteria evaluations for CRB-65."""
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
    """Complete CRB-65 Pneumonia Severity Score evaluation."""
    patient_id: str
    total_score: int  # 0 to 4
    risk_tier: str  # 'Low Risk (Group 1)', 'Intermediate Risk (Group 2)', 'High Risk (Group 3)'
    thirty_day_mortality_percent: float
    mortality_range_text: str
    recommended_disposition: str  # 'OUTPATIENT_HOME_CARE', 'INPATIENT_HOSPITAL_CARE', 'URGENT_HOSPITAL_OR_ICU'
    antibiotic_guidance: str
    criteria_breakdown: CRB65CriteriaBreakdown
    risk_factors_present: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


class CRB65Engine:
    """Computational engine for BTS / NICE CRB-65 CAP assessment."""

    @staticmethod
    def evaluate_confusion(confusion: bool) -> Tuple[int, Optional[str]]:
        """C: Confusion (AMT <=8, GCS <15, or new disorientation)."""
        if confusion:
            return 1, "New onset mental confusion (AMT <= 8 or GCS < 15, +1 pt)"
        return 0, None

    @staticmethod
    def evaluate_respiratory_rate(rr_bpm: int) -> Tuple[int, Optional[str]]:
        """R: Respiratory rate >= 30 breaths/min."""
        if rr_bpm >= 30:
            return 1, f"Tachypnea: Respiratory Rate {rr_bpm} >= 30 bpm (+1 pt)"
        return 0, None

    @staticmethod
    def evaluate_blood_pressure(sbp_mmhg: int, dbp_mmhg: int) -> Tuple[int, Optional[str]]:
        """B: Blood pressure: Systolic < 90 mmHg OR Diastolic <= 60 mmHg."""
        if sbp_mmhg < 90 or dbp_mmhg <= 60:
            return 1, f"Hypotension: SBP {sbp_mmhg} < 90 or DBP {dbp_mmhg} <= 60 mmHg (+1 pt)"
        return 0, None

    @staticmethod
    def evaluate_age(age_years: int) -> Tuple[int, Optional[str]]:
        """65: Age >= 65 years."""
        if age_years >= 65:
            return 1, f"Age {age_years} >= 65 years (+1 pt)"
        return 0, None

    @classmethod
    def evaluate(
        cls,
        patient_id: str = "PT-001",
        confusion: bool = False,
        respiratory_rate: int = 18,
        systolic_bp: int = 120,
        diastolic_bp: int = 80,
        age_years: int = 55,
    ) -> CRB65Result:
        """Evaluate full CRB-65 score, mortality estimate, and antibiotic triage."""
        factors = []

        pts_c, desc_c = cls.evaluate_confusion(confusion)
        if desc_c: factors.append(desc_c)

        pts_r, desc_r = cls.evaluate_respiratory_rate(respiratory_rate)
        if desc_r: factors.append(desc_r)

        pts_b, desc_b = cls.evaluate_blood_pressure(systolic_bp, diastolic_bp)
        if desc_b: factors.append(desc_b)

        pts_65, desc_65 = cls.evaluate_age(age_years)
        if desc_65: factors.append(desc_65)

        total_score = pts_c + pts_r + pts_b + pts_65

        if total_score == 0:
            tier = "Low Risk (Group 1)"
            mortality = 1.2
            mort_range = "0.9% - 1.5%"
            disp = "OUTPATIENT_HOME_CARE"
            abx = "Outpatient oral monotherapy: Amoxicillin 500mg-1g TID (or Doxycycline 100mg BID / Clarithromycin 500mg BID if penicillin-allergic) for 5 days."
        elif total_score in [1, 2]:
            tier = "Intermediate Risk (Group 2)"
            mortality = 8.2 if total_score == 2 else 5.3
            mort_range = "5.3% - 12.2%"
            disp = "INPATIENT_HOSPITAL_CARE"
            abx = "Inpatient admission indicated. Oral or IV dual therapy: Amoxicillin + Clarithromycin (or Levofloxacin / Moxifloxacin monotherapy)."
        else:
            tier = "High Risk (Group 3)"
            mortality = 31.3 if total_score == 4 else 23.0
            mort_range = "23.0% - 34.0%"
            disp = "URGENT_HOSPITAL_OR_ICU"
            abx = "Severe CAP emergency. Urgent hospital admission & HDU/ICU evaluation. Broad-spectrum IV dual therapy: Co-amoxiclav 1.2g IV TID + Clarithromycin 500mg IV BID (or Ceftriaxone 2g IV + Macrolide)."

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
            thirty_day_mortality_percent=mortality,
            mortality_range_text=mort_range,
            recommended_disposition=disp,
            antibiotic_guidance=abx,
            criteria_breakdown=breakdown,
            risk_factors_present=factors,
        )


# ==============================================================================
# CLI & BATCH PROCESSING
# ==============================================================================

def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="crb65-pneumonia-severity",
        description="CRB-65 Community-Acquired Pneumonia Severity & Mortality Risk Calculator"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Eval
    p_eval = subparsers.add_parser("eval", help="Evaluate CRB-65 score for patient")
    p_eval.add_argument("--patient-id", default="PT-2026-001")
    p_eval.add_argument("--confusion", action="store_true", help="New onset confusion / AMT <=8 / GCS <15")
    p_eval.add_argument("--rr", type=int, default=18, help="Respiratory Rate (breaths/min)")
    p_eval.add_argument("--sbp", type=int, default=120, help="Systolic Blood Pressure (mmHg)")
    p_eval.add_argument("--dbp", type=int, default=80, help="Diastolic Blood Pressure (mmHg)")
    p_eval.add_argument("--age", type=int, required=True, help="Age in years")
    p_eval.add_argument("--json", action="store_true", help="Output JSON format")

    # Chat
    p_chat = subparsers.add_parser("chat", help="Clinical questions about CRB-65")
    p_chat.add_argument("query", nargs="+")

    # Batch
    p_batch = subparsers.add_parser("batch", help="Batch evaluate CSV file")
    p_batch.add_argument("-i", "--input", required=True)
    p_batch.add_argument("-o", "--output", default="crb65_results.csv")

    args = parser.parse_args(argv)

    if args.command == "eval":
        res = CRB65Engine.evaluate(
            patient_id=args.patient_id,
            confusion=args.confusion,
            respiratory_rate=args.rr,
            systolic_bp=args.sbp,
            diastolic_bp=args.dbp,
            age_years=args.age,
        )
        if args.json:
            print(res.to_json())
        else:
            print("=" * 80)
            print(f"  CRB-65 PNEUMONIA SEVERITY REPORT — {res.patient_id}")
            print("=" * 80)
            print(f"  Total CRB-65 Score:     {res.total_score} / 4")
            print(f"  Risk Classification:    [{res.risk_tier}]")
            print(f"  30-Day Mortality Risk:  {res.thirty_day_mortality_percent:.1f}% ({res.mortality_range_text})")
            print(f"  Recommended Care:       {res.recommended_disposition}")
            print("-" * 80)
            print(f"  Criteria Met ({res.total_score}/4):")
            bd = res.criteria_breakdown
            print(f"    * C (Confusion):           {bd.confusion_points} pt ({bd.confusion_present})")
            print(f"    * R (RR >= 30 bpm):        {bd.respiratory_rate_points} pt ({bd.respiratory_rate_bpm} bpm)")
            print(f"    * B (SBP<90 or DBP<=60):   {bd.blood_pressure_points} pt ({bd.systolic_bp_mmhg}/{bd.diastolic_bp_mmhg} mmHg)")
            print(f"    * 65 (Age >= 65 years):    {bd.age_points} pt ({bd.age_years} years)")
            print("-" * 80)
            print(f"  Antibiotic Guidance: {res.antibiotic_guidance}")
            print("=" * 80)
        return 0

    elif args.command == "chat":
        q = " ".join(args.query).lower()
        if "criteria" in q or "variable" in q:
            print("CRB-65: Confusion (+1), Respiratory Rate >=30 (+1), Blood Pressure <90/<60 (+1), Age >=65 (+1).")
        elif "mortality" in q or "risk" in q:
            print("Score 0: Low Risk (1.2%), Score 1-2: Intermediate (5-12%), Score 3-4: High Risk / Severe (23-34%).")
        else:
            print("CRB-65 Pneumonia Severity Engine Active (BTS / NICE CG191 Guidelines).")
        return 0

    elif args.command == "batch":
        with open(args.input, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        out_rows = []
        for r in rows:
            pid = r.get("patient_id", "PT-000")
            conf = str(r.get("confusion", "0")).lower() in ["1", "true", "yes"]
            rr = int(r.get("rr", r.get("respiratory_rate", 18)))
            sbp = int(r.get("sbp", r.get("systolic_bp", 120)))
            dbp = int(r.get("dbp", r.get("diastolic_bp", 80)))
            age = int(r.get("age", r.get("age_years", 60)))

            eval_res = CRB65Engine.evaluate(
                patient_id=pid,
                confusion=conf,
                respiratory_rate=rr,
                systolic_bp=sbp,
                diastolic_bp=dbp,
                age_years=age,
            )
            out_rows.append({
                **r,
                "crb65_score": eval_res.total_score,
                "risk_tier": eval_res.risk_tier,
                "mortality_percent": eval_res.thirty_day_mortality_percent,
                "recommended_disposition": eval_res.recommended_disposition,
            })
        if out_rows:
            with open(args.output, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
                writer.writeheader()
                writer.writerows(out_rows)
        print(f"Batch processed {len(out_rows)} rows -> {args.output}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
