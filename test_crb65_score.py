#!/usr/bin/env python3
"""
Comprehensive Unit Test Suite for CRB-65 Pneumonia Severity Score Engine
Tests individual criteria scoring (Confusion, RR, BP, Age), risk groups (0, 1-2, 3-4),
30-day mortality risk projections, outpatient vs inpatient disposition recommendations,
JSON export, CLI commands, and input validation.
"""

import unittest
from crb65_score import (
    CRB65Engine,
    CRB65Result,
    CRB65CriteriaBreakdown,
    ClinicalValueError,
    _validate_clinical_params,
    main,
)


class TestIndividualCriteria(unittest.TestCase):
    """Test suite for individual component scoring."""

    def test_confusion_scoring(self):
        # Confusion true -> 1 pt
        pts, desc = CRB65Engine.evaluate_confusion(True)
        self.assertEqual(pts, 1)
        self.assertIn("mental confusion", desc)

        # Confusion false -> 0 pts
        pts, desc = CRB65Engine.evaluate_confusion(False)
        self.assertEqual(pts, 0)
        self.assertIsNone(desc)

    def test_respiratory_rate_scoring(self):
        # RR < 30 -> 0 pts
        self.assertEqual(CRB65Engine.evaluate_respiratory_rate(18)[0], 0)
        self.assertEqual(CRB65Engine.evaluate_respiratory_rate(29)[0], 0)

        # RR >= 30 -> 1 pt
        self.assertEqual(CRB65Engine.evaluate_respiratory_rate(30)[0], 1)
        self.assertEqual(CRB65Engine.evaluate_respiratory_rate(38)[0], 1)

    def test_blood_pressure_scoring(self):
        # Normal BP (120/80) -> 0 pts
        self.assertEqual(CRB65Engine.evaluate_blood_pressure(120, 80)[0], 0)

        # Systolic < 90 (85/65) -> 1 pt
        self.assertEqual(CRB65Engine.evaluate_blood_pressure(85, 65)[0], 1)

        # Diastolic <= 60 (110/58) -> 1 pt
        self.assertEqual(CRB65Engine.evaluate_blood_pressure(110, 58)[0], 1)
        self.assertEqual(CRB65Engine.evaluate_blood_pressure(110, 60)[0], 1)

        # Both low (80/50) -> 1 pt
        self.assertEqual(CRB65Engine.evaluate_blood_pressure(80, 50)[0], 1)

    def test_age_scoring(self):
        # Age < 65 -> 0 pts
        self.assertEqual(CRB65Engine.evaluate_age(45)[0], 0)
        self.assertEqual(CRB65Engine.evaluate_age(64)[0], 0)

        # Age >= 65 -> 1 pt
        self.assertEqual(CRB65Engine.evaluate_age(65)[0], 1)
        self.assertEqual(CRB65Engine.evaluate_age(82)[0], 1)


class TestTotalScoreAndRiskGroups(unittest.TestCase):
    """Test suite for full CRB-65 total scores and risk tiers."""

    def test_score_0_low_risk_outpatient(self):
        # 40yo, no confusion, RR 18, BP 120/80 -> Score 0
        res = CRB65Engine.evaluate(
            patient_id="PT-001",
            confusion=False,
            respiratory_rate=18,
            systolic_bp=120,
            diastolic_bp=80,
            age_years=40,
        )
        self.assertEqual(res.total_score, 0)
        self.assertEqual(res.risk_tier, "Low Risk (Group 1)")
        self.assertEqual(res.thirty_day_mortality_percent, 1.2)
        self.assertEqual(res.recommended_disposition, "OUTPATIENT_HOME_CARE")
        self.assertIn("Amoxicillin", res.antibiotic_guidance)

    def test_score_1_intermediate_risk(self):
        # Age 68 (>=65 -> +1), other parameters normal -> Score 1
        res = CRB65Engine.evaluate(
            patient_id="PT-002",
            confusion=False,
            respiratory_rate=22,
            systolic_bp=130,
            diastolic_bp=85,
            age_years=68,
        )
        self.assertEqual(res.total_score, 1)
        self.assertEqual(res.risk_tier, "Intermediate Risk (Group 2)")
        self.assertEqual(res.thirty_day_mortality_percent, 5.3)
        self.assertEqual(res.recommended_disposition, "INPATIENT_HOSPITAL_CARE")

    def test_score_2_intermediate_risk(self):
        # Age 70 (+1), RR 32 (+1) -> Score 2
        res = CRB65Engine.evaluate(
            patient_id="PT-003",
            confusion=False,
            respiratory_rate=32,
            systolic_bp=120,
            diastolic_bp=80,
            age_years=70,
        )
        self.assertEqual(res.total_score, 2)
        self.assertEqual(res.risk_tier, "Intermediate Risk (Group 2)")
        self.assertEqual(res.thirty_day_mortality_percent, 8.2)
        self.assertEqual(res.recommended_disposition, "INPATIENT_HOSPITAL_CARE")

    def test_score_3_high_risk_severe(self):
        # Confusion (+1), RR 34 (+1), Age 75 (+1), Normal BP -> Score 3
        res = CRB65Engine.evaluate(
            patient_id="PT-004",
            confusion=True,
            respiratory_rate=34,
            systolic_bp=125,
            diastolic_bp=75,
            age_years=75,
        )
        self.assertEqual(res.total_score, 3)
        self.assertEqual(res.risk_tier, "High Risk (Group 3)")
        self.assertEqual(res.thirty_day_mortality_percent, 23.0)
        self.assertEqual(res.recommended_disposition, "URGENT_HOSPITAL_OR_ICU")

    def test_score_4_maximum_severity(self):
        # All 4 criteria met: Confusion (+1), RR 36 (+1), BP 85/55 (+1), Age 80 (+1) -> Score 4
        res = CRB65Engine.evaluate(
            patient_id="PT-005",
            confusion=True,
            respiratory_rate=36,
            systolic_bp=85,
            diastolic_bp=55,
            age_years=80,
        )
        self.assertEqual(res.total_score, 4)
        self.assertEqual(res.risk_tier, "High Risk (Group 3)")
        self.assertEqual(res.thirty_day_mortality_percent, 31.3)
        self.assertEqual(res.recommended_disposition, "URGENT_HOSPITAL_OR_ICU")
        self.assertIn("HDU/ICU", res.antibiotic_guidance)


class TestEndToEndAndCLI(unittest.TestCase):
    """Test suite for JSON export and CLI operations."""

    def test_to_json_serialization(self):
        res = CRB65Engine.evaluate(patient_id="JSON-01", age_years=65, respiratory_rate=32)
        json_str = res.to_json()
        self.assertIn("JSON-01", json_str)
        self.assertIn("total_score", json_str)
        self.assertIn("thirty_day_mortality_percent", json_str)

    def test_cli_eval_command(self):
        self.assertEqual(main(["eval", "--age", "72", "--rr", "32", "--confusion"]), 0)
        self.assertEqual(main(["eval", "--age", "50", "--json"]), 0)

    def test_cli_chat_command(self):
        self.assertEqual(main(["chat", "What", "are", "the", "crb65", "criteria?"]), 0)


class TestInputValidation(unittest.TestCase):
    """Test suite for clinical parameter validation."""

    def test_valid_params_accepted(self):
        """Normal clinical parameters should not raise."""
        _validate_clinical_params(respiratory_rate=18, systolic_bp=120, diastolic_bp=80, age_years=55)
        _validate_clinical_params(respiratory_rate=30, systolic_bp=90, diastolic_bp=60, age_years=65)
        _validate_clinical_params(respiratory_rate=0, systolic_bp=0, diastolic_bp=0, age_years=0)

    def test_negative_age_rejected(self):
        with self.assertRaises(ClinicalValueError):
            _validate_clinical_params(respiratory_rate=18, systolic_bp=120, diastolic_bp=80, age_years=-5)

    def test_age_too_high_rejected(self):
        with self.assertRaises(ClinicalValueError):
            _validate_clinical_params(respiratory_rate=18, systolic_bp=120, diastolic_bp=80, age_years=200)

    def test_negative_rr_rejected(self):
        with self.assertRaises(ClinicalValueError):
            _validate_clinical_params(respiratory_rate=-1, systolic_bp=120, diastolic_bp=80, age_years=50)

    def test_rr_too_high_rejected(self):
        with self.assertRaises(ClinicalValueError):
            _validate_clinical_params(respiratory_rate=150, systolic_bp=120, diastolic_bp=80, age_years=50)

    def test_negative_bp_rejected(self):
        with self.assertRaises(ClinicalValueError):
            _validate_clinical_params(respiratory_rate=18, systolic_bp=-10, diastolic_bp=80, age_years=50)
        with self.assertRaises(ClinicalValueError):
            _validate_clinical_params(respiratory_rate=18, systolic_bp=120, diastolic_bp=-5, age_years=50)

    def test_bp_too_high_rejected(self):
        with self.assertRaises(ClinicalValueError):
            _validate_clinical_params(respiratory_rate=18, systolic_bp=350, diastolic_bp=80, age_years=50)
        with self.assertRaises(ClinicalValueError):
            _validate_clinical_params(respiratory_rate=18, systolic_bp=120, diastolic_bp=250, age_years=50)

    def test_diastolic_exceeds_systolic_rejected(self):
        with self.assertRaises(ClinicalValueError):
            _validate_clinical_params(respiratory_rate=18, systolic_bp=80, diastolic_bp=90, age_years=50)

    def test_engine_evaluate_validates(self):
        """CRB65Engine.evaluate should reject invalid parameters."""
        with self.assertRaises(ClinicalValueError):
            CRB65Engine.evaluate(age_years=-1)
        with self.assertRaises(ClinicalValueError):
            CRB65Engine.evaluate(age_years=50, respiratory_rate=200)


if __name__ == "__main__":
    unittest.main()
