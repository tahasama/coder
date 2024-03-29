# Base image
FROM python:3.9-slim

# Create a non-root user
RUN useradd -m myuser
USER myuser

# Working directory
WORKDIR /app

RUN pip install --upgrade pip

# Copy requirements file and install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files
COPY . .

# Add path to gunicorn to PATH environment variable
ENV PATH="/home/myuser/.local/bin:${PATH}"

# Expose the server port
EXPOSE 8000

# Command to start the server
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "codeConverter.wsgi"]