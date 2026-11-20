# Job Radar

Collects data engineering jobs from legal public sources, removes duplicates, scores each against a resume and sends alerts.

**Status:** planned, build starts in week 4. All data is public or synthetic. No employer data is used.

## Plan

1. Collect from public job board APIs and feeds. No LinkedIn or Indeed scraping.
2. Normalize, dedupe with fuzzy matching and extract skills.
3. Score against a resume and send Telegram alerts on a daily schedule.
4. Explore results in a Streamlit app.

## Part of a series

This is one of six portfolio projects. The first one, [patient-360](https://github.com/agshivam/patient-360), is already live with a [running report](https://patient-360.streamlit.app/). Portfolio: https://agshivam.github.io
