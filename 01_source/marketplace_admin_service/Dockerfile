FROM python:3.12-slim

WORKDIR /app

COPY marketplace_admin_service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY marketplace_admin_service/app ./app
COPY marketplace_admin_service/migrations ./migrations
COPY shared ./shared

ENV PYTHONPATH=/app
EXPOSE 8019

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8019"]
