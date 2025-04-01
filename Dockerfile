FROM oven/bun:1.0 AS bun-builder
WORKDIR /app/messaging
COPY messaging/package.json messaging/bun.lockb ./
RUN bun install
COPY messaging/ ./

FROM python:3.11-slim
WORKDIR /app

COPY --from=bun-builder /usr/local/bin/bun /usr/local/bin/bun
COPY --from=bun-builder /app/messaging /app/messaging

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main_api/ /app/main_api
COPY supervisord.conf .

CMD ["supervisord", "-c", "supervisord.conf"] 