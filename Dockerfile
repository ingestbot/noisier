FROM python:3.12-slim

SHELL ["/bin/bash", "-eo", "pipefail", "-c"]

ENV NOISIER_CONFIG_JSON=config.json
ENV NOISIER_LOG_LEVEL=info
ENV PATH="/app/venv/bin:${PATH}"

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        procps \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -g 1000 noisier && \
    useradd -m -u 1000 -g noisier noisier && \
    mkdir /app && chown noisier:noisier /app

USER noisier
WORKDIR /app

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD pgrep -f "noisier.py" || exit 1

RUN python -m venv /app/venv

COPY requirements.txt .
RUN pip install --no-cache-dir --disable-pip-version-check -r requirements.txt

COPY noisier.py .
COPY config.json .

ENTRYPOINT ["sh", "-c"]
CMD ["python /app/noisier.py --log \"$NOISIER_LOG_LEVEL\" --config \"$NOISIER_CONFIG_JSON\""]
