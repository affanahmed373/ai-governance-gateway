# Hugging Face Docker Space (and local) image. Listens on 7860. No LLM key required.
FROM python:3.11-slim

WORKDIR /app

COPY requirements-runtime.txt .
RUN pip install --no-cache-dir -r requirements-runtime.txt

COPY app ./app
COPY config ./config

ENV PORT=7860
EXPOSE 7860

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
