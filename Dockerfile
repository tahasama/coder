# Base image
FROM python:3.9-slim

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6  -y

# Install pip and gunicorn
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir --upgrade gunicorn

# Create a non-root user
RUN useradd -m myuser
USER myuser

# Working directory
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files
COPY . .

# Add path to gunicorn to PATH environment variable
ENV PATH="/home/myuser/.local/bin:${PATH}"

# Expose the server port
EXPOSE 8000

# Command to start Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "codeConverter.wsgi"]



# from bs4 import BeautifulSoup
# soup = BeautifulSoup("<p>Some<b>bad<i>HTML")
# print(soup.prettify())

# from electronvolt import *
# print(me)

# import pendulum
# now_in_paris = pendulum.now('Europe/Paris')
# print(now_in_paris)

# from DateTime import Timezones
# zones = set(Timezones())
# print(zones)

# from MathLibrary import *
# print(fact(5))