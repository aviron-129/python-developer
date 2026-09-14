FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY traces ./traces
EXPOSE 8129
CMD ["uvicorn", "traces.main:app", "--host", "0.0.0.0", "--port", "8129"]
