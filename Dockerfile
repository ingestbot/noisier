FROM python:3.9.13-alpine
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --user
WORKDIR /app
COPY . .
ENTRYPOINT [ "python", "/app/noisier.py", "--config", "/app/config.json"]
