# Backend Dockerfile
FROM python:3.11-slim

# Force rebuild: 2025-12-10-v1 - Add fix-encoding endpoint
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code FIRST
COPY app/ ./app/
COPY main.py .
COPY *.py ./

# Optional datasets are intentionally NOT copied (they may be large and/or contain API keys).
# Admin endpoints will gracefully report missing files if you haven't provided them.
# Example optional files:
# - hcm_restaurants_with_local_images.json
# - valid_image_names.json
# - places_photo_index.json
# - places_reviews_index.json

# Expose port
EXPOSE 8080

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
