from datetime import datetime

from app.database.models import Article
from app.services.formatter import MAX_MESSAGE_LEN, format_article_message, format_digest


def _article(**kwargs) -> Article:
    defaults = dict(
        id=1, source_id=1,
        original_title="Test <script>alert(1)</script> title",
        translated_title="Sinov sarlavhasi",
        original_summary="Original summary",
        translated_summary="Qisqa mazmun & tavsif",
        url="https://example.com/news/1",
        published_at=datetime(2026, 7, 20, 9, 30),
        content_hash="h", keywords=[], importance_score=0.5, reliability_score=0.8,
    )
    defaults.update(kwargs)
    return Article(**defaults)


def test_message_contains_required_parts():
    text = format_article_message(
        _article(), source_name="Reuters", category_name="Sun'iy intellekt",
        category_slug="ai", tz_name="Asia/Tashkent",
    )
    assert "Sinov sarlavhasi" in text
    assert "Qisqa mazmun &amp; tavsif" in text
    assert "Reuters" in text
    assert "Sun&#x27;iy intellekt" in text  # apostrof HTML-escape qilinadi
    # Havola tugma emas, matn oxirida bo'lishi kerak
    assert '<a href="https://example.com/news/1">Batafsil o\'qish</a>' in text
    assert "14:30" in text  # 09:30 UTC = 14:30 Tashkent


def test_html_is_escaped():
    text = format_article_message(
        _article(translated_title=None, translated_summary=None),
        source_name="<b>Src</b>", category_name="Cat", category_slug="ai",
    )
    assert "<script>" not in text
    assert "&lt;b&gt;Src&lt;/b&gt;" in text


def test_long_message_stays_under_telegram_limit():
    text = format_article_message(
        _article(translated_summary="Juda uzun matn. " * 500),
        source_name="Src", category_name="Cat", category_slug="wars",
    )
    assert len(text) <= MAX_MESSAGE_LEN


def test_critical_flag_adds_marker():
    text = format_article_message(
        _article(), source_name="S", category_name="C", category_slug="wars", critical=True,
    )
    assert "Muhim global yangilik" in text


def test_digest_format():
    items = [(_article(), "Reuters", "ai"), (_article(id=2), "BBC", "wars")]
    text = format_digest(items)
    assert "1." in text and "2." in text
    assert "Reuters" in text and "BBC" in text


def test_empty_digest():
    assert "yo'q" in format_digest([])
