#!/usr/bin/env python3
"""
Batch Job Monitoring Script

This script collects and formats batch job data for monitoring in Grafana.
It tracks job names, start times, and durations.

The data is exported in a format compatible with Prometheus/InfluxDB for Grafana visualization.
"""

import os
import time
import datetime
import json
import logging
import argparse
from typing import Dict, List, Any, Optional, Tuple
import sqlite3
import pandas as pd
import requests
from prometheus_client import start_http_server, Gauge, Counter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("batch_job_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("batch_job_monitor")

# Define metrics
JOB_DURATION = Gauge('batch_job_duration_seconds', 'Duration of batch job', ['job_name', 'status'])
JOB_START_TIME = Gauge('batch_job_start_time', 'Start time of batch job as unix timestamp', ['job_name'])
JOB_COUNT = Counter('batch_job_count_total', 'Total count of batch jobs', ['job_name', 'status'])

class BatchJobMonitor:
    """Monitor for batch jobs"""
    
    def __init__(self, db_path: str = "job_metrics.db"):
        """Initialize the batch job monitor
        
        Args:
            db_path: Path to SQLite database for storing job metrics
        """
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self) -> None:
        """Initialize the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create table for job metrics if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_name TEXT NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            duration_seconds REAL,
            status TEXT DEFAULT 'running',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")
    
    def register_job_start(self, job_name: str) -> int:
        """Register the start of a batch job
        
        Args:
            job_name: Name of the batch job
            
        Returns:
            job_id: ID of the registered job
        """
        start_time = datetime.datetime.now()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT INTO job_metrics (job_name, start_time) VALUES (?, ?)',
            (job_name, start_time)
        )
        
        job_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Update Prometheus metrics
        unix_start_time = time.mktime(start_time.timetuple())
        JOB_START_TIME.labels(job_name=job_name).set(unix_start_time)
        
        logger.info(f"Registered start of job '{job_name}' with ID {job_id}")
        return job_id
    
    def register_job_end(self, job_id: int, status: str = "completed") -> None:
        """Register the end of a batch job
        
        Args:
            job_id: ID of the job
            status: Status of the job (completed, failed, etc.)
        """
        end_time = datetime.datetime.now()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get job details
        cursor.execute('SELECT job_name, start_time FROM job_metrics WHERE id = ?', (job_id,))
        result = cursor.fetchone()
        
        if not result:
            logger.error(f"Job with ID {job_id} not found")
            conn.close()
            return
        
        job_name, start_time_str = result
        start_time = datetime.datetime.fromisoformat(start_time_str)
        duration_seconds = (end_time - start_time).total_seconds()
        
        # Update job record
        cursor.execute(
            'UPDATE job_metrics SET end_time = ?, duration_seconds = ?, status = ? WHERE id = ?',
            (end_time, duration_seconds, status, job_id)
        )
        
        conn.commit()
        conn.close()
        
        # Update Prometheus metrics
        JOB_DURATION.labels(job_name=job_name, status=status).set(duration_seconds)
        JOB_COUNT.labels(job_name=job_name, status=status).inc()
        
        logger.info(f"Registered end of job '{job_name}' with status '{status}' (duration: {duration_seconds:.2f}s)")
    
    def get_recent_jobs(self, limit: int = 50) -> pd.DataFrame:
        """Get data for recent jobs
        
        Args:
            limit: Maximum number of recent jobs to return
            
        Returns:
            DataFrame containing job metrics
        """
        conn = sqlite3.connect(self.db_path)
        
        query = f"""
        SELECT 
            job_name, 
            start_time,
            end_time,
            duration_seconds,
            status
        FROM 
            job_metrics
        ORDER BY 
            start_time DESC
        LIMIT {limit}
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Convert timestamp strings to datetime objects
        df['start_time'] = pd.to_datetime(df['start_time'])
        df['end_time'] = pd.to_datetime(df['end_time'])
        
        return df
    
    def export_to_json(self, output_path: str = "job_metrics.json") -> None:
        """Export job metrics to JSON for Grafana
        
        Args:
            output_path: Path to output JSON file
        """
        df = self.get_recent_jobs(limit=1000)
        
        # Format for Grafana visualization
        jobs_data = []
        for _, row in df.iterrows():
            if pd.isna(row['end_time']) or pd.isna(row['duration_seconds']):
                # Job still running
                continue
                
            jobs_data.append({
                "job_name": row['job_name'],
                "start_time": row['start_time'].isoformat(),
                "end_time": row['end_time'].isoformat(),
                "duration_seconds": row['duration_seconds'],
                "status": row['status']
            })
        
        with open(output_path, 'w') as f:
            json.dump(jobs_data, f, indent=2)
            
        logger.info(f"Exported job metrics to {output_path}")


def main():
    """Main function to run the batch job monitor"""
    parser = argparse.ArgumentParser(description='Batch Job Monitor')
    parser.add_argument('--db-path', type=str, default='job_metrics.db',
                        help='Path to SQLite database')
    parser.add_argument('--port', type=int, default=8000,
                        help='Port for Prometheus metrics server')
    parser.add_argument('--export', action='store_true',
                        help='Export job metrics to JSON')
    parser.add_argument('--output', type=str, default='job_metrics.json',
                        help='Path to output JSON file')
    
    args = parser.parse_args()
    
    # Start Prometheus metrics server
    start_http_server(args.port)
    logger.info(f"Started Prometheus metrics server on port {args.port}")
    
    monitor = BatchJobMonitor(db_path=args.db_path)
    
    if args.export:
        monitor.export_to_json(output_path=args.output)
        return
    
    # Example usage - in a real scenario, you would integrate this with your batch job system
    demo_jobs = [
        "data_ingestion",
        "data_transformation",
        "ml_training",
        "report_generation",
        "data_cleanup"
    ]
    
    # Simulate some batch jobs
    for _ in range(3):
        for job_name in demo_jobs:
            # Start job
            job_id = monitor.register_job_start(job_name)
            
            # Simulate job running
            sleep_time = 2 + (hash(job_name) % 8)  # 2-10 seconds based on job name
            time.sleep(sleep_time)
            
            # End job
            status = "completed" if sleep_time < 8 else "failed"
            monitor.register_job_end(job_id, status=status)
    
    # Export metrics
    monitor.export_to_json(output_path=args.output)
    
    
if __name__ == "__main__":
    main()
