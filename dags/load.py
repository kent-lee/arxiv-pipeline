from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
import feedparser
import pandas as pd
import s3fs
import psycopg2

source_path = 'http://export.arxiv.org/rss/cs'
s3_path = 's3://arxiv-pipeline/arxiv.csv'
rds_table = 'publications'

default_args = {
    'owner': 'kent',
    'start_date': datetime(2019, 6, 30),
    'depends_on_past':False,
    'retries': 1,
    'retry_delay': timedelta(seconds=15)
}

def source_to_s3(source, destination):
    columns = ['title', 'link', 'summary']
    s3 = s3fs.S3FileSystem()
    # get old feed from s3 if exists, else create empty df
    if s3.exists(destination):
        old_feed = pd.read_csv(destination)
    else:
        old_feed = pd.DataFrame(columns=columns)
    # get new feed from source
    data = feedparser.parse(source)
    df = pd.DataFrame.from_dict(data['entries'])
    new_feed = df[columns]
    # find rows in new feed that are not in old feed (i.e. find new uploads)
    merged = old_feed.merge(new_feed, how='outer', indicator=True)
    new_uploads = merged[merged['_merge'] == 'right_only'].drop('_merge', axis=1)
    if new_uploads.empty:
        return
    # append new uploads to old feed then save to csv
    df = old_feed.append(new_uploads, ignore_index=True)
    bytes_to_write = df.to_csv(None, index=False).encode()
    with s3.open(destination, 'wb') as f:
        f.write(bytes_to_write)

def s3_to_redshift(source, destination):
    con = psycopg2.connect(
        dbname='***',
        host='arxiv-cluster.***.ca-central-1.redshift.amazonaws.com',
        port='5439',
        user='***',
        password='***'
    )
    cursor = con.cursor()
    create_staging_table = (
        f"create temp table stage (like {destination}); "
        "copy stage "
        f"from '{source}' "
        "credentials 'aws_iam_role=***' "
        "csv; "
    )
    cursor.execute(create_staging_table)
    update_target_table = (
        "begin transaction; "
        f"delete from {destination} "
        "using stage "
        f"where {destination}.link = stage.link; "
        f"insert into {destination} "
        "select * from stage; "
        "end transaction; "
    )
    cursor.execute(update_target_table)
    con.close()

dag = DAG(
    'arxiv_pipeline',
    default_args=default_args,
    schedule_interval=timedelta(minutes=5),
    catchup=False
)

t1 = PythonOperator(
    task_id='source_to_s3',
    python_callable=source_to_s3,
    op_kwargs={'source': source_path, 'destination': s3_path},
    dag=dag
)

t2 = PythonOperator(
    task_id='s3_to_redshift',
    python_callable=s3_to_redshift,
    op_kwargs={'source': s3_path, 'destination': rds_table},
    dag=dag
)

t1 >> t2