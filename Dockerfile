# Stage 1: Build frontend
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend + serve frontend
FROM python:3.12-slim
WORKDIR /app

# Install backend dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend to static directory
COPY --from=frontend-build /app/frontend/dist/ ./static/

ENV PYTHONPATH=/app/backend
ENV ADMIN_PASSWORD=admin123
ENV DATABASE_URL=sqlite+aiosqlite:////data/app.db
ENV CORS_ORIGINS=*
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
