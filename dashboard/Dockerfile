FROM python:3.11-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY main.py assets .
COPY users.json.dist users.json.dist
RUN if [ ! -f users.json ]; then cp users.json.dist users.json; fi

COPY data data/

EXPOSE 8501
ENV PORT=8501

ENTRYPOINT ["/entrypoint.sh"]
