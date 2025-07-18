# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Build-time env var to get assignees
ARG ASSIGNEES
ENV ASSIGNEES=${ASSIGNEES}

# Create assignee JSON and folders during build
RUN mkdir -p assignee && \
    python3 -c "import os, json; \
    assignees = os.getenv('ASSIGNEES', '').split(','); \
    os.makedirs('assignee', exist_ok=True); \
    json.dump(assignees, open('assignee/assignee_available.json', 'w'))"

# Create required folders
RUN mkdir -p bpmn pending process templates

# Expose port
EXPOSE 5000

# Run the app with Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
