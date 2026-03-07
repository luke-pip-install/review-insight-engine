# 1. Base image
FROM python:3.11-slim

# 2. Set workdir inside the container
WORKDIR /app

# 3. Install system dependencies (optional)
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# 4. Copy Python dependency file and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy your source code
COPY . .

# 6. Expose port (if your app has a web API)
EXPOSE 8000

# 7. Command to run your app
CMD ["python", "main.py"]
