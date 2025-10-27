# Use Python 3.10 as base image
FROM python:3.13

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY . .

# Expose the port Streamlit runs on
EXPOSE 8088

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Command to run the application
CMD ["streamlit", "run", "app.py", "--server.port=8088", "--server.address=0.0.0.0"]
