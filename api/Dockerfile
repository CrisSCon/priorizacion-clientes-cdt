FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --no-create-home --uid 10001 api-user

COPY requirements.txt model_pkg/cdt_model_pkg-0.1.0-py3-none-any.whl /tmp/
RUN python -m pip install --only-binary=:all: -r /tmp/requirements.txt /tmp/cdt_model_pkg-0.1.0-py3-none-any.whl \
    && rm /tmp/requirements.txt /tmp/cdt_model_pkg-0.1.0-py3-none-any.whl

COPY __init__.py ./api/
COPY app/ ./api/app/

USER api-user
EXPOSE 8001

CMD ["python", "-m", "uvicorn", "api.app.main:app", "--host", "0.0.0.0", "--port", "8001"]
