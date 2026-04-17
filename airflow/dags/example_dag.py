from airflow.decorators import dag, task
from datetime import datetime

# ─────────────────────────────────────────────
# DAG
# ─────────────────────────────────────────────

@dag(
    dag_id="hola_mundo_decorators",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["simple", "test"]
)
def hola_mundo_dag():

    # ─────────────────────────────────────────
    # TASK
    # ─────────────────────────────────────────
    
    @task
    def hola_mundo():
        print("👋 Hola mundo desde Airflow con decoradores!")

    hola_mundo()


# Instancia del DAG
dag = hola_mundo_dag()
