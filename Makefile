.PHONY: help install clean test run-pipeline run-data-loader run-preprocessor run-trainer run-evaluator setup-env airflow-init airflow-start airflow-stop wsl-setup wsl-test setup-universal airflow-setup-universal

# Цель по умолчанию
help:	@echo "Доступные команды:"
	@echo "  install         - Установить все зависимости"
	@echo "  setup-env       - Настроить переменные окружения"
	@echo "  clean           - Очистить сгенерированные файлы"
	@echo "  test            - Запустить тесты (если доступны)"
	@echo ""
	@echo "  run-pipeline    - Запустить полный пайплайн автономно"
	@echo "  run-data-loader - Запустить модуль загрузки данных"
	@echo "  run-preprocessor- Запустить модуль предобработки данных"
	@echo "  run-trainer     - Запустить модуль обучения модели"
	@echo "  run-evaluator   - Запустить модуль оценки модели"
	@echo ""
	@echo "  === УНИВЕРСАЛЬНАЯ НАСТРОЙКА ==="
	@echo "  setup-universal      - Универсальная настройка для любой системы"
	@echo "  airflow-setup-universal - Универсальная настройка Airflow"
	@echo "  create-venv         - Создать виртуальное окружение"
	@echo "  install-airflow     - Установить Apache Airflow"
	@echo ""
	@echo "  === WSL СПЕЦИФИЧНЫЕ (для разработчика) ==="
	@echo "  airflow-init    - Инициализировать базу данных Airflow (WSL)"
	@echo "  airflow-start   - Запустить веб-сервер и планировщик Airflow (WSL)"
	@echo "  airflow-stop    - Остановить сервисы Airflow (WSL)"
	@echo "  wsl-setup       - Настроить окружение в WSL"
	@echo "  wsl-test        - Тестировать модули в WSL"

# Установка зависимостей
install:
	pip install -r requirements.txt

# Настройка окружения
setup-env:
	@if not exist .env (copy .env.example .env && echo "Создан файл .env из шаблона. Пожалуйста, отредактируйте его с вашими настройками.")
	@if exist .env (echo "Файл .env уже существует")

# Очистка сгенерированных файлов
clean:
	@if exist results rmdir /s /q results
	@if exist logs rmdir /s /q logs
	@if exist __pycache__ rmdir /s /q __pycache__
	@for /r %%i in (*.pyc) do del "%%i" 2>nul
	@for /r %%i in (__pycache__) do if exist "%%i" rmdir /s /q "%%i" 2>nul
	@echo "Очищены сгенерированные файлы"

# Запуск полного пайплайна автономно
run-pipeline: setup-env
	python -m etl.data_loader
	python -m etl.data_preprocessor
	python -m etl.model_trainer
	python -m etl.model_evaluator
	python -m etl.storage_manager

# Запуск отдельных модулей
run-data-loader: setup-env
	python -m etl.data_loader

run-preprocessor: setup-env
	python -m etl.data_preprocessor

run-trainer: setup-env
	python -m etl.model_trainer

run-evaluator: setup-env
	python -m etl.model_evaluator

# Тестирование компонентов пайплайна
test:
	@echo "Запуск базовых тестов валидации..."
	@python -c "import etl.data_loader; print('✓ Загрузчик данных импортируется успешно')"
	@python -c "import etl.data_preprocessor; print('✓ Предобработчик данных импортируется успешно')"
	@python -c "import etl.model_trainer; print('✓ Обучатель модели импортируется успешно')"
	@python -c "import etl.model_evaluator; print('✓ Оценщик модели импортируется успешно')"
	@python -c "import etl.storage_manager; print('✓ Менеджер хранилища импортируется успешно')"
	@echo "✓ Все модули импортируются успешно"

# === УНИВЕРСАЛЬНАЯ НАСТРОЙКА ДЛЯ ЛЮБОЙ СИСТЕМЫ ===

# Определение операционной системы
UNAME_S := $(shell uname -s 2>/dev/null || echo "Windows")
UNAME_M := $(shell uname -m 2>/dev/null || echo "unknown")

# Определение Python команды
PYTHON := $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null || echo "python")
PIP := $(shell command -v pip3 2>/dev/null || command -v pip 2>/dev/null || echo "pip")

# Определение виртуального окружения
ifeq ($(UNAME_S),Linux)
    VENV_DIR := venv
    VENV_ACTIVATE := $(VENV_DIR)/bin/activate
    AIRFLOW_HOME_DEFAULT := $(HOME)/airflow
else ifeq ($(UNAME_S),Darwin)
    VENV_DIR := venv
    VENV_ACTIVATE := $(VENV_DIR)/bin/activate
    AIRFLOW_HOME_DEFAULT := $(HOME)/airflow
else
    VENV_DIR := venv
    VENV_ACTIVATE := $(VENV_DIR)/Scripts/activate
    AIRFLOW_HOME_DEFAULT := $(CURDIR)/airflow_home
endif

# Универсальная настройка проекта
setup-universal:
	@echo "=== Универсальная настройка проекта ==="
	@echo "Операционная система: $(UNAME_S)"
	@echo "Архитектура: $(UNAME_M)"
	@echo "Python: $(PYTHON)"
	@echo "Pip: $(PIP)"
	@echo ""
	@$(MAKE) create-venv
	@$(MAKE) install-requirements
	@$(MAKE) setup-env
	@echo ""
	@echo "✅ Базовая настройка завершена!"
	@echo "Следующий шаг: make airflow-setup-universal"

# Создание виртуального окружения
create-venv:
	@echo "Создание виртуального окружения..."
	@if [ ! -d "$(VENV_DIR)" ]; then \
		$(PYTHON) -m venv $(VENV_DIR); \
		echo "✅ Виртуальное окружение создано: $(VENV_DIR)"; \
	else \
		echo "✅ Виртуальное окружение уже существует: $(VENV_DIR)"; \
	fi

# Установка зависимостей в виртуальное окружение
install-requirements:
	@echo "Установка зависимостей..."
ifeq ($(UNAME_S),Windows_NT)
	@$(VENV_DIR)\Scripts\pip install -r requirements.txt
else
	@. $(VENV_ACTIVATE) && pip install -r requirements.txt
endif
	@echo "✅ Зависимости установлены"

# Установка Apache Airflow
install-airflow:
	@echo "Установка Apache Airflow..."
ifeq ($(UNAME_S),Windows_NT)
	@$(VENV_DIR)\Scripts\pip install apache-airflow==2.8.0
	@$(VENV_DIR)\Scripts\pip install "apache-airflow-providers-common-compat<1.7.0"
else
	@. $(VENV_ACTIVATE) && pip install apache-airflow==2.8.0
	@. $(VENV_ACTIVATE) && pip install "apache-airflow-providers-common-compat<1.7.0"
endif
	@echo "✅ Apache Airflow установлен"

# Универсальная настройка Airflow
airflow-setup-universal:
	@echo "=== Универсальная настройка Apache Airflow ==="
	@$(MAKE) install-airflow
	@$(MAKE) create-airflow-scripts
	@$(MAKE) init-airflow-db
	@echo ""
	@echo "✅ Airflow настроен для вашей системы!"
	@echo ""
	@echo "Следующие шаги:"
	@echo "1. Запустите: ./start_airflow.sh (Linux/macOS) или start_airflow.bat (Windows)"
	@echo "2. Откройте: http://localhost:8080"
	@echo "3. Логин: admin, Пароль: admin"

# Создание скриптов запуска для текущей ОС
create-airflow-scripts:
	@echo "Создание скриптов запуска..."
ifeq ($(UNAME_S),Windows_NT)
	@$(MAKE) create-windows-scripts
else
	@$(MAKE) create-unix-scripts
endif

# Инициализация базы данных Airflow
init-airflow-db:
	@echo "Инициализация базы данных Airflow..."
ifeq ($(UNAME_S),Windows_NT)
	@set AIRFLOW_HOME=$(AIRFLOW_HOME_DEFAULT) && set AIRFLOW__CORE__DAGS_FOLDER=$(CURDIR)/dags && $(VENV_DIR)\Scripts\airflow db upgrade
	@set AIRFLOW_HOME=$(AIRFLOW_HOME_DEFAULT) && $(VENV_DIR)\Scripts\airflow users create --username admin --firstname Admin --lastname User --role Admin --email admin@example.com --password admin 2>nul || echo "Пользователь admin уже существует"
else
	@mkdir -p $(AIRFLOW_HOME_DEFAULT)
	@export AIRFLOW_HOME=$(AIRFLOW_HOME_DEFAULT) && export AIRFLOW__CORE__DAGS_FOLDER=$(CURDIR)/dags && . $(VENV_ACTIVATE) && airflow db upgrade
	@export AIRFLOW_HOME=$(AIRFLOW_HOME_DEFAULT) && . $(VENV_ACTIVATE) && airflow users create --username admin --firstname Admin --lastname User --role Admin --email admin@example.com --password admin 2>/dev/null || echo "Пользователь admin уже существует"
endif
	@echo "✅ База данных Airflow инициализирована"
airflow-init: install setup-env
	@echo "Инициализация Airflow..."
	wsl -e bash -c "cd /home/zima/Exam && source /home/zима/airflow-venv/bin/activate && export AIRFLOW_HOME=/home/airflow && export AIRFLOW__CORE__DAGS_FOLDER=/home/zима/Exam/dags && airflow db upgrade && airflow users create --username admin --firstname Admin --lastname User --role Admin --email admin@example.com --password admin"

airflow-start: setup-env
	@echo "Запуск Airflow через WSL..."
	@echo "Используйте скрипт start_airflow.sh для удобного запуска"
	@echo "Или выполните: wsl -e bash -c './start_airflow.sh'"
	@echo "Веб-интерфейс: http://localhost:8080"
	@echo "Логин: admin, Пароль: admin"

airflow-stop:
	@echo "Остановка сервисов Airflow..."
	wsl -e bash -c "./stop_airflow.sh" 2>nul || echo "Используйте ./stop_airflow.sh в WSL терминале"

# Команды для WSL
wsl-setup:
	@echo "Настройка окружения в WSL..."
	wsl -e bash -c "cd /home/zima/Exam && source /home/zima/airflow-venv/bin/activate && export AIRFLOW_HOME=/home/airflow && export AIRFLOW__CORE__DAGS_FOLDER=/home/zима/Exam/dags && echo 'Окружение настроено'"

wsl-test:
	@echo "Тестирование модулей в WSL..."
	wsl -e bash -c "cd /home/zима/Exam && source /home/zима/airflow-venv/bin/activate && python -c 'import etl.data_loader; print(\"✓ data_loader импортируется\")' && python -c 'import etl.data_preprocessor; print(\"✓ data_preprocessor импортируется\")' && python -c 'import etl.model_trainer; print(\"✓ model_trainer импортируется\")' && python -c 'import etl.model_evaluator; print(\"✓ model_evaluator импортируется\")' && python -c 'import etl.storage_manager; print(\"✓ storage_manager импортируется\")'"

# Помощники для разработки
lint:
	@echo "Запуск проверки качества кода..."
	flake8 etl/ --max-line-length=88 --ignore=E203,W503 || echo "Flake8 не установлен"
	black etl/ --check || echo "Black не установлен"

format:
	@echo "Форматирование кода..."
	black etl/ || echo "Black не установлен"

# Проверка зависимостей
check-deps:
	@echo "Проверка зависимостей..."
	@python -c "import pandas; print(f'✓ pandas {pandas.__version__}')" 2>nul || echo "✗ pandas не установлен"
	@python -c "import sklearn; print(f'✓ scikit-learn {sklearn.__version__}')" 2>nul || echo "✗ scikit-learn не установлен"
	@python -c "import numpy; print(f'✓ numpy {numpy.__version__}')" 2>nul || echo "✗ numpy не установлен"
	@python -c "import joblib; print(f'✓ joblib {joblib.__version__}')" 2>nul || echo "✗ joblib не установлен"

# Быстрая настройка для нового окружения
quick-setup: install setup-env
	@echo "Быстрая настройка завершена!"
	@echo "Следующие шаги:"
	@echo "1. Отредактируйте файл .env с вашими настройками"
	@echo "2. Запустите 'make run-pipeline' для тестирования пайплайна"
	@echo "3. Для WSL: запустите 'make wsl-setup' для настройки окружения"
	@echo "4. Для Airflow: запустите 'make airflow-init' для настройки Airflow"
	@echo "5. Для запуска Airflow: используйте './start_airflow.sh' в WSL"

# Универсальная быстрая настройка
quick-setup-universal: setup-universal airflow-setup-universal
	@echo ""
	@echo "🎉 Полная универсальная настройка завершена!"
	@echo ""
	@echo "Теперь вы можете:"
	@echo "1. Запустить пайплайн: make run-pipeline"
	@echo "2. Запустить Airflow:"
ifeq ($(UNAME_S),Windows_NT)
	@echo "   - Windows: start_airflow.bat"
else
	@echo "   - Linux/macOS: ./start_airflow.sh"
endif
	@echo "3. Открыть веб-интерфейс: http://localhost:8080"
	@echo "4. Логин: admin, Пароль: admin"

# Универсальная проверка статуса
check-system:
	@echo "=== Информация о системе ==="
	@echo "ОС: $(UNAME_S)"
	@echo "Архитектура: $(UNAME_M)"
	@echo "Python: $(PYTHON)"
	@echo "Pip: $(PIP)"
	@echo "Виртуальное окружение: $(VENV_DIR)"
	@echo "Airflow Home: $(AIRFLOW_HOME_DEFAULT)"
	@echo ""
	@echo "=== Проверка файлов ==="
	@if [ -d "$(VENV_DIR)" ]; then echo "✅ Виртуальное окружение найдено"; else echo "❌ Виртуальное окружение не найдено"; fi
	@if [ -f "requirements.txt" ]; then echo "✅ requirements.txt найден"; else echo "❌ requirements.txt не найден"; fi
	@if [ -d "dags" ]; then echo "✅ Папка dags найдена"; else echo "❌ Папка dags не найдена"; fi
	@if [ -f "wdbc.data" ]; then echo "✅ Файл данных найден"; else echo "❌ Файл данных не найден"; fi

# Дополнительные команды для диагностики
check-wsl:
	@echo "Проверка доступности WSL..."
	wsl --list --verbose
	
check-airflow-status:
	@echo "Проверка статуса Airflow..."
	wsl -e bash -c "ps aux | grep airflow | grep -v grep" || echo "Airflow не запущен"

fix-airflow-db:
	@echo "Исправление проблем с базой данных Airflow..."
	wsl -e bash -c "cd /home/zima/Exam && source /home/zima/airflow-venv/bin/activate && export AIRFLOW_HOME=/home/airflow && airflow db upgrade"

# Создание Unix скриптов (Linux/macOS)
create-unix-scripts:
	@echo "Создание Unix скриптов..."
	@echo '#!/bin/bash' > start_airflow.sh
	@echo '# Автоматический запуск Apache Airflow' >> start_airflow.sh
	@echo '' >> start_airflow.sh
	@echo 'SCRIPT_DIR="$$(cd "$$(dirname "$${BASH_SOURCE[0]}")" && pwd)"' >> start_airflow.sh
	@echo 'cd "$$SCRIPT_DIR"' >> start_airflow.sh
	@echo '' >> start_airflow.sh
	@echo '# Активация виртуального окружения' >> start_airflow.sh
	@echo 'if [ -f "$(VENV_ACTIVATE)" ]; then' >> start_airflow.sh
	@echo '    source $(VENV_ACTIVATE)' >> start_airflow.sh
	@echo 'else' >> start_airflow.sh
	@echo '    echo "❌ Виртуальное окружение не найдено: $(VENV_ACTIVATE)"' >> start_airflow.sh
	@echo '    echo "Запустите: make setup-universal"' >> start_airflow.sh
	@echo '    exit 1' >> start_airflow.sh
	@echo 'fi' >> start_airflow.sh
	@echo '' >> start_airflow.sh
	@echo '# Установка переменных окружения' >> start_airflow.sh
	@echo 'export AIRFLOW_HOME=$(AIRFLOW_HOME_DEFAULT)' >> start_airflow.sh
	@echo 'export AIRFLOW__CORE__DAGS_FOLDER="$$SCRIPT_DIR/dags"' >> start_airflow.sh
	@echo '' >> start_airflow.sh
	@echo 'echo "🚀 Запуск Apache Airflow..."' >> start_airflow.sh
	@echo 'echo "Scheduler запускается в фоновом режиме..."' >> start_airflow.sh
	@echo '' >> start_airflow.sh
	@echo '# Запуск scheduler в фоновом режиме' >> start_airflow.sh
	@echo 'nohup airflow scheduler > scheduler.log 2>&1 &' >> start_airflow.sh
	@echo 'echo "Scheduler запущен. PID: $$!"' >> start_airflow.sh
	@echo '' >> start_airflow.sh
	@echo '# Пауза для инициализации' >> start_airflow.sh
	@echo 'sleep 3' >> start_airflow.sh
	@echo '' >> start_airflow.sh
	@echo 'echo "🌐 Запуск веб-сервера на порту 8080..."' >> start_airflow.sh
	@echo 'echo "Веб-интерфейс: http://localhost:8080"' >> start_airflow.sh
	@echo 'echo "Логин: admin, Пароль: admin"' >> start_airflow.sh
	@echo 'echo "Для остановки нажмите Ctrl+C"' >> start_airflow.sh
	@echo '' >> start_airflow.sh
	@echo 'airflow webserver -p 8080' >> start_airflow.sh
	@chmod +x start_airflow.sh
	@echo '' > stop_airflow.sh
	@echo '#!/bin/bash' > stop_airflow.sh
	@echo '# Остановка Apache Airflow' >> stop_airflow.sh
	@echo '' >> stop_airflow.sh
	@echo 'echo "🛑 Остановка Apache Airflow..."' >> stop_airflow.sh
	@echo '' >> stop_airflow.sh
	@echo '# Остановка процессов' >> stop_airflow.sh
	@echo 'pkill -f "airflow scheduler" || true' >> stop_airflow.sh
	@echo 'pkill -f "airflow webserver" || true' >> stop_airflow.sh
	@echo 'pkill -f "gunicorn" || true' >> stop_airflow.sh
	@echo '' >> stop_airflow.sh
	@echo 'echo "✅ Процессы Airflow остановлены"' >> stop_airflow.sh
	@echo '' >> stop_airflow.sh
	@echo '# Проверка оставшихся процессов' >> stop_airflow.sh
	@echo 'REMAINING=$$(pgrep -f airflow || true)' >> stop_airflow.sh
	@echo 'if [ -n "$$REMAINING" ]; then' >> stop_airflow.sh
	@echo '    echo "⚠️  Некоторые процессы все еще запущены:"' >> stop_airflow.sh
	@echo '    ps aux | grep airflow | grep -v grep' >> stop_airflow.sh
	@echo '    echo "Для принудительной остановки: pkill -9 -f airflow"' >> stop_airflow.sh
	@echo 'else' >> stop_airflow.sh
	@echo '    echo "✅ Все процессы успешно остановлены"' >> stop_airflow.sh
	@echo 'fi' >> stop_airflow.sh
	@chmod +x stop_airflow.sh
	@echo "✅ Unix скрипты созданы: start_airflow.sh, stop_airflow.sh"

# Создание Windows скриптов
create-windows-scripts:
	@echo "Создание Windows скриптов..."
	@echo '@echo off' > start_airflow.bat
	@echo 'REM Автоматический запуск Apache Airflow для Windows' >> start_airflow.bat
	@echo '' >> start_airflow.bat
	@echo 'cd /d "%~dp0"' >> start_airflow.bat
	@echo '' >> start_airflow.bat
	@echo 'REM Проверка виртуального окружения' >> start_airflow.bat
	@echo 'if not exist "$(VENV_DIR)\Scripts\activate.bat" (' >> start_airflow.bat
	@echo '    echo ❌ Виртуальное окружение не найдено: $(VENV_DIR)' >> start_airflow.bat
	@echo '    echo Запустите: make setup-universal' >> start_airflow.bat
	@echo '    pause' >> start_airflow.bat
	@echo '    exit /b 1' >> start_airflow.bat
	@echo ')' >> start_airflow.bat
	@echo '' >> start_airflow.bat
	@echo 'REM Активация виртуального окружения' >> start_airflow.bat
	@echo 'call $(VENV_DIR)\Scripts\activate.bat' >> start_airflow.bat
	@echo '' >> start_airflow.bat
	@echo 'REM Установка переменных окружения' >> start_airflow.bat
	@echo 'set AIRFLOW_HOME=$(AIRFLOW_HOME_DEFAULT)' >> start_airflow.bat
	@echo 'set AIRFLOW__CORE__DAGS_FOLDER=%cd%\dags' >> start_airflow.bat
	@echo '' >> start_airflow.bat
	@echo 'echo 🚀 Запуск Apache Airflow...' >> start_airflow.bat
	@echo 'echo Веб-интерфейс: http://localhost:8080' >> start_airflow.bat
	@echo 'echo Логин: admin, Пароль: admin' >> start_airflow.bat
	@echo 'echo.' >> start_airflow.bat
	@echo 'echo Для остановки закройте это окно или нажмите Ctrl+C' >> start_airflow.bat
	@echo 'echo.' >> start_airflow.bat
	@echo '' >> start_airflow.bat
	@echo 'REM Запуск scheduler в отдельном окне' >> start_airflow.bat
	@echo 'start "Airflow Scheduler" cmd /k "set AIRFLOW_HOME=$(AIRFLOW_HOME_DEFAULT) && set AIRFLOW__CORE__DAGS_FOLDER=%cd%\dags && $(VENV_DIR)\Scripts\airflow scheduler"' >> start_airflow.bat
	@echo '' >> start_airflow.bat
	@echo 'REM Запуск webserver' >> start_airflow.bat
	@echo 'airflow webserver -p 8080' >> start_airflow.bat
	@echo '' > stop_airflow.bat
	@echo '@echo off' > stop_airflow.bat
	@echo 'REM Остановка Apache Airflow для Windows' >> stop_airflow.bat
	@echo '' >> stop_airflow.bat
	@echo 'echo 🛑 Остановка Apache Airflow...' >> stop_airflow.bat
	@echo '' >> stop_airflow.bat
	@echo 'REM Остановка процессов' >> stop_airflow.bat
	@echo 'taskkill /f /im python.exe /fi "WINDOWTITLE eq Airflow*" 2>nul' >> stop_airflow.bat
	@echo 'taskkill /f /im cmd.exe /fi "WINDOWTITLE eq Airflow*" 2>nul' >> stop_airflow.bat
	@echo '' >> stop_airflow.bat
	@echo 'echo ✅ Процессы Airflow остановлены' >> stop_airflow.bat
	@echo 'pause' >> stop_airflow.bat
	@echo "✅ Windows скрипты созданы: start_airflow.bat, stop_airflow.bat"

# === КОМАНДЫ ДЛЯ КОНКРЕТНОЙ СИСТЕМЫ РАЗРАБОТЧИКА (WSL) ===

# Диагностика и устранение неполадок
diagnose-airflow: check-env
	@echo "=== Диагностика Airflow ==="
	@echo "Проверка процессов Airflow:"
ifeq ($(DETECTED_OS),Windows)
	wsl -e bash -c "ps aux | grep airflow | grep -v grep || echo 'Процессы Airflow не найдены'"
else
	ps aux | grep airflow | grep -v grep || echo "Процессы Airflow не найдены"
endif
	@echo ""
	@echo "Конфигурация Airflow:"
ifeq ($(DETECTED_OS),Windows)
	wsl -e bash -c "source $(VENV_PATH)/bin/activate && airflow config get-value core executor"
	wsl -e bash -c "source $(VENV_PATH)/bin/activate && airflow config get-value core dags_folder"
else
	$(VENV_ACTIVATE) && airflow config get-value core executor
	$(VENV_ACTIVATE) && airflow config get-value core dags_folder
endif

fix-executor-sqlite: check-env
	@echo "=== Исправление конфигурации executor для SQLite ==="
ifeq ($(DETECTED_OS),Windows)
	wsl -e bash -c "sed -i 's/executor = LocalExecutor/executor = SequentialExecutor/' ~/airflow/airflow.cfg"
	wsl -e bash -c "sed -i 's|dags_folder = /home/.*airflow/dags|dags_folder = $(WSL_PROJECT_DIR)/dags|' ~/airflow/airflow.cfg"
else
	sed -i 's/executor = LocalExecutor/executor = SequentialExecutor/' ~/airflow/airflow.cfg
	sed -i 's|dags_folder = .*/airflow/dags|dags_folder = $(PROJECT_DIR)/dags|' ~/airflow/airflow.cfg
endif
	@echo "Конфигурация обновлена для работы с SQLite"

unpause-dag: check-env
	@echo "=== Включение DAG ==="
ifeq ($(DETECTED_OS),Windows)
	wsl -e bash -c "source $(VENV_PATH)/bin/activate && cd $(WSL_PROJECT_DIR) && airflow dags unpause breast_cancer_ml_pipeline"
else
	$(VENV_ACTIVATE) && airflow dags unpause breast_cancer_ml_pipeline
endif

trigger-dag: check-env
	@echo "=== Принудительный запуск DAG ==="
ifeq ($(DETECTED_OS),Windows)
	wsl -e bash -c "source $(VENV_PATH)/bin/activate && cd $(WSL_PROJECT_DIR) && airflow dags trigger breast_cancer_ml_pipeline"
else
	$(VENV_ACTIVATE) && airflow dags trigger breast_cancer_ml_pipeline
endif

check-dag-status: check-env
	@echo "=== Статус DAG ==="
ifeq ($(DETECTED_OS),Windows)
	wsl -e bash -c "source $(VENV_PATH)/bin/activate && cd $(WSL_PROJECT_DIR) && airflow dags list-runs -d breast_cancer_ml_pipeline --limit 5"
else
	$(VENV_ACTIVATE) && airflow dags list-runs -d breast_cancer_ml_pipeline --limit 5
endif

stop-airflow: check-env
	@echo "=== Остановка всех процессов Airflow ==="
ifeq ($(DETECTED_OS),Windows)
	wsl -e bash -c "pkill -f airflow || echo 'Процессы Airflow уже остановлены'"
else
	pkill -f airflow || echo "Процессы Airflow уже остановлены"
endif

clean-defunct: check-env
	@echo "=== Очистка defunct процессов ==="
ifeq ($(DETECTED_OS),Windows)
	wsl -e bash -c "pkill -f 'airflow worker' || echo 'Defunct процессы очищены'"
else
	pkill -f "airflow worker" || echo "Defunct процессы очищены"
endif

quick-fix: stop-airflow clean-defunct fix-executor-sqlite
	@echo "=== Быстрое исправление проблем Airflow ==="
	@echo "Обновление базы данных..."
ifeq ($(DETECTED_OS),Windows)
	wsl -e bash -c "source $(VENV_PATH)/bin/activate && cd $(WSL_PROJECT_DIR) && airflow db upgrade"
else
	$(VENV_ACTIVATE) && airflow db upgrade
endif
	@echo "Быстрое исправление завершено. Теперь запустите: make start-airflow"
