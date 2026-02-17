#!/usr/bin/env bash
set -euo pipefail
DC="docker compose -f docker/compose.yml --env-file .env"

menu() {
  echo ""
  echo "HELIX menu"
  echo "1) up (build)"
  echo "2) down"
  echo "3) delete all containers"
  echo "4) restart core"
  echo "41) restart web"
  echo "5) logs core"
  echo "6) logs web"
  echo "7) status"
  echo "8) rebuild web"
  echo "9) rebuild core"
  echo "51) shell core"
  echo "52) ssh staging"
  echo "0) exit"
  echo -n "> "
}

while true; do
  menu
  read -r choice
  case "$choice" in
    1)
        $DC up -d --build
        for i in {1..60}; do
          if $DC ps -q postgres >/dev/null 2>&1 && \
             $DC exec -T postgres pg_isready -U postgres -d helix >/dev/null 2>&1; then
            break
          fi
          sleep 2
        done
        for i in {1..20}; do
          if $DC exec -T helix-core alembic upgrade head; then
            break
          fi
          sleep 2
        done
        ;;
    2) $DC down ;;
    3) docker stop $(docker ps -a -q) && docker rm $(docker ps -a -q) && docker rmi $(docker images -a -q) && docker network prune -f && docker volume rm $(docker volume ls -q) ;;
    4) $DC restart helix-core ;;
    41) $DC restart helix-web ;;
    5) $DC logs -f --tail=200 helix-core ;;
    6) $DC logs -f --tail=200 helix-web ;;
    7) $DC ps ;;
    8) $DC build --no-cache helix-web ;;
    9) $DC build --no-cache helix-core ;;
    51) docker exec -it helix-core bash ;;
    52)
            echo "🔌 Подключение к staging серверу..."
            ssh root@109.123.252.5
            ;;
    0) exit 0 ;;
    *) echo "Unknown option" ;;
  esac
done
