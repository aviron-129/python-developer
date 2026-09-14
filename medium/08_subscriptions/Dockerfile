FROM python:3.12-slim
WORKDIR /app
RUN mkdir -p /data
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY subs ./subs
ENV DATABASE_PATH=/data/state.db
EXPOSE 8108
CMD ["uvicorn", "subs.main:app", "--host", "0.0.0.0", "--port", "8108"]
