FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl unzip \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && npm install -g dingtalk-workspace-cli \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

RUN mkdir -p /app/data /app/.dws

EXPOSE 5080
CMD ["python", "-m", "src.main"]
