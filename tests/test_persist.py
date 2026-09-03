from geox_app.persist import _slug


def test_slug_sanitizes_name():
    assert _slug("My Design!") == "My_Design"
    assert _slug("  ") == "design"
    assert _slug("_latest") == "design"
    assert _slug("latest") == "design"
