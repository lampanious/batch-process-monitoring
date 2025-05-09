#!/bin/bash
# Adapter script for batch_job_monitor.py

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if the storage directory exists, if not create it
mkdir -p ${SCRIPT_DIR}/data

# Run the batch job monitor with the correct parameters
# Translating --db-path to --storage
python ${SCRIPT_DIR}/batch_job_monitor.py --storage ${SCRIPT_DIR}/data/job_metrics.db --simulate $@