from mi_agent.ids import content_hash, event_id, normalize_title, normalize_url


def test_normalize_url_strips_tracking_fragment_and_slash():
    a = normalize_url("HTTPS://Example.com/Post/?utm_source=x&b=2&a=1#top")
    b = normalize_url("https://example.com/Post?a=1&b=2")
    assert a == b


def test_event_id_is_stable_across_cosmetic_changes():
    e1 = event_id("Databricks", "https://x.com/a/?utm_campaign=z", "New  Feature ")
    e2 = event_id("databricks", "https://x.com/a", "new feature")
    assert e1 == e2 and e1.startswith("evt_") and len(e1) == 20


def test_event_id_differs_for_different_items():
    assert event_id("A", "https://x.com/1", "t") != event_id("A", "https://x.com/2", "t")


def test_content_hash_ignores_whitespace():
    assert content_hash("a  b\n") == content_hash("a b")
    assert normalize_title("  Hi   There ") == "hi there"
