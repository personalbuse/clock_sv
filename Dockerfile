FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    alsa-utils \
    libasound2 \
    portaudio19-dev \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r appuser && useradd -r -g appuser -G audio appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY config/asound.conf /etc/asound.conf
COPY . .

RUN chmod +x scripts/entrypoint.sh scripts/check_audio.sh

USER appuser

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["scripts/entrypoint.sh"]
