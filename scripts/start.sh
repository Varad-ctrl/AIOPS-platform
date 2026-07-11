#!/usr/bin/env bash
# Bring up the full Phase 1 stack (Postgres + FastAPI + React) with one command.
set -e

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "No .env found - copying from .env.example"
  cp .env.example .env
fi

echo "Building and starting containers..."
docker compose up --build
