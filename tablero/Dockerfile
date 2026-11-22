FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY api/model_pkg/cdt_model_pkg-0.1.0-py3-none-any.whl /tmp/
COPY tablero/requirements.txt ./tablero/requirements.txt
RUN python -m pip install --only-binary=:all: /tmp/cdt_model_pkg-0.1.0-py3-none-any.whl -r tablero/requirements.txt \
    && rm /tmp/cdt_model_pkg-0.1.0-py3-none-any.whl

COPY api/__init__.py ./api/
COPY api/app/__init__.py api/app/profiles.py api/app/service.py ./api/app/
COPY tablero/ ./tablero/

EXPOSE 8050

CMD ["gunicorn", "--bind", "0.0.0.0:8050", "--workers", "1", "--threads", "4", "--timeout", "120", "tablero.wsgi:server"]
