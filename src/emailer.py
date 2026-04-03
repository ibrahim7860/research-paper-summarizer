from __future__ import annotations

import logging
import smtplib
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from jinja2 import Environment

from src.fetchers.base import Paper

logger = logging.getLogger(__name__)

TEMPLATE_PATH = Path(__file__).parent.parent / "templates" / "digest.html"


def _prepare_paper_data(paper: Paper, result: dict) -> dict:
    return {
        "title": paper.title,
        "url": paper.url,
        "authors": paper.authors[:5],  # limit for readability
        "source": paper.source,
        "one_liner": result.get("one_liner", result.get("key_takeaway", "")),
        "summary": result.get("summary", ""),
        "key_takeaway": result.get("key_takeaway", ""),
        "novelty": result.get("novelty", ""),
        "new_doors": result.get("new_doors", []),
        "score": result.get("relevance_score", 0),
        "pdf_url": paper.pdf_url,
        "code_url": paper.code_url,
    }


def render_digest(scored_papers: list[tuple[Paper, dict]], threshold: int = 7) -> str:
    """Render HTML email from scored papers."""
    env = Environment(autoescape=True)
    template = env.from_string(TEMPLATE_PATH.read_text())

    must_read = []
    worth_a_look = []

    for paper, result in scored_papers:
        score = result.get("relevance_score", 0)
        if score < threshold:
            continue

        data = _prepare_paper_data(paper, result)
        if score >= 9:
            must_read.append(data)
        else:
            worth_a_look.append(data)

    must_read.sort(key=lambda p: p["score"], reverse=True)
    worth_a_look.sort(key=lambda p: p["score"], reverse=True)

    return template.render(
        date=date.today().strftime("%B %d, %Y"),
        total_papers=len(must_read) + len(worth_a_look),
        must_read=must_read,
        worth_a_look=worth_a_look,
    )


def send_email(
    html_body: str,
    smtp_host: str,
    smtp_port: int,
    sender: str,
    password: str,
    recipients: list[str],
    subject_prefix: str = "[Paper Digest]",
) -> None:
    """Send the digest email via SMTP."""
    subject = f"{subject_prefix} {date.today().strftime('%B %d, %Y')}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)

    # Plain text fallback
    plain = "Your AI Paper Digest is ready. View this email in an HTML-capable client for the full experience."
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    logger.info(f"Sending digest to {recipients}...")
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, recipients, msg.as_string())

    logger.info("Email sent successfully")
