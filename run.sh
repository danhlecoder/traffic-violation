#!/usr/bin/env bash
set -euo pipefail

COMPOSE=${COMPOSE:-docker-compose}

echo "Building images..."
$COMPOSE build

echo "Starting services..."
$COMPOSE up
