import json

from mi_agent.ingestion.parsers import make_raw_id, parse_rss, parse_sec_submissions

RSS = b"""<?xml version="1.0"?><rss version="2.0"><channel><title>t</title>
<item><title>Acme  launches &amp; ships</title><link>https://x.com/a?utm_source=rss</link>
<description>&lt;p&gt;Big &lt;b&gt;news&lt;/b&gt; today&lt;/p&gt;</description>
<pubDate>Tue, 28 Oct 2026 14:00:00 GMT</pubDate></item>
<item><title></title><link>https://x.com/b</link></item>
<item><title>No link here</title></item>
<item><title>Second</title><link>https://x.com/c</link><description>d</description></item>
</channel></rss>"""

ATOM = b"""<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"><title>t</title>
<entry><title>Release</title><link href="https://y.com/r"/><updated>2026-10-01T00:00:00Z</updated>
<content type="html">&lt;li&gt;Feature&lt;/li&gt;</content></entry></feed>"""

SEC = json.dumps({"cik": "0001045810", "name": "NVIDIA CORP", "filings": {"recent": {
    "form": ["8-K", "4", "10-Q"], "accessionNumber": ["0001-26-1", "0001-26-2", "0001-26-3"],
    "primaryDocument": ["a.htm", "b.xml", "c.htm"],
    "primaryDocDescription": ["Current report", "", "Quarterly report"],
    "filingDate": ["2026-10-20", "2026-10-19", "2026-08-30"]}}}).encode()


def test_rss_parses_cleans_and_rejects():
    r = parse_rss(RSS, "src", "Acme", 50)
    assert [i.title for i in r.items] == ["Acme launches & ships", "Second"]
    assert r.rejected == 2
    first = r.items[0]
    assert first.body == "Big news today"
    assert first.published_at.year == 2026 and first.published_at.tzinfo is not None


def test_rss_respects_max_items():
    assert len(parse_rss(RSS, "src", "Acme", 1).items) + parse_rss(RSS, "src", "Acme", 1).rejected == 1


def test_atom_supported():
    r = parse_rss(ATOM, "gcp", "Google Cloud", 10)
    assert r.items[0].item_url == "https://y.com/r" and r.items[0].body == "Feature"


def test_sec_filters_forms_and_builds_urls():
    r = parse_sec_submissions(SEC, "sec", "NVIDIA", 10)
    assert [i.title.split(":")[0] for i in r.items] == ["NVIDIA CORP files 8-K", "NVIDIA CORP files 10-Q"]
    assert r.items[0].item_url == "https://www.sec.gov/Archives/edgar/data/1045810/0001261/a.htm"


def test_raw_id_stable_and_content_sensitive():
    a = parse_rss(RSS, "src", "Acme", 50).items[0]
    b = parse_rss(RSS, "src", "Acme", 50).items[0]
    assert a.raw_id == b.raw_id
    assert make_raw_id("src", "https://x.com/a", "different") != a.raw_id
