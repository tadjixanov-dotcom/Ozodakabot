from app.news.deduplication.dedup import content_hash, find_similar_title, titles_similar


def test_content_hash_ignores_case_and_punct():
    a = content_hash("Russia launches new offensive in the East!")
    b = content_hash("russia launches new offensive in the east")
    assert a == b


def test_content_hash_differs_for_different_news():
    assert content_hash("AI chip export rules") != content_hash("Earthquake hits Japan")


def test_titles_similar_true_for_variants():
    assert titles_similar(
        "US announces new sanctions against Iran oil exports",
        "US announces new sanctions on Iran oil exports",
    )


def test_titles_similar_false_for_unrelated():
    assert not titles_similar(
        "Robot dog learns to climb stairs",
        "Central bank raises interest rates again",
    )


def test_find_similar_title_returns_id():
    candidates = [(1, "OpenAI releases new model"), (2, "Flood warning issued in Tashkent region")]
    assert find_similar_title("Flood warning issued in Tashkent", candidates) == 2
    assert find_similar_title("Completely unrelated title about sports", candidates) is None
