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


def test_extract_text_unsupported_extension_raises():
    with pytest.raises(UnsupportedDocumentError):
        extract_text("데이터.xlsx", b"...")


def test_extract_text_no_extension_raises():
    with pytest.raises(UnsupportedDocumentError):
        extract_text("noext", b"...")
