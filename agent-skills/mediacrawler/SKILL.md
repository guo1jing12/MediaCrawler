---
name: mediacrawler
description: Run MediaCrawler safely from an AI coding agent. Use this skill to crawl supported media platforms with cookies, multi-account configs, proxy pools, and resume checkpoints.
---

# MediaCrawler Agent Skill

Use this skill when a user asks an agent to collect public data with MediaCrawler, run a crawl, configure accounts, resume a crawl, or inspect saved crawler output.

## Safety Defaults

- Use this project only for learning and research.
- Respect target platform terms, robots.txt, and rate limits.
- Do not run large-scale crawling. Keep `--max_concurrency_num` low unless the user explicitly accepts the risk.
- Do not print cookies, tokens, or proxy passwords in chat, logs, or commit messages.
- Prefer `config/accounts.json` over passing cookies directly on the command line.
- Prefer `--enable_resume_crawl true` so interrupted runs can continue without refetching completed pages.

## Supported Platforms

- `xhs`: Xiaohongshu / Rednote
- `dy`: Douyin
- `ks`: Kuaishou
- `bili`: Bilibili
- `wb`: Weibo
- `tieba`: Baidu Tieba
- `zhihu`: Zhihu

Crawler types:

- `search`: keyword search
- `detail`: specific post/video/note IDs or URLs
- `creator`: creator homepage data

## Before Running

1. Confirm the current directory is the MediaCrawler repository root.
2. Check the current branch and worktree:

```bash
git status --short --branch
```

3. Confirm dependencies are available:

```bash
uv run python main.py --help
```

4. If using browser login instead of API-only cookie mode, install the browser extra:

```bash
uv sync --extra browser
uv run playwright install
```

## Account Config

Create `config/accounts.json` from `config/accounts.example.json`. Example:

```json
{
  "accounts": [
    {
      "name": "xhs_01",
      "platform": "xhs",
      "cookies": "a1=...; web_session=...",
      "proxy": "http://user:pass@127.0.0.1:7890",
      "user_agent": "",
      "enabled": true
    }
  ]
}
```

Never commit `config/accounts.json`.

## Common Commands

Run one platform with multiple accounts, API-only mode, and checkpoint resume:

```bash
uv run python main.py \
  --platform xhs \
  --type search \
  --keywords "编程副业" \
  --enable_multi_account true \
  --account_config_path config/accounts.json \
  --enable_resume_crawl true \
  --disable_playwright true \
  --save_data_option jsonl
```

Run one account with a direct cookie:

```bash
uv run python main.py \
  --platform bili \
  --type search \
  --keywords "AI工具" \
  --lt cookie \
  --cookies "$MEDIACRAWLER_COOKIES" \
  --enable_resume_crawl true \
  --disable_playwright true
```

Use the global proxy pool provider:

```bash
uv run python main.py \
  --platform wb \
  --type search \
  --keywords "人工智能" \
  --enable_ip_proxy true \
  --ip_proxy_pool_count 2 \
  --ip_proxy_provider_name kuaidaili \
  --enable_resume_crawl true
```

## Output Locations

- Data defaults to `data/{platform}/...`
- Checkpoints default to `data/checkpoints/{platform}_{type}_{account}.json`
- Multi-account runs use account names in checkpoint file names.

## Agent Workflow

1. Ask for platform, crawler type, keywords or IDs, desired save format, and whether accounts are already configured.
2. If cookies are missing, tell the user to place them in `config/accounts.json`; do not ask them to paste secrets into chat.
3. Start with a small run, for example `--max_concurrency_num 1` and low `CRAWLER_MAX_NOTES_COUNT` in config.
4. Run the crawler.
5. Summarize saved files and checkpoint path.
6. If a crawl fails, inspect logs and checkpoint state before retrying.

## Known Limits

- API-only mode requires valid cookies for login-required platforms.
- Browser login still requires the optional Playwright extra.
- Platform anti-abuse controls may change; reduce request rate before retrying failures.
