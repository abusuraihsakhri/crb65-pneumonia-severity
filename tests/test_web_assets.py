from pathlib import Path


def test_pages_app_is_static_and_crb65_specific():
    html = Path("web/index.html").read_text(encoding="utf-8")
    assert "CRB-65 Pneumonia Severity Calculator" in html
    assert "NICE NG250" in html
    assert "fetch(" not in html
    assert "/api/audit" not in html
    assert "rr >= 30" in html
    assert "sbp < 90 || dbp <= 60" in html
    assert "score === 2" in html
    assert "calculations run entirely in your browser" in html
