from pathlib import Path


def test_prompt_template_has_placeholders():
    prompt_path = Path(__file__).parent.parent / "prompts" / "scoring_prompt.txt"
    template = prompt_path.read_text()
    assert "{title}" in template
    assert "{abstract}" in template


def test_prompt_template_requests_json():
    prompt_path = Path(__file__).parent.parent / "prompts" / "scoring_prompt.txt"
    template = prompt_path.read_text()
    assert "relevance_score" in template
    assert "summary" in template
    assert "key_takeaway" in template
