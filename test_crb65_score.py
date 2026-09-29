#!/usr/bin/env python3
"""Tests for the CRB-65 scoring engine and command-line interface."""
import csv
import json
from pathlib import Path

import pytest

from crb65_score import (
    CRB65Engine,
    ClinicalValueError,
    _parse_bool,
    _validate_clinical_params,
    main,
)


def test_individual_criteria_boundaries():
    assert CRB65Engine.evaluate_confusion(False)[0] == 0
    assert CRB65Engine.evaluate_confusion(True)[0] == 1
    assert CRB65Engine.evaluate_respiratory_rate(29)[0] == 0
    assert CRB65Engine.evaluate_respiratory_rate(30)[0] == 1
    assert CRB65Engine.evaluate_blood_pressure(90, 61)[0] == 0
    assert CRB65Engine.evaluate_blood_pressure(89, 61)[0] == 1
    assert CRB65Engine.evaluate_blood_pressure(120, 60)[0] == 1
    assert CRB65Engine.evaluate_age(64)[0] == 0
    assert CRB65Engine.evaluate_age(65)[0] == 1


@pytest.mark.parametrize(
    ("kwargs", "score", "risk", "mortality_range", "disposition"),
    [
        (
            dict(confusion=False, respiratory_rate=18, systolic_bp=120, diastolic_bp=80, age_years=40),
            0,
            "Low Risk (Group 1)",
            "<1%",
            "PRIMARY_CARE_WITH_SAFETY_NETTING",
        ),
        (
            dict(confusion=False, respiratory_rate=18, systolic_bp=120, diastolic_bp=80, age_years=70),
            1,
            "Intermediate Risk (Group 2)",
            "1% to 10%",
            "SHARED_DECISION_COMMUNITY_OR_REFERRAL",
        ),
        (
            dict(confusion=False, respiratory_rate=32, systolic_bp=120, diastolic_bp=80, age_years=70),
            2,
            "Intermediate Risk (Group 2)",
            "1% to 10%",
            "CONSIDER_HOSPITAL_REFERRAL",
        ),
        (
            dict(confusion=True, respiratory_rate=34, systolic_bp=120, diastolic_bp=80, age_years=75),
            3,
            "High Risk (Group 3)",
            ">10%",
            "CONSIDER_HOSPITAL_REFERRAL_HIGH_RISK",
        ),
        (
            dict(confusion=True, respiratory_rate=36, systolic_bp=85, diastolic_bp=55, age_years=80),
            4,
            "High Risk (Group 3)",
            ">10%",
            "CONSIDER_HOSPITAL_REFERRAL_HIGH_RISK",
        ),
    ],
)
def test_nice_risk_bands_and_place_of_care(kwargs, score, risk, mortality_range, disposition):
    result = CRB65Engine.evaluate(**kwargs)
    assert result.total_score == score
    assert result.risk_tier == risk
    assert result.thirty_day_mortality_percent is None
    assert result.mortality_range_text == mortality_range
    assert result.recommended_disposition == disposition
    assert "clinical judgement" in result.clinical_note.lower()
    assert "does not determine" in result.antibiotic_guidance.lower()


def test_json_serialization_uses_risk_band_without_false_precision():
    result = CRB65Engine.evaluate(
        patient_id="CASE-01",
        confusion=False,
        respiratory_rate=30,
        systolic_bp=120,
        diastolic_bp=80,
        age_years=65,
    )
    payload = json.loads(result.to_json())
    assert payload["patient_id"] == "CASE-01"
    assert payload["total_score"] == 2
    assert payload["thirty_day_mortality_percent"] is None
    assert payload["mortality_range_text"] == "1% to 10%"


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(respiratory_rate=18, systolic_bp=120, diastolic_bp=80, age_years=17),
        dict(respiratory_rate=0, systolic_bp=120, diastolic_bp=80, age_years=50),
        dict(respiratory_rate=18, systolic_bp=0, diastolic_bp=0, age_years=50),
        dict(respiratory_rate=18, systolic_bp=80, diastolic_bp=90, age_years=50),
    ],
)
def test_invalid_clinical_values_are_rejected(kwargs):
    with pytest.raises(ClinicalValueError):
        _validate_clinical_params(**kwargs)


def test_boolean_parser_is_strict():
    assert _parse_bool("true") is True
    assert _parse_bool("1") is True
    assert _parse_bool("false") is False
    assert _parse_bool("0") is False
    with pytest.raises(ClinicalValueError):
        _parse_bool("maybe")


def test_cli_eval_requires_measured_vitals(capsys):
    assert main(["eval", "--age", "72", "--rr", "32", "--sbp", "118", "--dbp", "74", "--confusion"]) == 0
    assert "Score:" in capsys.readouterr().out


def test_batch_requires_complete_data_and_writes_results(tmp_path: Path):
    source = tmp_path / "input.csv"
    output = tmp_path / "output.csv"
    source.write_text(
        "patient_id,confusion,rr,sbp,dbp,age\n"
        "A,false,20,120,80,40\n"
        "B,true,32,88,58,75\n",
        encoding="utf-8",
    )
    assert main(["batch", "-i", str(source), "-o", str(output)]) == 0
    rows = list(csv.DictReader(output.open(encoding="utf-8")))
    assert rows[0]["crb65_score"] == "0"
    assert rows[1]["crb65_score"] == "4"
    assert rows[1]["mortality_risk"] == ">10%"


def test_batch_rejects_missing_measurements(tmp_path: Path):
    source = tmp_path / "bad.csv"
    source.write_text("patient_id,confusion,age\nA,false,70\n", encoding="utf-8")
    with pytest.raises(ClinicalValueError, match="CSV row 2"):
        main(["batch", "-i", str(source), "-o", str(tmp_path / "out.csv")])
