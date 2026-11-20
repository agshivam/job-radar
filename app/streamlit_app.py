from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Job Radar", layout="wide")
DATA = Path(__file__).resolve().parent.parent / "app_data" / "jobs.parquet"

st.title("Job Radar")
st.caption("Data engineering jobs from public job APIs, deduplicated and scored against a resume profile. "
           "The sample data here is a saved snapshot; run the pipeline to refresh it.")

if not DATA.exists():
    st.info("No data yet. Run `python scripts/make_demo_data.py` or `python -m jobradar`.")
    st.stop()

df = pd.read_parquet(DATA)
c1, c2, c3 = st.columns(3)
min_score = c1.slider("Minimum score", 0, 100, 40)
remote_only = c2.checkbox("Remote only")
skill = c3.text_input("Must mention skill", placeholder="e.g. Snowflake")

view = df[df["score"] >= min_score]
if remote_only:
    view = view[view["remote"]]
if skill:
    view = view[view["skills"].str.contains(skill, case=False, na=False)]

m1, m2, m3 = st.columns(3)
m1.metric("Jobs shown", len(view))
m2.metric("Best score", f"{view['score'].max():.0f}" if len(view) else "-")
m3.metric("Sources", view["source"].nunique())

st.dataframe(view[["score", "title", "company", "location", "remote", "skills", "posted_at", "url"]],
             hide_index=True, width="stretch", column_config={"url": st.column_config.LinkColumn("Apply")})

st.subheader("Skills asked for most")
counts = view["skills"].str.split(", ").explode().value_counts().head(12)
st.bar_chart(counts)

with st.expander("How the score works"):
    st.markdown("70% skill coverage (weighted), 15% seniority fit, 10% location fit, 5% freshness. "
                "Duplicates across sources are merged with fuzzy title matching.")
