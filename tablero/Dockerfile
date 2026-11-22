FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY model_pkg/ ./model_pkg/
COPY tablero/requirements.txt ./tablero/requirements.txt
RUN python -m pip install --no-cache-dir ./model_pkg -r tablero/requirements.txt

COPY tablero/ ./tablero/

EXPOSE 8050

CMD ["gunicorn", "--bind", "0.0.0.0:8050", "--workers", "1", "--threads", "4", "--timeout", "120", "tablero.wsgi:server"]
