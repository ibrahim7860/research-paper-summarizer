from src.fetchers.base import Paper


def test_paper_normalized_title():
    paper = Paper(
        source="test",
        external_id="123",
        title="  A New Method  for  AI Agents  ",
        authors=["Test Author"],
        abstract="Abstract here",
        url="https://example.com",
    )
    assert paper.normalized_title == "a new method for ai agents"


def test_paper_normalized_title_consistent():
    p1 = Paper(
        source="arxiv",
        external_id="1",
        title="LLM Agents: A Survey",
        authors=[],
        abstract="",
        url="",
    )
    p2 = Paper(
        source="semantic_scholar",
        external_id="2",
        title="llm agents:  a survey",
        authors=[],
        abstract="",
        url="",
    )
    assert p1.normalized_title == p2.normalized_title
