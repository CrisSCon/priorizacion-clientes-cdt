# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app/api

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --no-create-home --uid 10001 api-user

COPY requirements.txt ./
COPY model_pkg/*.whl ./model_pkg/
RUN python -m pip install -r requirements.txt

COPY __init__.py ./
COPY app/ ./app/
COPY --from=common /*.py /app/common/

WORKDIR /app
USER api-user
EXPOSE 8001

CMD ["python", "-m", "uvicorn", "api.app.main:app", "--host", "0.0.0.0", "--port", "8001"]
