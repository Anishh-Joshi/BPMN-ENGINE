FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Create necessary directories (optional here, also in entrypoint)
RUN mkdir -p bpmn pending process templates assignee

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 5000

# Run entrypoint script on container start
ENTRYPOINT ["/entrypoint.sh"]
