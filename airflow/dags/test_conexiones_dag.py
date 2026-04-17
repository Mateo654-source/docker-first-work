"""
DAG: test_conexiones
Propósito: Verificar que todas las conexiones del stack funcionan correctamente.
Trigger: Manual desde la UI
Queue: la_cola
"""

from datetime import datetime
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator

# ─────────────────────────────────────────────
# DEFAULT ARGS
# ─────────────────────────────────────────────
default_args = {
    "owner": "admin",
    "retries": 0,
    "queue": "default",
}

# ─────────────────────────────────────────────
# TASKS
# ─────────────────────────────────────────────

def test_worker_identity(**ctx):
    """Muestra en qué worker físico se ejecutó la tarea."""
    import socket
    import os
    hostname = socket.gethostname()
    worker_ip = socket.gethostbyname(hostname)
    print(f"✅ Worker hostname : {hostname}")
    print(f"✅ Worker IP       : {worker_ip}")
    print(f"✅ PID             : {os.getpid()}")
    return {"hostname": hostname, "ip": worker_ip}


def test_postgres_interno(**ctx):
    """Verifica conexión a la Postgres interna de Airflow (10.0.1.182:5432)."""
    import psycopg2
    conn = psycopg2.connect(
        host="10.0.1.182",
        port=5432,
        dbname="airflow",
        user="airflow",
        password="airflow_secure_pass",
        connect_timeout=5,
    )
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()[0]
    cur.close()
    conn.close()
    print(f"✅ Postgres interno OK: {version}")
    return version


def test_postgres_produccion(**ctx):
    """Verifica conexión a la DB de producción externa (51.222.142.204:5432)."""
    from airflow.hooks.base import BaseHook
    conn_obj = BaseHook.get_connection("BD_PRODUCCION")
    import psycopg2
    conn = psycopg2.connect(
        host=conn_obj.host,
        port=conn_obj.port or 5432,
        dbname=conn_obj.schema,
        user=conn_obj.login,
        password=conn_obj.password,
        connect_timeout=5,
    )
    cur = conn.cursor()
    cur.execute("SELECT current_database(), current_user;")
    db, user = cur.fetchone()
    cur.close()
    conn.close()
    print(f"✅ Postgres producción OK — DB: {db} | User: {user}")
    return {"db": db, "user": user}


def test_rabbitmq(**ctx):
    """Verifica que el worker puede alcanzar RabbitMQ en 10.0.1.182:5672."""
    import socket
    host, port = "10.0.1.182", 5672
    s = socket.create_connection((host, port), timeout=5)
    s.close()
    print(f"✅ RabbitMQ alcanzable en {host}:{port}")
    return True


def test_celery_result_backend(**ctx):
    """Verifica que el result backend de Celery (Postgres local) es escribible."""
    import psycopg2
    conn = psycopg2.connect(
        host="10.0.1.182",
        port=5432,
        dbname="airflow",
        user="airflow",
        password="airflow_secure_pass",
        connect_timeout=5,
    )
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM celery_taskmeta;")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    print(f"✅ Celery result backend OK — registros en celery_taskmeta: {count}")
    return count


def test_airflow_api(**ctx):
    """Verifica que la API de Airflow responde desde el worker."""
    import urllib.request
    url = "http://10.0.1.182:8080/api/v2/version"
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            import json
            data = json.loads(r.read())
            print(f"✅ Airflow API OK — versión: {data.get('version', 'desconocida')}")
            return data
    except Exception as e:
        # 401 es esperado sin auth — pero significa que la API responde
        if "401" in str(e) or "Unauthorized" in str(e):
            print("✅ Airflow API OK — responde (401 esperado sin token)")
            return "API responde con 401 (normal)"
        raise


def resumen(**ctx):
    """Imprime resumen final de todas las pruebas."""
    ti = ctx["ti"]
    resultados = {
        "worker_identity"      : ti.xcom_pull(task_ids="test_worker_identity"),
        "postgres_interno"     : ti.xcom_pull(task_ids="test_postgres_interno"),
        "postgres_produccion"  : ti.xcom_pull(task_ids="test_postgres_produccion"),
        "rabbitmq"             : ti.xcom_pull(task_ids="test_rabbitmq"),
        "celery_result_backend": ti.xcom_pull(task_ids="test_celery_result_backend"),
        "airflow_api"          : ti.xcom_pull(task_ids="test_airflow_api"),
    }
    print("\n" + "="*50)
    print("        RESUMEN DE DIAGNÓSTICO")
    print("="*50)
    for nombre, resultado in resultados.items():
        estado = "✅ OK" if resultado is not None else "❌ FALLÓ"
        print(f"  {estado}  →  {nombre}")
    print("="*50 + "\n")


# ─────────────────────────────────────────────
# DAG DEFINITION
# ─────────────────────────────────────────────
with DAG(
    dag_id="test_conexiones",
    description="DAG de diagnóstico — testea todas las conexiones del stack",
    start_date=datetime(2025, 1, 1),
    schedule=None,           # Solo trigger manual
    catchup=False,
    tags=["diagnostico", "test"],
    default_args=default_args,
) as dag:

    t_worker = PythonOperator(
        task_id="test_worker_identity",
        python_callable=test_worker_identity,
    )

    t_pg_interno = PythonOperator(
        task_id="test_postgres_interno",
        python_callable=test_postgres_interno,
    )

    t_pg_prod = PythonOperator(
        task_id="test_postgres_produccion",
        python_callable=test_postgres_produccion,
    )

    t_rabbit = PythonOperator(
        task_id="test_rabbitmq",
        python_callable=test_rabbitmq,
    )

    t_celery_backend = PythonOperator(
        task_id="test_celery_result_backend",
        python_callable=test_celery_result_backend,
    )

    t_api = PythonOperator(
        task_id="test_airflow_api",
        python_callable=test_airflow_api,
    )

    t_resumen = PythonOperator(
        task_id="resumen",
        python_callable=resumen,
    )

    # Todas las pruebas en paralelo → resumen al final
    [t_worker, t_pg_interno, t_pg_prod, t_rabbit, t_celery_backend, t_api] >> t_resumen
