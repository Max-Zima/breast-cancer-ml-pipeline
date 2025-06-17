#!/usr/bin/env python3
"""
Основной скрипт для запуска пайплайна машинного обучения диагностики рака молочной железы.

Этот модуль предоставляет функции для выполнения полного цикла машинного обучения,
включая загрузку данных, предобработку, обучение модели, оценку и сохранение результатов.

Обновления:
- Универсальная поддержка Windows, Linux, macOS
- Автоматическое определение операционной системы
- Добавлена поддержка WSL окружения для разработчика
- Интеграция с Apache Airflow 2.8+
- Автоматические скрипты запуска/остановки Airflow
- Решение проблем совместимости провайдеров
- Улучшенная обработка ошибок БД

Универсальный запуск:
1. make quick-setup-universal (автонастройка)
2. start_airflow.bat (Windows) или ./start_airflow.sh (Linux/macOS)
3. Откройте http://localhost:8080
4. Запустите DAG breast_cancer_ml_pipeline

Для разработчика (WSL):
1. Используйте ./start_airflow.sh в WSL
2. Откройте http://localhost:8080
3. Запустите DAG breast_cancer_ml_pipeline
"""

import logging
import os
import sys
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_complete_pipeline():
    """Запуск полного пайплайна машинного обучения.

    Returns:
        bool: True если пайплайн выполнен успешно, False в противном случае.
    """
    try:
        logger.info("=" * 60)
        logger.info("ЗАПУСК ПАЙПЛАЙНА МО ДЛЯ ДИАГНОСТИКИ РАКА МОЛОЧНОЙ ЖЕЛЕЗЫ")
        logger.info("=" * 60)

        start_time = datetime.now()

        # Шаг 1: Загрузка и анализ данных
        logger.info("\n🔄 Шаг 1: Загрузка и анализ данных...")
        from etl.data_loader import main as load_main

        load_main()
        logger.info("✅ Загрузка данных завершена")

        # Шаг 2: Предобработка данных
        logger.info("\n🔄 Шаг 2: Предобработка данных...")
        from etl.data_preprocessor import main as preprocess_main

        preprocess_main()
        logger.info("✅ Предобработка данных завершена")

        # Шаг 3: Обучение модели
        logger.info("\n🔄 Шаг 3: Обучение модели...")
        from etl.model_trainer import main as train_main

        train_main()
        logger.info("✅ Обучение модели завершено")

        # Шаг 4: Оценка модели
        logger.info("\n🔄 Шаг 4: Оценка модели...")
        from etl.model_evaluator import main as evaluate_main

        evaluate_main()
        logger.info("✅ Оценка модели завершена")

        # Шаг 5: Загрузка результатов
        logger.info("\n🔄 Шаг 5: Загрузка результатов...")
        from etl.storage_manager import main as storage_main

        storage_main()
        logger.info("✅ Загрузка результатов завершена")

        # Расчет общего времени выполнения
        end_time = datetime.now()
        duration = end_time - start_time

        logger.info("\n" + "=" * 60)
        logger.info("🎉 ПАЙПЛАЙН ВЫПОЛНЕН УСПЕШНО!")
        logger.info(f"⏱️  Общее время выполнения: {duration}")
        logger.info(f"📊 Результаты сохранены в: {os.path.abspath('results')}")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"❌ Сбой пайплайна: {str(e)}")
        logger.exception("Полные детали ошибки:")
        return False


def show_results_summary():
    """Отображение сводки сгенерированных результатов."""
    results_dir = "results"
    if os.path.exists(results_dir):
        logger.info("\n📋 Сгенерированные файлы:")
        for file in os.listdir(results_dir):
            file_path = os.path.join(results_dir, file)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                logger.info(f"  📄 {file} ({size} байт)")
    else:
        logger.warning("Директория результатов не найдена")


def check_dependencies():
    """Проверка установки необходимых зависимостей.

    Returns:
        bool: True если все зависимости установлены, False в противном случае.
    """
    required_modules = ["pandas", "numpy", "sklearn", "joblib"]

    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
            logger.info(f"✅ {module} доступен")
        except ImportError:
            missing_modules.append(module)
            logger.error(f"❌ {module} отсутствует")

    if missing_modules:
        logger.error(f"Отсутствующие модули: {missing_modules}")
        logger.info("Установите с помощью: pip install -r requirements.txt")
        return False

    return True


def main():
    """Основная функция."""
    logger.info("🚀 Запуск пайплайна МО для диагностики рака молочной железы")

    # Проверка зависимостей
    if not check_dependencies():
        logger.error("Проверка зависимостей не пройдена")
        sys.exit(1)

    # Проверка файла данных
    if not os.path.exists("wdbc.data"):
        logger.error("Файл данных 'wdbc.data' не найден")
        sys.exit(1)    # Создание директорий
    os.makedirs("results", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    # Запуск пайплайна
    success = run_complete_pipeline()

    if success:
        show_results_summary()
        logger.info(
            "🎯 Для просмотра детальных результатов проверьте директорию results/"
        )
        logger.info("=" * 60)
        logger.info("🌐 ВАРИАНТЫ ЗАПУСКА AIRFLOW:")
        logger.info("  Универсальный (любая ОС):")
        logger.info("    1. make quick-setup-universal")
        logger.info("    2. start_airflow.bat (Windows) или ./start_airflow.sh (Linux/macOS)")
        logger.info("  Для разработчика (WSL): ./start_airflow.sh")
        logger.info("🔧 Остановка Airflow:")
        logger.info("    stop_airflow.bat (Windows) или ./stop_airflow.sh (Linux/macOS/WSL)")
        logger.info("📊 Веб-интерфейс Airflow: http://localhost:8080 (admin/admin)")
        logger.info("=" * 60)
    else:
        logger.error("Выполнение пайплайна завершилось неудачей")
        sys.exit(1)


if __name__ == "__main__":
    main()
