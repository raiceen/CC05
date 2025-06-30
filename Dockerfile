# Use the official Python slim image
FROM python:3.11-slim

# Set workdir inside the container
WORKDIR /app

# Copy dependency lists first (to leverage Docker cache)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Expose the port your Flask app will run on
EXPOSE 5000

# Set environment variables for Flask
ENV FLASK_APP=flask_app.py
ENV FLASK_RUN_HOST=0.0.0.0
# (Optional) set production config, e.g. disable reloader
ENV FLASK_ENV=production

# Command to launch the app
CMD ["flask", "run"]
