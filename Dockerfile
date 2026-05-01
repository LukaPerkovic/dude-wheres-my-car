FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1

ENV PYTHONBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*


RUN pip install --updgrade pip \
    && pip install uv

COPY pyproject.toml uv.lock ./

RUN uv sync --system --frozen

COPY . .

CMD ["python", "main.py"]