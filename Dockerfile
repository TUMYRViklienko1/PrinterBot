FROM python:3.11-slim-bookworm

# Prevent Python from writing .pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /usr/src/app

# System dependencies (minimized, merged into one layer)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      gcc \
      libffi-dev \
      libpq-dev \
      curl \
 apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (leverage cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy your app source
COPY . .

# Start command
CMD ["python", "./main.py"]
