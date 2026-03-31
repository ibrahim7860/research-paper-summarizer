# Paper Digest

A daily AI research paper digest pipeline. It fetches recent papers from arXiv, Semantic Scholar, and Papers with Code, scores them for practical relevance using Claude, and emails a curated digest.

## How It Works

1. **Fetch** — Pulls recent papers from three sources (arXiv, Semantic Scholar, Papers with Code)
2. **Deduplicate** — Filters out previously seen papers using a local SQLite database and normalized title matching
3. **Score** — Sends each paper's title and abstract to Claude with a scoring prompt that returns a relevance score, summary, and key takeaways
4. **Filter** — Keeps only papers above a configurable relevance threshold
5. **Email** — Renders a digest using an HTML template and sends it via SMTP

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- An [Anthropic API key](https://console.anthropic.com/)
- A Gmail app password (optional, for sending email digests)

## Setup

1. Clone the repository:

   ```sh
   git clone <repo-url>
   cd paper-digest
   ```

2. Install dependencies:

   ```sh
   uv sync
   ```

3. Copy the example configuration files:

   ```sh
   cp config.example.yaml config.yaml
   cp .env.example .env
   ```

4. Edit `.env` and set your API keys:

   ```
   ANTHROPIC_API_KEY=sk-ant-...
   SMTP_PASSWORD=your-gmail-app-password
   SEMANTIC_SCHOLAR_API_KEY=optional-for-higher-rate-limits
   ```

5. Edit `config.yaml` to configure paper sources, filtering, and email settings (see [Configuration](#configuration) below).

## Usage

Run the digest pipeline:

```sh
uv run paper-digest
```

Run tests:

```sh
uv run pytest
```

## Configuration

All settings live in `config.yaml`. Key sections:

### Sources

```yaml
sources:
  arxiv:
    enabled: true
    categories: ["cs.AI", "cs.LG", "cs.CL", "cs.SE", "cs.MA"]
    max_results_per_category: 30

  semantic_scholar:
    enabled: true
    keywords: ["AI agents", "LLM applications", "code generation", "RAG retrieval augmented generation"]

  papers_with_code:
    enabled: true
```

### Filtering

```yaml
filtering:
  relevance_threshold: 7    # Minimum score (1-10) to include a paper
  max_papers_per_digest: 20  # Cap on papers per email
```

### Email

```yaml
email:
  smtp_host: smtp.gmail.com
  smtp_port: 587
  sender: your-email@gmail.com
  recipients:
    - your-email@gmail.com
  subject_prefix: "[Paper Digest]"
```

### Storage & Schedule

```yaml
storage:
  db_path: "~/.paper-digest/papers.db"  # SQLite DB for tracking seen papers

schedule:
  days_back: 1  # How many days back to fetch
```

## Automated Daily Digest (GitHub Actions)

The repository includes a GitHub Actions workflow that runs the digest pipeline daily at 8 AM CT.

To enable it:

1. Push the repository to GitHub.

2. Add the following secrets in **Settings → Secrets and variables → Actions**:

   | Secret | Required | Description |
   |--------|----------|-------------|
   | `ANTHROPIC_API_KEY` | Yes | Your Anthropic API key |
   | `SMTP_PASSWORD` | Yes | Gmail app password for sending the digest |
   | `EMAIL_ADDRESS` | Yes | Your email address (used as sender and recipient) |
   | `SEMANTIC_SCHOLAR_API_KEY` | No | For higher Semantic Scholar rate limits |

3. The workflow uses `config.example.yaml` as a base and substitutes your email address at runtime. Edit `config.example.yaml` to customize sources, filtering, and other settings.

4. The seen-paper database is cached between runs so you won't receive duplicate papers.

You can also trigger a run manually from the **Actions** tab using the "Run workflow" button.

## Prompt Optimization (Autoresearch)

The project includes an evaluation system for iteratively improving the scoring prompt.

1. **Create a test set** of human-labeled papers:

   ```sh
   uv run python eval/create_test_set.py
   ```

2. **Evaluate** the current prompt against the test set:

   ```sh
   uv run python eval/evaluate.py
   ```

   This computes a composite score (60% rank correlation + 40% classification accuracy).

3. **Run the optimization loop** by following the instructions in `eval/program.md` — modify the prompt in `prompts/scoring_prompt.txt`, evaluate, keep improvements, revert regressions.

## Project Structure

```
├── .github/
│   └── workflows/
│       └── daily-digest.yml  # GitHub Actions daily cron
├── src/
│   ├── main.py              # Pipeline orchestration
│   ├── config.py            # YAML + env config loading
│   ├── summarizer.py        # Claude-based paper scoring
│   ├── emailer.py           # Digest rendering and SMTP sending
│   ├── storage.py           # SQLite seen-paper tracking
│   └── fetchers/
│       ├── base.py          # Paper dataclass and fetcher interface
│       ├── arxiv_fetcher.py
│       ├── semantic_scholar.py
│       └── papers_with_code.py
├── prompts/
│   └── scoring_prompt.txt   # Claude scoring prompt (editable)
├── templates/
│   └── digest.html          # Jinja2 email template
├── eval/
│   ├── evaluate.py          # Evaluation harness
│   ├── create_test_set.py   # Test set builder
│   └── program.md           # Autoresearch loop instructions
├── tests/
├── config.example.yaml
├── .env.example
└── pyproject.toml
```
