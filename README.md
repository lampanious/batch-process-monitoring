# Batch Job Monitoring System

This system provides a comprehensive solution for monitoring batch job processing, with a focus on visualizing:
- Job execution timelines (horizontal bars showing start time and duration)
- Job names (vertical axis)
- Job status and performance metrics

## Components

1. **Python Monitoring Script**: Collects and exports batch job metrics
2. **Grafana Dashboard**: Visualizes job processing data with horizontal bars for timing and vertical listing of job names

## Installation and Setup

### Prerequisites

- Python 3.7+
- SQLite
- Prometheus
- Grafana

### Python Dependencies

```bash
pip install pandas prometheus_client requests
```

### Setup Instructions

1. **Clone or download the repository**

2. **Install the Python script**
   ```bash
   # Make the script executable
   chmod +x batch_job_monitor.py
   ```

3. **Start the Prometheus metrics server**
   ```bash
   python batch_job_monitor.py --port 8000
   ```

4. **Configure Prometheus**
   
   Add the following to your `prometheus.yml` configuration:
   ```yaml
   scrape_configs:
     - job_name: 'batch_job_monitor'
       static_configs:
         - targets: ['localhost:8000']
   ```

5. **Import the Grafana Dashboard**
   - In Grafana, navigate to Dashboards > Import
   - Upload the provided JSON dashboard file or copy/paste its contents
   - Configure the Prometheus data source

## Usage

### Integrating with Your Batch Jobs

Add the following code at the beginning and end of your batch jobs:

```python
from batch_job_monitor import BatchJobMonitor

# Initialize the monitor
monitor = BatchJobMonitor()

# At the start of your job
job_id = monitor.register_job_start("your_job_name")

# ... Your job processing here ...

# At the end of your job
monitor.register_job_end(job_id, status="completed")  # or "failed" if there was an error
```

### Running the Monitor Standalone

```bash
# Basic usage with default settings
python batch_job_monitor.py

# Specify a custom database path
python batch_job_monitor.py --db-path /path/to/custom/db.sqlite

# Export metrics to JSON for external processing
python batch_job_monitor.py --export --output job_metrics.json
```

### Viewing the Dashboard

1. Open Grafana in your browser (default: http://localhost:3000)
2. Navigate to the "Batch Job Processing Dashboard"

## Dashboard Features

The Grafana dashboard provides the following visualizations:

1. **Batch Job Duration by Job Name**
   - Stacked bar chart showing job durations over time

2. **Batch Job Timeline**
   - Horizontal bars representing job execution
   - X-axis shows time/duration
   - Y-axis shows job names
   - Color coding based on status

3. **Recent Batch Jobs Table**
   - Detailed listing of recent jobs with sortable columns
   - Visual indicators for job status and duration

4. **Job Distribution Charts**
   - Pie charts showing distribution by job name and status

## Customization

### Adding New Metrics

To add new metrics to the monitoring system:

1. Define new Prometheus metrics in the Python script
2. Update the `register_job_start` and `register_job_end` methods
3. Add new panels to the Grafana dashboard

### Dashboard Variables

The dashboard includes the following variables for filtering:

- `job_name`: Filter by specific job names
- `status`: Filter by job status (completed, failed, running)
- `interval`: Time range selection

## Troubleshooting

### Common Issues

1. **No data appearing in Grafana**
   - Check that the Prometheus server is running and scraping the metrics endpoint
   - Verify that the batch job monitor script is running with `ps aux | grep batch_job_monitor`
   - Check Prometheus targets status page for any scraping errors

2. **Database errors**
   - Ensure SQLite is properly installed
   - Check file permissions on the database file
   - Use the SQLite command-line tool to verify database integrity: `sqlite3 job_metrics.db .schema`

3. **Missing job data**
   - Ensure jobs are properly calling both `register_job_start` and `register_job_end`
   - Check for error messages in the log file: `cat batch_job_monitor.log`

## Advanced Configuration

### Retention Policy

By default, the system keeps all job data indefinitely. To implement a retention policy:

1. Add a scheduled task to clean up old data:

```python
def cleanup_old_data(days=30):
    """Delete job records older than the specified number of days"""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
    
    cursor.execute(
        'DELETE FROM job_metrics WHERE start_time < ?',
        (cutoff_date,)
    )
    
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    
    logger.info(f"Cleaned up {deleted_count} job records older than {days} days")
```

2. Call this function periodically or via a cron job.

### High-Availability Setup

For production environments, consider:

1. Using a more robust database like PostgreSQL instead of SQLite
2. Setting up redundant monitoring servers
3. Implementing alerting for failed jobs or system issues

## Performance Considerations

- For systems with many concurrent batch jobs, consider:
  - Increasing the database connection pool size
  - Batching metric updates
  - Using a dedicated metrics server

- For very long-running jobs:
  - Implement progress tracking with checkpoints
  - Consider sending heartbeat signals during job execution

## Security

- The monitoring system does not implement authentication by default
- For production use, secure the Prometheus and Grafana endpoints
- Consider encrypting sensitive job data if needed

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.