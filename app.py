from flask import Flask, request, jsonify, send_from_directory, render_template
from utils.bpmn_utils import generate_process_mapping, extract_script_tasks, try_parse_value
from utils.file_utils import (
    load_pending_requests, save_pending_requests,
    load_assignees, load_process_map
)
import os
import re
from utils.process_handlers import PROCESS_HANDLERS

app = Flask(__name__)

PROCESS_DIR = os.path.join(os.getcwd(), 'process')
PROCESS_JSON = os.path.join(PROCESS_DIR, 'process.json')


ASSIGNEE_DIR = os.path.join(os.getcwd(), 'assignee')
ASSIGNEE_JSON = os.path.join(ASSIGNEE_DIR, 'assignee_available.json')

PENDING_REQUESTS_DIR = os.path.join(os.getcwd(), 'pending')
PENDING_REQUESTS_JSON = os.path.join(PENDING_REQUESTS_DIR, 'pending_requests.json')

# Load global data once or reload if needed
process_map = load_process_map()
assignees = load_assignees()


@app.route('/')
def index():
    process_id = request.args.get('process_id')
    if not process_id or process_id not in process_map:
        return "Invalid process ID", 400

    bpmn_file = process_map[process_id]
    bpmn_path = os.path.join('bpmn', bpmn_file)

    from utils.bpmn_utils import requires_approval
    approval_required = requires_approval(bpmn_path)

    ctx = {
        'process_id': process_id,
        'assignees': assignees,
        'approval_required': approval_required,
    }

    # Map each process to its template
    template_map = {
        'UserValidationProcess': 'process_form.html',
        'CheckAMPM':             'time.html',
        'UserRegistrationApproval': 'registration_form.html',
        'UserRegistrationAuto':               'registration_form.html',  # ← here
    }

    tpl = template_map.get(process_id)
    if not tpl:
        return "Invalid process ID", 400

    return render_template(tpl, **ctx)


@app.route('/portal/<string:assignee>')
def assignee_portal(assignee):
    return render_template('portal.html', assignee=assignee)


@app.route('/assignee_available.json')
def serve_assignees():
    return send_from_directory('.', 'assignee_available.json')


@app.route('/submit-request', methods=['POST'])
def submit_request():
    data = request.form.to_dict()
    process_id = data.get('process_id')
    assignee = data.get('assignee')  # may be None
    variables = {k: v for k, v in data.items() if k not in ('process_id', 'assignee')}

    if not process_id:
        return jsonify({'error': 'process_id is required'}), 400

    bpmn_file = process_map.get(process_id)
    if not bpmn_file:
        return jsonify({'error': 'Invalid process_id'}), 404

    bpmn_path = os.path.join("bpmn", bpmn_file)

    from utils.bpmn_utils import requires_approval
    approval_required = requires_approval(bpmn_path)

    if approval_required:
        if not assignee:
            return jsonify({'error': 'Assignee required for approval flows'}), 400
        pending = load_pending_requests()
        pending.append({
            'process_id': process_id,
            'assignee': assignee,
            'variables': variables,
        })
        save_pending_requests(pending)
        return jsonify({'message': 'Pending approval', 'total_pending': len(pending)}), 201

    # 🔁 Otherwise, approval not required → Auto evaluate and handle
    from werkzeug.datastructures import MultiDict
    form_data = MultiDict(data)
    form_data.setlist("process_id", [process_id])  # ensure it's in list format

    with app.test_request_context('/evaluate', method='POST', data=form_data):
        eval_response = evaluate()
        response_data = eval_response.get_json()

    return jsonify({
        'message': 'Auto-evaluated and processed',
        'result': response_data
    }), 200



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


@app.route('/evaluate', methods=['POST'])
def evaluate():
    data = request.form
    process_id = data.getlist('process_id')[0] if 'process_id' in data else None
    if not process_id:
        return jsonify({'error': 'Missing process_id'}), 400

    if process_id not in process_map:
        return jsonify({'error': f'Process ID \"{process_id}\" not found'}), 404

    bpmn_path = os.path.join('bpmn', process_map[process_id])

    variables = {
        k: try_parse_value(v)
        for k, v in data.items()
        if k != 'process_id'
    }

    tasks = extract_script_tasks(bpmn_path)
    results = {}

    safe_builtins = {
        "bool": bool, "int": int, "float": float, "str": str,
        "len": len, "min": min, "max": max, "sum": sum, "abs": abs,
        "all": all, "any": any,
    }

    safe_globals = {
        "__builtins__": safe_builtins,
        "re": re,
    }

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

    response = {
        "results": results,
        "variables": variables
    }
    if validations:
        response["validations"] = validations
    
    import traceback
    try:
        print(process_id)
        handler = PROCESS_HANDLERS.get(process_id)
        print(handler)
        if handler:
            try:
                response["post_process"] = handler(variables)
            except Exception as e:
                print(f"[Handler Error] {process_id}: {str(e)}")
                print(traceback.format_exc())
                response["post_process"] = {"error": f"Handler failed: {str(e)}"}
    except Exception as outer_e:
        print(f"[Evaluate Error] {process_id}: {str(outer_e)}")
        print(traceback.format_exc())
        return jsonify({'error': 'Internal evaluation failure'}), 500

    # ✅ Always return a response
    return jsonify(response)



    
if __name__ == '__main__':
    os.makedirs('process', exist_ok=True)
    os.makedirs('pending', exist_ok=True)
    os.makedirs('assignee', exist_ok=True)
    os.makedirs('bpmn', exist_ok=True)


    # Generate process mapping JSON file
    generate_process_mapping()
    print(f"✅ Process mapping generated: process.json")

    # Run Flask
    app.run(host='0.0.0.0', port=5001, debug=True)
