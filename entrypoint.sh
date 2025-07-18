#!/bin/sh
set -e

echo "[entrypoint] Creating necessary directories..."
mkdir -p /app/process /app/pending /app/assignee /app/bpmn /app/templates

echo "[entrypoint] Generating process mapping JSON..."
python -c "from utils.bpmn_utils import generate_process_mapping; generate_process_mapping()"

echo "[entrypoint] Creating assignee JSON from ENV..."
python -c "
import os, json
assignees = os.getenv('ASSIGNEES', '').split(',')
os.makedirs('/app/assignee', exist_ok=True)
with open('/app/assignee/assignee_available.json', 'w') as f:
    json.dump(assignees, f)
"

echo "[entrypoint] Copying process.json to mounted host directory..."
cp /app/process/process.json /process/ 2>/dev/null || echo "No mounted /process folder to copy to"

echo "[entrypoint] Copying assignee_available.json to mounted host directory..."
cp /app/assignee/assignee_available.json /assignee/ 2>/dev/null || echo "No mounted /assignee folder to copy to"

echo "[entrypoint] Starting Gunicorn..."
exec gunicorn -b 0.0.0.0:5000 app:app
