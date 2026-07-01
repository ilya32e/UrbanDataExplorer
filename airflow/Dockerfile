# Image Airflow enrichie des dependances du pipeline Urban Data Explorer.
#
# On part de l'image officielle et on installe les libs metier AVEC le fichier de
# contraintes officiel d'Airflow : cela garantit que SQLAlchemy (1.4), pandas, etc.
# restent aux versions compatibles avec Airflow et n'ecrasent pas le core.
FROM apache/airflow:2.10.4

ARG AIRFLOW_VERSION=2.10.4
ARG PYTHON_VERSION=3.12
ARG CONSTRAINTS_URL=https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt

COPY airflow/requirements.txt /requirements.txt

RUN pip install --no-cache-dir -r /requirements.txt --constraint "${CONSTRAINTS_URL}"
