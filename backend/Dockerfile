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

# Copy JSON file for seeding
COPY hcm_restaurants_with_local_images.json /app/hcm_restaurants_with_local_images.json

# Copy valid image names for filtering
COPY valid_image_names.json /app/valid_image_names.json

# Copy indexes for multiple images + Google reviews import
COPY places_photo_index.json /app/places_photo_index.json
COPY places_reviews_index.json /app/places_reviews_index.json

# DO NOT copy smart_travel.db - let the app create fresh database with new schema (author_name column)

# Expose port
EXPOSE 8080

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
