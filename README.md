# docker-work

Cluster distribuido de Apache Airflow 3.2.0 con CeleryExecutor sobre AWS EC2.

## Arquitectura
Internet
│
▼
[Master EC2 — subred pública — 54.91.27.27]
├── Airflow Webserver  :8080
├── Airflow Scheduler
├── RabbitMQ           :5672 / :15672
├── PostgreSQL         :5432
└── Flower             :5555
│  (VPC interna — subred privada)
├── Worker 1   10.0.2.119
├── Worker 2   10.0.2.143
└── Worker 3   10.0.2.165

## Estructura
docker-work/
├── .env                        ← secretos del master (nunca al repo)
├── .env.worker                 ← secretos de los workers (nunca al repo)
├── .gitignore
├── README.md
├── master/
│   └── docker-compose.yml
├── worker/
│   └── docker-compose.yml
└── airflow/
├── dags/
│   └── example_dag.py
├── logs/
└── plugins/

---

## CHECKLIST — LUNES

### Paso 0 · Introducción a Docker
- [ ] Todo el equipo entiende imagen, contenedor y docker-compose
- [ ] `docker run hello-world` corre sin errores en el master

### Paso 1 · Estructura del proyecto
- [ ] Carpetas creadas: `master/`, `worker/`, `airflow/dags/`, `airflow/logs/`, `airflow/plugins/`
- [ ] Archivos base creados: `.gitignore`, `.env`, `.env.worker`, `README.md`

### Paso 2 · Repositorio en GitHub
- [ ] Repo `docker-work` creado en GitHub
- [ ] `.env` y `.env.worker` están en `.gitignore`
- [ ] Primer push al repo sin secretos

### Paso 3 · Instalar Docker en los 4 servidores
- [ ] Docker instalado en el master
- [ ] Docker instalado en worker 1 — 10.0.2.119
- [ ] Docker instalado en worker 2 — 10.0.2.143
- [ ] Docker instalado en worker 3 — 10.0.2.165
- [ ] `docker --version` responde en los 4 servidores
- [ ] `docker compose version` responde en los 4 servidores
- [ ] Usuario `ubuntu` en grupo `docker` en los 4 servidores

### Paso 4 · Deploy keys y clonar repo
- [ ] Deploy key generada y agregada a GitHub en el master
- [ ] Deploy key generada y agregada a GitHub en worker 1
- [ ] Deploy key generada y agregada a GitHub en worker 2
- [ ] Deploy key generada y agregada a GitHub en worker 3
- [ ] Repo clonado en los 4 servidores

### Paso 5 · Distribuir archivos .env
- [ ] FERNET_KEY generado y copiado en `.env` y `.env.worker`
- [ ] SECRET_KEY generado y copiado en `.env` y `.env.worker`
- [ ] `.env` copiado al master
- [ ] `.env.worker` copiado a worker 1 como `.env`
- [ ] `.env.worker` copiado a worker 2 como `.env`
- [ ] `.env.worker` copiado a worker 3 como `.env`

### Paso 6 · Validar conectividad
- [ ] Desde master: `ssh ubuntu@10.0.2.119` funciona
- [ ] Desde master: `ssh ubuntu@10.0.2.143` funciona
- [ ] Desde master: `ssh ubuntu@10.0.2.165` funciona
- [ ] Puertos 5432, 5672, 15672, 8080, 5555 abiertos en security group del master

---

## CHECKLIST — MARTES

### Paso 7 · Generar secretos
```bash
# Ejecutar en el master — genera FERNET_KEY
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Genera SECRET_KEY
python3 -c "import secrets; print(secrets.token_hex(32))"
```
- [ ] FERNET_KEY generado y pegado en `.env` y `.env.worker` (debe ser idéntico)
- [ ] SECRET_KEY generado y pegado en `.env` y `.env.worker` (debe ser idéntico)

### Paso 8 · Levantar el master
```bash
cd ~/docker-work
docker compose -f master/docker-compose.yml up airflow-init
# Esperar que termine, luego:
docker compose -f master/docker-compose.yml up -d
```
- [ ] `airflow-init` termina sin errores
- [ ] Todos los servicios en estado `running` o `healthy`
- [ ] Airflow UI accesible: `http://54.91.27.27:8080`
- [ ] Login con usuario admin funciona
- [ ] RabbitMQ UI accesible: `http://54.91.27.27:15672`
- [ ] Flower accesible: `http://54.91.27.27:5555`

### Paso 9 · Levantar los 3 workers
```bash
# En cada worker:
cd ~/docker-work
docker compose -f worker/docker-compose.yml up -d
```
- [ ] Worker 1 aparece ONLINE en Flower
- [ ] Worker 2 aparece ONLINE en Flower
- [ ] Worker 3 aparece ONLINE en Flower

### Paso 10 · Sincronizar DAGs
```bash
# En cada servidor:
cd ~/docker-work && git pull
```
- [ ] `example_dag.py` visible en Airflow UI
- [ ] git pull ejecutado en master
- [ ] git pull ejecutado en worker 1
- [ ] git pull ejecutado en worker 2
- [ ] git pull ejecutado en worker 3

### Paso 11 · Trigger y verificar distribución
- [ ] DAG `example_dag` ejecutado manualmente desde la UI
- [ ] `verificar_worker` muestra hostname del worker en los logs
- [ ] `verificar_conexion_bd` muestra conexión exitosa a BD de producción
- [ ] El master NO aparece como ejecutor de ninguna tarea
- [ ] Flower muestra las tareas distribuidas entre los 3 workers

### Paso 12 · Demo final
- [ ] Flower con 3 workers ONLINE en pantalla
- [ ] DAG ejecutándose con distribución visible
- [ ] Logs con hostnames distintos
- [ ] PRs mergeados al main
- [ ] README actualizado con estado final

---

## Comandos útiles

```bash
# Ver logs de un servicio
docker compose -f master/docker-compose.yml logs -f airflow-webserver

# Reiniciar un servicio
docker compose -f master/docker-compose.yml restart airflow-scheduler

# Ver estado de todos los contenedores
docker compose -f master/docker-compose.yml ps

# Parar todo
docker compose -f master/docker-compose.yml down

# Sincronizar DAGs en todos los workers desde el master
for IP in 10.0.2.119 10.0.2.143 10.0.2.165; do
  ssh ubuntu@$IP "cd ~/docker-work && git pull"
done
```
