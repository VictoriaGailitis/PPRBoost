FROM python:3.12-slim AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends poppler-utils && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .                                                                                                        
RUN python3 -m pip install --upgrade pip && \
    pip install --no-cache-dir torch==2.4.1 -f https://download.pytorch.org/whl/cpu/torch-2.4.1%2Bcpu-cp312-cp312-linux_x86_64.whl && \  
    pip install --no-cache-dir -r requirements.txt

ENV HF_HOME=/app/llms

RUN mkdir -p /app/llms/hub && \
    python -c "from sentence_transformers import SentenceTransformer; \
    model = SentenceTransformer('intfloat/multilingual-e5-large'); \
    model.save_pretrained('/app/llms/hub/models--intfloat--multilingual-e5-large'); \
    print('Model downloaded and saved to /app/llms/hub/models--intfloat--multilingual-e5-large')"

FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends poppler-utils && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

COPY --from=builder /app/llms/ /app/llms

COPY . .

ENV PYTHONPATH=/app
ENV HF_HOME=/app/llms
ENV USER_AGENT="MyApp/1.0"

CMD ["gunicorn", "--workers=1", "--worker-class=uvicorn.workers.UvicornWorker", "--bind=0.0.0.0:8000", "--timeout=5000", "main:app"]