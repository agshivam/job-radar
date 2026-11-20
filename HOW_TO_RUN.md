# How to run Job Radar

## 1. Try it with no setup (2 minutes)
```bash
git clone https://github.com/agshivam/job-radar && cd job-radar
pip install -r requirements.txt
PYTHONPATH=src pytest -q            # expect: 9 passed
python scripts/make_demo_data.py    # uses saved sample jobs
streamlit run app/streamlit_app.py
```

## 2. Run on live jobs
```bash
PYTHONPATH=src python -m jobradar
```
Reads the sources in `config/companies.yaml`. Open feeds (`arbeitnow`, `remotive`) work with no company list. To add a company, find its board URL and copy the last part:
`boards.greenhouse.io/<token>`, `jobs.lever.co/<token>`, `jobs.ashbyhq.com/<token>`. Open the URL in a browser first to check it works. A wrong token is skipped with a message.

## 3. Telegram alerts (free, 5 minutes)
1. In Telegram, message **@BotFather**, send `/newbot`, follow the prompts, copy the token.
2. Send any message to your new bot, then open `https://api.telegram.org/bot<TOKEN>/getUpdates` in a browser and copy the number after `"chat":{"id":`.
3. In your GitHub repo: Settings, Secrets and variables, Actions, add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`.
Never paste the token in chat, code or a commit.

## 4. Daily run
`.github/workflows/daily-radar.yml` runs every day at 08:00 India time, runs the tests, collects jobs, alerts, and commits the refreshed data. You can also run it by hand from the Actions tab.

## 5. Deploy the report
share.streamlit.io, New app, pick this repo, main file `app/streamlit_app.py`, Deploy.

## Troubleshooting
- `ModuleNotFoundError: jobradar`: set `PYTHONPATH=src`.
- "skip greenhouse/xyz": the token is wrong or that company does not use that board.
- No alerts: scores under `alert_min_score`, no new jobs, or the secrets are missing.
