import io
import pytest
from app.doctext import extract_text, UnsupportedDocumentError


def test_extract_text_txt():
    result = extract_text("메모.txt", "오픈율이 하락했다.".encode("utf-8"))
    assert result == "오픈율이 하락했다."


def test_extract_text_md():
    result = extract_text("notes.md", "# 제목\n본문".encode("utf-8"))
    assert result == "# 제목\n본문"


def test_extract_text_docx_roundtrip():
    docx = pytest.importorskip("docx")
    doc = docx.Document()
    doc.add_paragraph("오픈율이 12%에서 8%로 하락했다.")
    doc.add_paragraph("구독 해지가 급증했다.")
    buf = io.BytesIO()
    doc.save(buf)

    result = extract_text("보고서.docx", buf.getvalue())
    assert "오픈율이 12%에서 8%로 하락했다." in result
    assert "구독 해지가 급증했다." in result


def test_extract_text_pdf_blank_page_returns_empty():
    pypdf = pytest.importorskip("pypdf")
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buf = io.BytesIO()
    writer.write(buf)

    result = extract_text("빈문서.pdf", buf.getvalue())
    assert result == ""


def test_extract_text_pptx_roundtrip():
    pptx = pytest.importorskip("pptx")
    prs = pptx.Presentation()
    slide_layout = prs.slide_layouts[1]
    slide1 = prs.slides.add_slide(slide_layout)
    slide1.shapes.title.text = "8월 캠페인 현황"
    slide1.placeholders[1].text = "오픈율이 12%에서 8%로 하락했다."
    slide2 = prs.slides.add_slide(slide_layout)
    slide2.shapes.title.text = "다음 단계"
    slide2.placeholders[1].text = "콘텐츠 개선안을 수립한다."
    buf = io.BytesIO()
    prs.save(buf)

    result = extract_text("발표자료.pptx", buf.getvalue())
    assert "--- slide 1 ---" in result
    assert "8월 캠페인 현황" in result
    assert "오픈율이 12%에서 8%로 하락했다." in result
    assert "--- slide 2 ---" in result
    assert "콘텐츠 개선안을 수립한다." in result


def test_extract_text_unsupported_extension_raises():
    with pytest.raises(UnsupportedDocumentError):
        extract_text("데이터.xlsx", b"...")


def test_extract_text_no_extension_raises():
    with pytest.raises(UnsupportedDocumentError):
        extract_text("noext", b"...")
