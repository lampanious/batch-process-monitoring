"""
Batch Jobs Airflow DAG

This DAG orchestrates the execution of batch jobs with dependencies,
monitoring, and error handling.

Save this file to your Airflow DAGs directory.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import BranchPythonOperator
import sqlite3
import requests
import os
import sys

# Default arguments for the DAG
default_args = {
    'owner': 'data_team',
    'depends_on_past': False,
    'start_date': datetime(2025, 5, 1),
    'email': ['alerts@yourdomain.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Create DAG
dag = DAG(
    'batch_job_processing',
    default_args=default_args,
    description='Batch job processing workflow',
    schedule_interval='0 1 * * *',  # Run daily at 1 AM
    catchup=False,
    max_active_runs=1
)

# Helper function to register job in the monitoring system
def register_job_start(job_name):
    """Register the start of a batch job in the monitoring system"""
    import sqlite3
    import datetime
    
    db_path = "/path/to/storage/job_metrics.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    start_time = datetime.datetime.now().isoformat()
    
    cursor.execute(
        'INSERT INTO jobs (name, start, status) VALUES (?, ?, ?)',
        (job_name, start_time, 'running')
    )
    
    job_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return job_id

def register_job_end(job_id, status="completed"):
    """Register the end of a batch job in the monitoring system"""
    import sqlite3
    import datetime
    
    db_path = "/path/to/storage/job_metrics.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    end_time = datetime.datetime.now().isoformat()
    
    # Get job details
    cursor.execute('SELECT name, start FROM jobs WHERE id = ?', (job_id,))
    result = cursor.fetchone()
    
    if not result:
        print(f"Job with ID {job_id} not found")
        conn.close()
        return
    
    job_name, start_time_str = result
    
    # Calculate duration
    start_time = datetime.datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
    end_time_dt = datetime.datetime.fromisoformat(end_time.replace('Z', '+00:00'))
    duration_seconds = (end_time_dt - start_time).total_seconds()
    
    # Update job record
    cursor.execute(
        'UPDATE jobs SET end = ?, duration = ?, status = ? WHERE id = ?',
        (end_time, duration_seconds, status, job_id)
    )
    
    conn.commit()
    conn.close()

# Wrapper function for tasks to enable monitoring
def monitored_task(job_name, task_function, **kwargs):
    """Wrapper function to monitor task execution"""
    job_id = register_job_start(job_name)
    try:
        result = task_function(**kwargs)
        register_job_end(job_id, "completed")
        return result
    except Exception as e:
        register_job_end(job_id, "failed")
        raise

# Define the actual task functions
def data_ingestion_task(**kwargs):
    """Data ingestion task implementation"""
    print("Starting data ingestion...")
    # Your data ingestion code here
    # Example:
    # import pandas as pd
    # data = pd.read_csv('/path/to/source.csv')
    # data.to_sql('raw_data', engine)
    print("Data ingestion completed")
    
def data_transformation_task(**kwargs):
    """Data transformation task implementation"""
    print("Starting data transformation...")
    # Your data transformation code here
    # Example:
    # import pandas as pd
    # from sklearn.preprocessing import StandardScaler
    # data = pd.read_sql('SELECT * FROM raw_data', engine)
    # scaler = StandardScaler()
    # data_scaled = scaler.fit_transform(data)
    # pd.DataFrame(data_scaled).to_sql('transformed_data', engine)
    print("Data transformation completed")
    
def ml_training_task(**kwargs):
    """Machine learning training task implementation"""
    print("Starting ML model training...")
    # Your ML training code here
    # Example:
    # import pandas as pd
    # from sklearn.ensemble import RandomForestClassifier
    # data = pd.read_sql('SELECT * FROM transformed_data', engine)
    # X = data.drop('target', axis=1)
    # y = data['target']
    # model = RandomForestClassifier()
    # model.fit(X, y)
    # import joblib
    # joblib.dump(model, '/path/to/model.pkl')
    print("ML model training completed")
    
def report_generation_task(**kwargs):
    """Report generation task implementation"""
    print("Starting report generation...")
    # Your report generation code here
    # Example:
    # import pandas as pd
    # import matplotlib.pyplot as plt
    # data = pd.read_sql('SELECT * FROM metrics', engine)
    # plt.figure(figsize=(10, 6))
    # data.plot(kind='bar')
    # plt.savefig('/path/to/report.png')
    print("Report generation completed")
    
def data_cleanup_task(**kwargs):
    """Data cleanup task implementation"""
    print("Starting data cleanup...")
    # Your data cleanup code here
    # Example:
    # import sqlite3
    # conn = sqlite3.connect('/path/to/database.db')
    # cursor = conn.cursor()
    # cursor.execute('DELETE FROM temp_data WHERE created_at < date("now", "-30 day")')
    # conn.commit()
    # conn.close()
    print("Data cleanup completed")

def check_data_quality(**kwargs):
    """Check if data quality is sufficient to proceed with ML training"""
    # Your data quality check code here
    # Example:
    # import pandas as pd
    # data = pd.read_sql('SELECT * FROM transformed_data', engine)
    # missing_values = data.isnull().sum().sum()
    # if missing_values > threshold:
    #     return 'skip_ml_training'
    # else:
    #     return 'ml_training'
    return 'ml_training'  # Default to proceeding with ML training

# Create the tasks
start = DummyOperator(
    task_id='start',
    dag=dag,
)

data_ingestion = PythonOperator(
    task_id='data_ingestion',
    python_callable=lambda **kwargs: monitored_task('data_ingestion', data_ingestion_task, **kwargs),
    provide_context=True,
    dag=dag,
)

data_transformation = PythonOperator(
    task_id='data_transformation',
    python_callable=lambda **kwargs: monitored_task('data_transformation', data_transformation_task, **kwargs),
    provide_context=True,
    dag=dag,
)

data_quality_check = BranchPythonOperator(
    task_id='data_quality_check',
    python_callable=check_data_quality,
    provide_context=True,
    dag=dag,
)

ml_training = PythonOperator(
    task_id='ml_training',
    python_callable=lambda **kwargs: monitored_task('ml_training', ml_training_task, **kwargs),
    provide_context=True,
    dag=dag,
)

skip_ml_training = DummyOperator(
    task_id='skip_ml_training',
    dag=dag,
)

report_generation = PythonOperator(
    task_id='report_generation',
    python_callable=lambda **kwargs: monitored_task('report_generation', report_generation_task, **kwargs),
    provide_context=True,
    dag=dag,
)

data_cleanup = PythonOperator(
    task_id='data_cleanup',
    python_callable=lambda **kwargs: monitored_task('data_cleanup', data_cleanup_task, **kwargs),
    provide_context=True,
    dag=dag,
)

end = DummyOperator(
    task_id='end',
    dag=dag,
    trigger_rule='none_failed',
)

# Define task dependencies
start >> data_ingestion >> data_transformation >> data_quality_check
data_quality_check >> [ml_training, skip_ml_training]
ml_training >> report_generation
skip_ml_training >> report_generation
report_generation >> data_cleanup >> end