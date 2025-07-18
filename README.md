# 🧠 BPMN Parser & Evaluation Portal

A Flask-based BPMN evaluator and reviewer tool that:
- Parses BPMN `.bpmn` XML files with script tasks
- Submits requests to assignees
- Allows assignees to review and accept/reject
- Runs in Docker with configurable assignees from `.env`

---

## 🚀 Features

- BPMN evaluation via script task logic
- Dynamic assignee portal with request queue
- Fully Dockerized with auto-folder & JSON creation
- Live templates for custom workflows
- Gunicorn for production-ready serving

---

## 🧱 Folder Structure

```

.
├── app.py                   # Main Flask app
├── assignee/                # Auto-created from .env
├── bpmn/                    # BPMN XML files
├── pending/                 # Pending review requests
├── process/                 # Auto-generated process.json
├── templates/               # HTML forms and portals
├── utils/                   # Script parsing + file tools
├── Dockerfile
├── docker-compose.yml
├── .env
└── README.md

````

---

## ⚙️ Setup

### 1. 📦 Create a `.env` file

```env
ASSIGNEES=alice,bob,carol
````

These will be auto-used to:

* Create `/assignee` folder
* Generate `assignee/assignee_available.json`

---

### 2. 🐳 Build & Run

```bash
docker-compose build
docker-compose up
```

Then visit:
📍 [http://127.0.0.1:5050](http://localhost:5050)

---

### 3. 🧪 Trigger Evaluation (Direct API Use)

You can directly call the evaluation API to run BPMN logic without any UI forms or review:

```bash
curl -X POST http://localhost:5050/evaluate \
  -F "process_id=CheckAMPM" \
  -F "time=15:20"
```

This is useful for automation or standalone usage.

---

### 4. 🧑‍⚖️ Full Review Workflow (Using Forms and Portal)

To leverage the full review feature with submission forms and assignee review portals:

* Submit requests via form for a given process, e.g.:

  ```
  http://127.0.0.1:5050/?process_id=UserValidationProcess
  ```

* Review requests as an assignee:

  ```
  http://127.0.0.1:5050/portal/<assignee_name>
  ```

The portal internally uses the `/evaluate` API for processing but provides a user-friendly interface for review, accept/reject, and management.

---
Absolutely! Here’s a clear section you can add to your README explaining how users can add their own BPMN 2.0 files, link them, and use them in your app:

---

## ➕ Adding Your Own BPMN 2.0 Files

You can extend the application by adding your own BPMN 2.0 workflow files. Here’s how:

### 1. Add your BPMN file

Place your BPMN XML file (`*.bpmn`) inside the `/bpmn` directory.

Example:

```
/bpmn
  ├── your_custom_process.bpmn
  └── ...
```

---

### 2. Define the Process ID

Make sure your BPMN file contains a `<process>` element with a unique `id` attribute. For example:

```xml
<bpmn:process id="YourCustomProcessID" ...>
  ...
</bpmn:process>
```

This `id` is how the app identifies and runs your process.

---

### 3. Update the process mapping

The app automatically generates `process/process.json` by scanning the `/bpmn` folder for `.bpmn` files and extracting their process IDs.

This mapping links process IDs to the respective BPMN files.

If you add or update BPMN files, **restart the app** or rebuild the Docker image to regenerate this mapping.

---

### 4. Use your process

You can now invoke your custom BPMN process via:

* **Direct API call:**

```bash
curl -X POST http://localhost:5050/evaluate \
  -F "process_id=YourCustomProcessID" \
  -F "your_variable1=value1" \
  -F "your_variable2=value2"
```

* **Form UI (if you create a corresponding form template):**

```
http://localhost:5050/?process_id=YourCustomProcessID
```

* **Review portal:**

```
http://localhost:5050/portal/<assignee_name>
```

---

### 5. (Optional) Add form templates

If your process requires user input forms:

* Create a new HTML template inside the `/templates` folder, e.g., `your_custom_process.html`.
* Customize the form inputs to match the variables your BPMN process expects.
* The app will render this form when accessed with `?process_id=YourCustomProcessID`.

---

This makes your BPMN workflows fully extensible and integrated into the review and evaluation system.

---

Would you like me to help you create a sample BPMN file and matching form template as a starting point?


## 🛠️ Development Tips

* New `.bpmn` files in `/bpmn` are auto-indexed via `process/process.json`
* HTML templates can be edited in `templates/`
* Add new logic using `<scriptTask>` in BPMN files

---

## 🧼 Clean Up

```bash
docker-compose down
```
---

