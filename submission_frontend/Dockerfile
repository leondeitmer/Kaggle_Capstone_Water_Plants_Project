# Use python 3.11 slim image
FROM python:3.11-slim

WORKDIR /app

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files
COPY pyproject.toml ./

# Install python dependencies
RUN uv pip install --system --requirement pyproject.toml

# Copy codebase
COPY main.py moisture_calculator.py plant_database.json ./
COPY static/ ./static/

# Set production env variables
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8080

EXPOSE 8080

# Run uvicorn server
CMD ["python", "main.py"]
