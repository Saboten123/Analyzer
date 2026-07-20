FROM python:3.11-slim

# Install Stockfish
RUN apt-get update && \
    apt-get install -y stockfish && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

ENV STOCKFISH_PATH=/usr/games/stockfish

EXPOSE 10000

CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]