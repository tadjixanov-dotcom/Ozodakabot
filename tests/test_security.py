from app.core.security import parse_callback


def test_valid_callbacks():
    assert parse_callback("fb:12:like") == ("fb", ["12", "like"])
    assert parse_callback("save:5") == ("save", ["5"])
    assert parse_callback("set:mode") == ("set", ["mode"])


def test_invalid_callbacks_rejected():
    assert parse_callback(None) is None
    assert parse_callback("") is None
    assert parse_callback("unknown_prefix:1") is None
    assert parse_callback("fb:1:like:extra:parts:toomany") is None
    assert parse_callback("fb:<script>") is None
    assert parse_callback("x" * 100) is None
