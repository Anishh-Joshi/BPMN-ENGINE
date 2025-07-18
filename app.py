from flask import Flask, request, jsonify,send_from_directory,render_template
import xml.etree.ElementTree as ET
import tempfile
import os
import re
import json

app = Flask(__name__)


PENDING_REQUESTS_FILE = 'pending_requests.json'
ASSIGNEE_FILE = 'assignee_available.json'
PROCESS_MAP_PATH = 'process.json'

def load_process_map():
    if os.path.exists(PROCESS_MAP_PATH):
        with open(PROCESS_MAP_PATH) as f:
            return json.load(f)
    return {}

def load_assignees():
    if os.path.exists(ASSIGNEE_FILE):
        with open(ASSIGNEE_FILE) as f:
            return json.load(f)
    return []

process_map = load_process_map()
assignees = load_assignees()

@app.route('/')
def index():
    process_id = request.args.get('process_id', None) 
    
    if process_id == 'UserValidationProcess':
        return render_template('process_form.html', 
                            process_id=process_id, 
                            assignees=assignees)
    elif process_id == 'CheckAMPM':
        return render_template('time.html', 
                            process_id=process_id, 
                            assignees=assignees)
    else:
        return "Invalid process ID", 400

@app.route('/portal/<assignee>')
def assignee_portal(assignee):
    # Pass the assignee name to the template
    return render_template('portal.html', assignee=assignee)


def load_pending_requests():
    if os.path.exists(PENDING_REQUESTS_FILE):
        with open(PENDING_REQUESTS_FILE) as f:
            return json.load(f)
    return []

def save_pending_requests(requests):
    with open(PENDING_REQUESTS_FILE, 'w') as f:
        json.dump(requests, f, indent=2)

@app.route('/assignee_available.json')
def serve_assignees():
    # Assignee file should exist in the same dir or serve via static
    return send_from_directory('.', ASSIGNEE_FILE)

@app.route('/submit-request', methods=['POST'])
def submit_request():
    data = request.form.to_dict()
    # Extract variables except process_id and assignee
    process_id = data.get('process_id')
    assignee = data.get('assignee')

    # Extract variables (all other keys except process_id and assignee)
    variables = {k: v for k, v in data.items() if k not in ('process_id', 'assignee')}

    if not process_id or not assignee:
        return jsonify({'error': 'process_id and assignee are required'}), 400

    pending = load_pending_requests()
    pending.append({
        'process_id': process_id,
        'assignee': assignee,
        'variables': variables,
    })
    save_pending_requests(pending)

    return jsonify({'message': 'Request submitted', 'total_pending': len(pending)}), 201

@app.route('/pending-requests')
def pending_requests():
    pending = load_pending_requests()
    return jsonify(pending)

@app.route('/mark-request-processed/<int:index>', methods=['POST'])
def mark_request_processed(index):
    pending = load_pending_requests()
    if 0 <= index < len(pending):
        pending.pop(index)
        save_pending_requests(pending)
        return jsonify({'message': 'Request processed and removed'})
    else:
        return jsonify({'error': 'Invalid request index'}), 404

@app.route('/reject-request/<int:index>', methods=['POST'])
def reject_request(index):
    pending = load_pending_requests()
    if 0 <= index < len(pending):
        pending.pop(index)
        save_pending_requests(pending)
        return jsonify({'message': 'Request rejected and removed'})
    else:
        return jsonify({'error': 'Invalid request index'}), 404

















# ----------------------------------------------------------------
# Folder and file paths
BPMN_FOLDER = os.path.join(os.getcwd(), 'bpmn')
PROCESS_JSON = os.path.join(os.getcwd(), 'process.json')

# BPMN namespace for parsing
NAMESPACES = {
    'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'
}


# Extract process ID from a BPMN file
def extract_process_id(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    process = root.find('.//bpmn:process', NAMESPACES)
    return process.get('id') if process is not None else None


# Scan all BPMN files and generate process.json
def generate_process_mapping():
    process_map = {}
    for file in os.listdir(BPMN_FOLDER):
        if file.endswith('.bpmn'):
            path = os.path.join(BPMN_FOLDER, file)
            process_id = extract_process_id(path)
            if process_id:
                process_map[process_id] = file
    with open(PROCESS_JSON, 'w') as f:
        json.dump(process_map, f, indent=2)
    return process_map


# Extract all script tasks from a BPMN file
def extract_script_tasks(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    script_tasks = root.findall('.//bpmn:scriptTask', NAMESPACES)
    tasks = []
    for task in script_tasks:
        script_elem = task.find('bpmn:script', NAMESPACES)
        if script_elem is not None:
            tasks.append({
                'id': task.get('id'),
                'name': task.get('name'),
                'script': script_elem.text.strip()
            })
    return tasks


# Attempt to parse input types
def try_parse_value(value):
    if isinstance(value, str) and value.lower() in ['true', 'false']:
        return value.lower() == 'true'
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


@app.route('/evaluate', methods=['POST'])
def evaluate():
    data = request.form
    process_id = data.get('process_id')
    if not process_id:
        return jsonify({'error': 'Missing process_id'}), 400

    # Load process.json
    try:
        with open(PROCESS_JSON) as f:
            process_map = json.load(f)
    except Exception as e:
        return jsonify({'error': f'Failed to load process.json: {e}'}), 500

    if process_id not in process_map:
        return jsonify({'error': f'Process ID \"{process_id}\" not found'}), 404

    bpmn_path = os.path.join(BPMN_FOLDER, process_map[process_id])

    # Load variables from form input
    variables = {
        k: try_parse_value(v)
        for k, v in request.form.items()
        if k != 'process_id'
    }

    # Get script tasks from the BPMN
    tasks = extract_script_tasks(bpmn_path)
    results = {}

    # Define safe execution environment
    safe_builtins = {
        "bool": bool, "int": int, "float": float, "str": str,
        "len": len, "min": min, "max": max, "sum": sum, "abs": abs,
        "all": all, "any": any,
    }

    safe_globals = {
        "__builtins__": safe_builtins,
        "re": re,
    }

    # Execute script tasks
    for task in tasks:
        try:
            if '=' in task['script'] or 'db_' in task['script']:
                exec(task['script'], safe_globals, variables)
                results[task['name'] or task['id']] = "executed"
            else:
                result = eval(task['script'], safe_globals, variables)
                results[task['name'] or task['id']] = bool(result)
        except Exception as e:
            results[task['name'] or task['id']] = f"Error: {str(e)}"

    # Dynamically build validations based on is_* or is_valid_* variables
    validations = {
        re.sub(r'^is_valid_', '', k): v
        for k, v in variables.items()
        if k.startswith("is_valid_") and isinstance(v, bool)
    }

    validations.update({
        re.sub(r'^is_', '', k): v
        for k, v in variables.items()
        if k.startswith("is_") and isinstance(v, bool) and re.sub(r'^is_', '', k) not in validations
    })

    # Final response
    response = {
        "results": results,
        "variables": variables
    }

    if validations:
        response["validations"] = validations

    return jsonify(response)


if __name__ == '__main__':
    if not os.path.exists(BPMN_FOLDER):
        os.makedirs(BPMN_FOLDER)
    generate_process_mapping()
    print(f"✅ Process mapping generated: {PROCESS_JSON}")
    app.run(debug=True)
