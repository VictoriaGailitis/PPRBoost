# Этап сборки
FROM python:3.12-slim AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends poppler-utils && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /admin_service

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt && \
    pip install --no-cache-dir sentence-transformers

ENV HF_HOME=/admin_service/llms
RUN mkdir -p /admin_service/llms/hub && \
    python -c "from sentence_transformers import SentenceTransformer; \
    model = SentenceTransformer('intfloat/multilingual-e5-large'); \
    model.save_pretrained('/admin_service/llms/hub/models--intfloat--multilingual-e5-large'); \
    print('Model downloaded and saved to /admin_service/llms/hub/models--intfloat--multilingual-e5-large')"

# Финальный образ
FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends poppler-utils && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /admin_service

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/admin_service/llms

COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*

COPY --from=builder /admin_service/llms/ /admin_service/llms/
COPY . .

# Используем Gunicorn с минимальным количеством воркеров для экономии памяти
CMD ["sh", "-c", "python manage.py collectstatic --noinput && python manage.py migrate && gunicorn adminService.wsgi:application --bind 0.0.0.0:8001 --workers 1 --threads 1"]
