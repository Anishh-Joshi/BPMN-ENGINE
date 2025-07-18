import json
import os

PENDING_REQUESTS_FILE = 'pending/pending_requests.json'
ASSIGNEE_FILE = 'assignee/assignee_available.json'
PROCESS_MAP_PATH = 'process/process.json'

def load_pending_requests():
    if os.path.exists(PENDING_REQUESTS_FILE):
        with open(PENDING_REQUESTS_FILE) as f:
            return json.load(f)
    return []

def save_pending_requests(requests):
    with open(PENDING_REQUESTS_FILE, 'w') as f:
        json.dump(requests, f, indent=2)

def load_assignees():
    if os.path.exists(ASSIGNEE_FILE):
        with open(ASSIGNEE_FILE) as f:
            return json.load(f)
    return []

def load_process_map():
    if os.path.exists(PROCESS_MAP_PATH):
        with open(PROCESS_MAP_PATH) as f:
            return json.load(f)
    return {}
