FROM python:alpine

ENV NOISIER_CONFIG_JSON=config.json
ENV NOISIER_LOG_LEVEL=info

RUN adduser -D -H noisier
RUN mkdir /app && chown noisier:noisier /app
USER noisier

WORKDIR /app
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD pgrep -f "noisier.py" || exit 1

RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:${PATH}"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY noisier.py .
COPY config.json . 

ENTRYPOINT ["sh", "-c"]

CMD ["python /app/noisier.py --log $NOISIER_LOG_LEVEL --config $NOISIER_CONFIG_JSON"]
