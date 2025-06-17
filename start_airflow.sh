#!/bin/bash

# Скрипт для запуска Apache Airflow
# Использование: ./start_airflow.sh

# Активация виртуального окружения
source /home/zima/airflow-venv/bin/activate

# Переход в директорию проекта
cd /home/zima/Exam

# Установка переменных окружения
export AIRFLOW_HOME=/home/airflow
export AIRFLOW__CORE__DAGS_FOLDER=/home/zima/Exam/dags

echo "Запуск Apache Airflow..."
echo "Scheduler запускается в фоновом режиме..."

# Запуск scheduler в фоновом режиме
nohup airflow scheduler > scheduler.log 2>&1 &

echo "Scheduler запущен. PID: $!"

# Небольшая пауза для инициализации scheduler
sleep 3

echo "Запуск веб-сервера на порту 8080..."
echo "Веб-интерфейс будет доступен по адресу: http://localhost:8080"
echo "Логин: admin"
echo "Пароль: admin"
echo ""
echo "Для остановки нажмите Ctrl+C"

# Запуск веб-сервера
airflow webserver -p 8080
