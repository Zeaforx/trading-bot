# Use a lightweight Python Linux image
FROM python:3.12.12-slim-trixie

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies required for psycopg2 (Postgres adapter)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all your code into the container
COPY . .

# Command to run when the container starts
CMD ["python", "main.py"]