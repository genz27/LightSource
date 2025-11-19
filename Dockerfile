FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app app
COPY scripts scripts

RUN mkdir -p /app/storage/media

ENV STORAGE_BASE=/app/storage/media
ENV DATABASE_URL=postgresql+psycopg2://postgres:postgres@host.docker.internal:5432/lightsource
ENV CORS_ORIGINS=["*"]
ENV PUBLIC_API_KEY=
ENV RATE_LIMIT_PER_MINUTE=60
ENV BURST_LIMIT=20
ENV JWT_SECRET=please-change-in-prod
ENV JWT_ACCESS_MINUTES=15
ENV JWT_REFRESH_MINUTES=10080
ENV DEBUG=false

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]