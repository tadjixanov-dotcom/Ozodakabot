from app.news.parsers.cleaner import clean_html, extract_keywords, normalize_title, truncate_text


def test_clean_html_strips_tags():
    raw = "<p>Hello <b>world</b> &amp; friends</p><script>alert(1)</script>"
    cleaned = clean_html(raw)
    assert "<" not in cleaned
    assert "Hello world & friends" in cleaned


def test_clean_html_handles_none():
    assert clean_html(None) == ""
    assert clean_html("") == ""


def test_normalize_title_case_and_punct():
    assert normalize_title("Breaking: NATO Summit!") == normalize_title("breaking nato summit")


def test_extract_keywords_skips_stopwords():
    kws = extract_keywords("The war in the region and the new missile system for defense")
    assert "the" not in kws
    assert "war" in kws
    assert "missile" in kws


def test_truncate_text_cuts_on_sentence():
    text = "First sentence here. Second sentence follows. " * 20
    result = truncate_text(text, max_chars=100)
    assert len(result) <= 101
