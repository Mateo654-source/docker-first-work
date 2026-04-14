from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.hooks.base import BaseHook
import socket

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

def verificar_worker(**kwargs):
    hostname = socket.gethostname()
    print(f"Tarea ejecutada en: {hostname}")
    print(f"Run ID: {kwargs['run_id']}")
    return hostname

def verificar_conexion_bd(**kwargs):
    conn = BaseHook.get_connection("bd_produccion")
    print(f"Conectando a: {conn.host}")
    print(f"Base de datos: {conn.schema}")
    print(f"Usuario: {conn.login}")
    print("Conexion verificada correctamente")

with DAG(
    dag_id="example_dag",
    description="Verifica workers y conexion a BD de produccion",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["test"],
) as dag:

    tarea_worker = PythonOperator(
        task_id="verificar_worker",
        python_callable=verificar_worker,
    )

    tarea_bd = PythonOperator(
        task_id="verificar_conexion_bd",
        python_callable=verificar_conexion_bd,
    )

    tarea_worker >> tarea_bd
