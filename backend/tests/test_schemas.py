from app.schemas import DiagnosisItem, Citation


def test_diagnosis_item_defaults_needs_review():
    item = DiagnosisItem(id="d1", channel="이메일", summary="오픈율 하락", kind="weakness")
    assert item.status == "needs_review"
    assert item.citations == []


def test_diagnosis_item_with_citation():
    item = DiagnosisItem(
        id="d1", channel="이메일", summary="오픈율 하락", kind="weakness",
        citations=[Citation(quote="오픈율이 12%로 하락", source_id="s1")],
    )
    assert item.citations[0].source_id == "s1"
