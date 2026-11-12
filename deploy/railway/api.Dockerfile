FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gosu && rm -rf /var/lib/apt/lists/*
COPY apps/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home --uid 10001 app
COPY --chown=app:app apps/api /app
COPY deploy/railway/api-entrypoint.sh /usr/local/bin/api-entrypoint.sh
ENTRYPOINT ["sh", "/usr/local/bin/api-entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "[::]:8000", "--workers", "2", "--timeout", "30", "--access-logfile", "-"]
