from flask import Flask, request, jsonify
import xml.etree.ElementTree as ET
import tempfile
import os
import re  # import once globally for injection into script execution

app = Flask(__name__)

NAMESPACES = {
    'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'
}

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

def try_parse_value(value):
    if value.lower() in ['true', 'false']:
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
    if 'bpmn_file' not in request.files:
        return jsonify({'error': 'Missing BPMN file'}), 400

    variables = {
        k: try_parse_value(v)
        for k, v in request.form.items()
        if k != 'bpmn_file'
    }

    bpmn_file = request.files['bpmn_file']
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bpmn") as temp:
        bpmn_file.save(temp.name)
        tasks = extract_script_tasks(temp.name)
        os.unlink(temp.name)

    results = {}

    # Define allowed builtins explicitly (safe subset)
    safe_builtins = {
        "bool": bool,
        "int": int,
        "float": float,
        "str": str,
        "len": len,
        "min": min,
        "max": max,
        "sum": sum,
        "abs": abs,
        # Add more if needed
    }

    safe_globals = {"__builtins__": safe_builtins, "re": re}

    for task in tasks:
        try:
            if '=' in task['script']:
                # Use exec with the same variables dict to share state between tasks
                exec(task['script'], safe_globals, variables)
                results[task['name'] or task['id']] = "executed"
            else:
                result = eval(task['script'], safe_globals, variables)
                results[task['name'] or task['id']] = bool(result)
        except Exception as e:
            results[task['name'] or task['id']] = f"Error: {str(e)}"

    return jsonify({
        "results": results,
        "variables": variables
    })


if __name__ == '__main__':
    app.run(debug=True)
