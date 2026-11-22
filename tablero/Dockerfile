# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    API_URL=localhost \
    API_PORT=8001

WORKDIR /app

RUN useradd --no-create-home --uid 10001 dash-user

COPY requirements.txt ./tablero/requirements.txt
RUN python -m pip install -r tablero/requirements.txt

COPY *.py sample_customers.csv ./tablero/
COPY assets/ ./tablero/assets/
COPY --from=common /*.py /app/common/

USER dash-user
EXPOSE 8050

CMD ["gunicorn", "--bind", "0.0.0.0:8050", "--workers", "1", "--threads", "4", "--timeout", "120", "tablero.wsgi:server"]
