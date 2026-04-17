from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime


def hola_mundo():
    print("Hola mundo desde Airflow 🚀")


with DAG(
    dag_id="hola_mundo",
    start_date=datetime(2024, 1, 1),
    schedule=None,  # manual
    catchup=False,
    tags=["test"],
) as dag:

    tarea_hola = PythonOperator(
        task_id="imprimir_hola_mundo",
        python_callable=hola_mundo,
    )

    tarea_hola
