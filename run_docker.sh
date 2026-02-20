#!/bin/bash
echo "Building Docker image..."
docker build -t automation-agent .

echo "Running Docker container..."
docker run --rm automation-agent
