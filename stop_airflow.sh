#!/bin/bash

# Скрипт для остановки Apache Airflow
# Использование: ./stop_airflow.sh

echo "Остановка Apache Airflow..."

# Остановка процессов Airflow
pkill -f "airflow scheduler"
pkill -f "airflow webserver"
pkill -f "gunicorn"

echo "Процессы Airflow остановлены."

# Проверка оставшихся процессов
REMAINING=$(pgrep -f airflow || true)
if [ -n "$REMAINING" ]; then
    echo "Внимание: некоторые процессы Airflow все еще запущены:"
    ps aux | grep airflow | grep -v grep
    echo "Для принудительной остановки выполните: pkill -9 -f airflow"
else
    echo "Все процессы Airflow успешно остановлены."
fi
