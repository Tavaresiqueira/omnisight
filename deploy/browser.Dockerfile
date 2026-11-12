FROM mcr.microsoft.com/playwright/python:v1.62.0-noble
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /browser
COPY apps/browser/requirements.txt /browser/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=pwuser:pwuser apps/browser /browser
USER pwuser
EXPOSE 9000
CMD ["python", "server.py"]
