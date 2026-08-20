FROM python:3.12-slim

# git n'est là que parce que le CLI embarqué s'en sert pour ses checkpoints.
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    WORKSPACE_ROOT=/data/sessions

COPY requirements.txt .
RUN pip install -r requirements.txt

# La skill est installée au niveau "utilisateur" : n'importe quel dossier de
# session la voit, sans recopier 6 Mo de templates par conversation.
COPY skill/ /root/.claude/skills/tribe-design-rituals/

COPY app/ ./app/

RUN mkdir -p /data/sessions
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
