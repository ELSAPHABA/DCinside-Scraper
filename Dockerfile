FROM python:3.11-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir ".[s3,postgres]"

ENTRYPOINT ["python", "-m", "dcinside_scraper.adapters.container"]
