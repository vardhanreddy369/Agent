# Use an official lightweight Python image.
# This "slim" version is smaller and faster to download.
FROM python:3.9-slim

# Set the working directory inside the container to /app
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install the Python dependencies inside the container
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code (main.py, credentials.json)
COPY . .

# Run the python script when the container launches
CMD ["python", "main.py"]
