from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.email import EmailOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

with DAG(
    dag_id='query_email_every_2hrs',
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval='0 */2 * * *',  # Every 2 hours
    catchup=False
) as dag:

    def get_postgres_data(**kwargs):
        hook = PostgresHook(postgres_conn_id='my_postgres_conn')  # Set this in Airflow UI
        sql = sql = """
                    select * from athletes where noc = 'India' and discipline='Boxing'
                    """

        results = hook.get_records(sql)

        # Convert query result into HTML table
        html = "<h3>PostgreSQL Query Results</h3><table border='1'>"
        for row in results:
            html += "<tr>" + "".join([f"<td>{str(col)}</td>" for col in row]) + "</tr>"
        html += "</table>"

        # Push result to XCom for email
        kwargs['ti'].xcom_push(key='query_results', value=html)

    query_postgres = PythonOperator(
        task_id='query_postgres',
        python_callable=get_postgres_data,
        provide_context=True
    )

    send_email = EmailOperator(
        task_id='send_email',
        to='sudarshanjn30@gmail.com',  # 👉 Replace with your email
        subject='Automated Postgres Report',
        html_content="{{ ti.xcom_pull(task_ids='query_postgres', key='query_results') }}",
    )

    query_postgres >> send_email
