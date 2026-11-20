"""Find skills in a job description. Each skill has aliases and a weight (how much it matters for a data engineer)."""
import re

# skill: (weight, aliases). Weight 3 = core, 2 = common, 1 = nice to have.
SKILLS = {
    "Snowflake": (3, ["snowflake"]), "dbt": (3, ["dbt", "data build tool"]), "SQL": (3, ["sql"]),
    "Python": (3, ["python"]), "Airflow": (2, ["airflow"]), "Fivetran": (2, ["fivetran"]), "Airbyte": (1, ["airbyte"]),
    "AWS": (2, ["aws", "amazon web services", "s3", "redshift", "lambda"]), "Azure": (2, ["azure", "adls"]),
    "GCP": (2, ["gcp", "google cloud", "bigquery"]), "Databricks": (2, ["databricks", "delta lake"]),
    "Spark": (2, ["spark", "pyspark"]), "Kafka": (1, ["kafka"]), "Terraform": (1, ["terraform"]),
    "Docker": (1, ["docker"]), "Kubernetes": (1, ["kubernetes", "k8s"]), "Tableau": (1, ["tableau"]),
    "Power BI": (1, ["power bi", "powerbi"]), "Looker": (1, ["looker"]), "MongoDB": (1, ["mongodb"]),
    "Dagster": (1, ["dagster"]), "ETL/ELT": (2, ["etl", "elt", "data pipeline", "data pipelines"]),
    "Data modeling": (2, ["data model", "data modeling", "data modelling", "dimensional model", "star schema"]),
    "CI/CD": (1, ["ci/cd", "cicd", "github actions", "gitlab ci"]), "HIPAA": (1, ["hipaa"]),
    "Healthcare": (1, ["healthcare", "ehr", "emr", "epic", "fhir"]), "Data quality": (1, ["data quality", "data testing", "great expectations"]),
}
WEIGHTS = {k: v[0] for k, v in SKILLS.items()}
_PATTERNS = {k: re.compile(r"(?<![A-Za-z0-9])(" + "|".join(re.escape(a) for a in v[1]) + r")(?![A-Za-z0-9])", re.I)
             for k, v in SKILLS.items()}


def extract_skills(text: str) -> list[str]:
    return [k for k, p in _PATTERNS.items() if p.search(text or "")]
