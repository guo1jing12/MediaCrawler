---
description: Run MediaCrawler with accounts, proxies, and resume checkpoints
argument-hint: "[platform] [crawler_type] [keywords_or_ids]"
allowed-tools: Bash, Read, LS, Grep
---

# MediaCrawler Crawl

You are operating inside the MediaCrawler repository.

Task input: `$ARGUMENTS`

Follow this workflow:

1. Inspect the repository state with `git status --short --branch`.
2. Read `agent-skills/mediacrawler/SKILL.md` and follow its safety defaults.
3. Confirm required crawl parameters from the user if they are missing:
   - platform: `xhs`, `dy`, `ks`, `bili`, `wb`, `tieba`, or `zhihu`
   - crawler type: `search`, `detail`, or `creator`
   - keywords, specified IDs, or creator IDs
   - save format
   - whether `config/accounts.json` is configured
4. Do not ask the user to paste cookies into chat. Use `config/accounts.json` or environment variables.
5. Prefer API-only multi-account resume mode:

```bash
uv run python main.py \
  --platform <platform> \
  --type <search|detail|creator> \
  --keywords "<keywords>" \
  --enable_multi_account true \
  --account_config_path config/accounts.json \
  --enable_resume_crawl true \
  --disable_playwright true \
  --save_data_option jsonl
```

6. If browser login is required, install the optional browser extra before running:

```bash
uv sync --extra browser
uv run playwright install
```

7. After the run, report:
   - command shape without secrets
   - output directory
   - checkpoint file
   - any failures and the safest retry plan
