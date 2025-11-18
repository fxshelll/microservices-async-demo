#!/bin/sh
echo "Aguardando RabbitMQ em $RABBITMQ_URL..."
until nc -z rabbitmq 5672; do
  sleep 1
done
echo "RabbitMQ está pronto. Iniciando serviço..."
exec "$@"

