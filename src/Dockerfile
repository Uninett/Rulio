# Use an official lightweight Python image
FROM python:3.12-slim

# Set environment variables to optimize Python inside Docker
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /backend

# Install system dependencies (if needed for database adapters like psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt /backend/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your local project files into the container
COPY . /backend/

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]