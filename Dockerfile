FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "main_enriched_stage1_5:app", "--host", "0.0.0.0", "--port", "80"]
