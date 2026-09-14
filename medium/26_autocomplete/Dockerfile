FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY suggest ./suggest
EXPOSE 8126
CMD ["uvicorn", "suggest.main:app", "--host", "0.0.0.0", "--port", "8126"]
