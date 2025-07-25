# Use official Python 3.10 image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy all files
COPY . .

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose port
EXPOSE 10000

# Start the app
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "user_app:app"]
