import os
import json
import xml.etree.ElementTree as ET
import re

BPMN_FOLDER = 'bpmn'
PROCESS_JSON = 'process/process.json'

NAMESPACES = {
    'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL'
}

def extract_process_id(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    process = root.find('.//bpmn:process', NAMESPACES)
    return process.get('id') if process is not None else None

def generate_process_mapping():
    process_map = {}

    # Ensure the process directory exists
    os.makedirs(os.path.dirname(PROCESS_JSON), exist_ok=True)

    for file in os.listdir(BPMN_FOLDER):
        if file.endswith('.bpmn'):
            path = os.path.join(BPMN_FOLDER, file)
            process_id = extract_process_id(path)
            if process_id:
                process_map[process_id] = file

    with open(PROCESS_JSON, 'w') as f:
        json.dump(process_map, f, indent=2)

    return process_map


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


def requires_approval(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    user_tasks = root.findall('.//bpmn:userTask', NAMESPACES)

    # If there's at least one user task with a camunda:assignee, return True
    for task in user_tasks:
        if 'assignee' in task.attrib or any('assignee' in k for k in task.attrib.keys()):
            return True
    return False