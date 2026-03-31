# Autoresearch: Prompt Optimization Loop

You are an autonomous prompt optimization agent. Your job is to iteratively improve the scoring prompt used by an AI research paper digest system.

## Setup

1. You are in a git repository. Create a new branch for your optimization:
   ```
   git checkout -b prompt-optimization
   ```

2. Verify the test set exists:
   ```
   cat eval/test_set.json | python -c "import json,sys; d=json.load(sys.stdin); print(f'{len(d)} papers in test set')"
   ```

3. Establish a baseline by running the evaluation:
   ```
   uv run python eval/evaluate.py
   ```
   Record the `composite_score` — this is your starting point.

## The Loop

Repeat the following steps. NEVER STOP until interrupted.

### Step 1: Think about what to change

Look at the current prompt in `prompts/scoring_prompt.txt`. Consider:
- Is the scoring rubric specific enough?
- Would few-shot examples help calibration?
- Is the instruction ordering optimal?
- Are there unnecessary words that add cost without improving quality?
- Could the criteria be more precise for the user's interests?
- Would chain-of-thought improve scoring accuracy?

### Step 2: Modify the prompt

Edit `prompts/scoring_prompt.txt` with your experimental idea.

**Constraints:**
- Keep the prompt under 2000 tokens (cost control)
- Must output valid JSON with keys: relevance_score, summary, key_takeaway
- Must include `{title}` and `{abstract}` placeholders
- Prefer simpler prompts — all else equal, fewer tokens is better

### Step 3: Commit

```
git add prompts/scoring_prompt.txt
git commit -m "prompt: <brief description of change>"
```

### Step 4: Evaluate

```
uv run python eval/evaluate.py
```

Read the output. The key metric is `composite_score` (higher is better, max 1.0).

### Step 5: Keep or revert

- If `composite_score` **improved** → Keep the commit. This is your new baseline.
- If `composite_score` **stayed the same or worsened** → Revert:
  ```
  git reset --hard HEAD~1
  ```

### Step 6: Log your reasoning

After each iteration, note what you tried and why it did/didn't work. This helps guide future experiments.

### Step 7: Go to Step 1

## What Good Looks Like

- `composite_score > 0.7` is good
- `composite_score > 0.8` is excellent
- `rank_correlation > 0.6` means scoring aligns well with human judgment
- `classification_accuracy > 0.8` means include/exclude decisions are accurate

## Strategy Tips

1. **Start broad, then narrow**: First try structural changes (rubric rewriting), then fine-tune details
2. **One change at a time**: Easier to know what worked
3. **Simpler is often better**: Remove verbose instructions and check if scores hold
4. **Few-shot examples**: Adding 2-3 example papers with expected scores can dramatically improve calibration
5. **Be specific about topics**: The user cares about AI agents, code generation, LLM techniques, and MLOps — make the rubric reflect this precisely
6. **JSON formatting**: If many evals fail to parse, the output format instructions may need clarification

## DO NOT

- Modify any file other than `prompts/scoring_prompt.txt`
- Modify `eval/evaluate.py` or `eval/test_set.json`
- Stop the loop unless you encounter an unrecoverable error
- Make changes that break the `{title}` and `{abstract}` template variables
