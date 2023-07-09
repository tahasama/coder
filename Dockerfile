# Base image
FROM python:3.9-slim

# Working directory
WORKDIR /app

# Create and activate a virtual environment
RUN python -m venv venv
RUN . venv/bin/activate

# Install dependencies
RUN pip install --upgrade pip

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files
COPY . .

# Expose the server port
EXPOSE 8000

# Command to start the server
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "codeConverter.wsgi"]