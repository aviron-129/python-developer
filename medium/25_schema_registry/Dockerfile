FROM python:3.12-slim
WORKDIR /app
RUN mkdir -p /data
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY registry ./registry
ENV DATABASE_PATH=/data/state.db
EXPOSE 8125
CMD ["uvicorn", "registry.main:app", "--host", "0.0.0.0", "--port", "8125"]
