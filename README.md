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
