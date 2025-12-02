# Use an official Python runtime as a parent image
# Need at least Python 3.7+ for newer Flask/Gunicorn versions.
# Using 'slim' variant for smaller image size.
FROM python:3.10-slim

# Set environment variables
# PYTHONDONTWRITEBYTECODE prevents Python writing .pyc files
# PYTHONUNBUFFERED ensures container logging goes straight to terminal
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container to /app
WORKDIR /app

# Install system dependencies required for some python packages or sqlite3
# (Optional: remove apt-get lines if your specific app doesn't need OS-level libraries)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc-dev \
    sqlite3 \
 && rm -rf /var/lib/apt/lists/*

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code
# Note: This will copy tickets.db if it is not in .dockerignore
COPY . .

# Create a non-root user to run the application for security
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port 8000 for Gunicorn
EXPOSE 8000

# Define the command to run the application using Gunicorn
# Syntax: gunicorn [options] module_name:application_instance_name
# Assuming your Flask instance inside app.py is named 'app' (e.g., app = Flask(__name__))
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4", "app:app"]