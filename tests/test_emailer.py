from src.emailer import render_digest
from src.fetchers.base import Paper


def test_render_digest_empty():
    html = render_digest([], threshold=7)
    assert "AI Paper Digest" in html
    assert "0 papers" in html


def test_render_digest_groups_by_score():
    paper_high = Paper(
        source="arxiv", external_id="1", title="High Paper",
        authors=["Author A"], abstract="Abstract", url="https://example.com/1",
    )
    paper_mid = Paper(
        source="arxiv", external_id="2", title="Mid Paper",
        authors=["Author B"], abstract="Abstract", url="https://example.com/2",
    )

    scored = [
        (paper_high, {"relevance_score": 9, "summary": "Great paper", "key_takeaway": "New capability", "one_liner": "Agents that fix their own bugs"}),
        (paper_mid, {"relevance_score": 7, "summary": "Decent paper", "key_takeaway": "Useful insight", "one_liner": "Faster fine-tuning on consumer GPUs"}),
    ]

    html = render_digest(scored, threshold=7)
    assert "High Paper" in html
    assert "Mid Paper" in html
    assert "2 papers" in html
    assert "Agents that fix their own bugs" in html
    assert "Faster fine-tuning on consumer GPUs" in html


def test_render_digest_filters_below_threshold():
    paper = Paper(
        source="arxiv", external_id="1", title="Low Paper",
        authors=["Author"], abstract="Abstract", url="https://example.com",
    )
    scored = [
        (paper, {"relevance_score": 3, "summary": "Not relevant", "key_takeaway": "N/A", "one_liner": "Nothing new here"}),
    ]

    html = render_digest(scored, threshold=7)
    assert "Low Paper" not in html
    assert "0 papers" in html


def test_render_digest_one_liner_falls_back_to_key_takeaway():
    paper = Paper(
        source="arxiv", external_id="1", title="Old Paper",
        authors=["Author"], abstract="Abstract", url="https://example.com",
    )
    scored = [
        (paper, {"relevance_score": 9, "summary": "Great paper", "key_takeaway": "Fallback takeaway"}),
    ]

    html = render_digest(scored, threshold=7)
    assert "Fallback takeaway" in html
