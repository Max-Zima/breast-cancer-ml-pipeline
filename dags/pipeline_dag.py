"""
Apache Airflow DAG для пайплайна машинного обучения диагностики рака молочной железы.

Этот модуль определяет DAG для автоматизированного пайплайна обработки данных
и обучения модели машинного обучения для предсказания злокачественности
опухолей молочной железы.
"""

import os
import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

project_path = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, project_path)

# Аргументы по умолчанию для DAG
default_args = {
    "owner": "data-engineer (Zima)",
    "depends_on_past": False,
    "start_date": days_ago(1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "catchup": False,
}

# Создание DAG
dag = DAG(
    "breast_cancer_ml_pipeline",
    default_args=default_args,
    description="Сквозной пайплайн МО для предсказания рака молочной железы",
    schedule_interval=None,  # Только ручной запуск
    max_active_runs=1,
    tags=["ml", "healthcare", "breast-cancer", "classification"],
)


def load_and_analyze_data(**context):
    """Функция задачи для загрузки и анализа данных.

    Args:
        **context: Контекст выполнения Airflow.
    Returns:
        str: Сообщение о завершении анализа данных.

    Raises:
        Exception: При ошибках загрузки или анализа данных.
    """
    try:
        import logging

        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        logger.info("Начинается задача загрузки и анализа данных")

        # Импорт и запуск загрузчика данных
        from etl.data_loader import (  # Загрузка данных
            analyze_data,
            load_breast_cancer_data,
            validate_data_schema,
        )

        df = load_breast_cancer_data("wdbc.data")

        # Валидация схемы
        validate_data_schema(df)

        # Анализ данных
        analysis = analyze_data(df)

        # Сохранение результатов анализа
        os.makedirs("results", exist_ok=True)
        with open("results/data_analysis.txt", "w") as f:
            f.write("=== АНАЛИЗ НАБОРА ДАННЫХ РАКА МОЛОЧНОЙ ЖЕЛЕЗЫ ===\n\n")
            f.write(f"Размер набора данных: {analysis['shape']}\n")
            f.write(
                f"Распределение целевых классов: "
                f"{analysis['target_distribution']}\n"
            )
            f.write(f"Проблемы качества: {analysis['quality_issues']}\n")

        logger.info("Загрузка и анализ данных завершены успешно")
        return "Анализ данных завершен"

    except Exception as e:
        logger.error(f"Ошибка в задаче загрузки данных: {str(e)}")
        raise


def preprocess_data(**context):
    """Функция задачи для предобработки данных.

    Args:
        **context: Контекст выполнения Airflow.

    Returns:
        str: Сообщение о завершении предобработки данных.

    Raises:
        Exception: При ошибках предобработки данных.
    """
    try:
        import logging

        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        logger.info("Начинается задача предобработки данных")

        # Импорт функций предобработки
        import joblib

        from etl.data_loader import load_breast_cancer_data
        from etl.data_preprocessor import (
            prepare_features,
            save_processed_data,
            split_and_scale_data,
        )
        from etl.data_preprocessor import preprocess_data as preprocess_func

        # Загрузка исходных данных
        df = load_breast_cancer_data("wdbc.data")

        # Предобработка данных
        processed_df = preprocess_func(df)

        # Подготовка признаков
        X, y = prepare_features(processed_df)

        # Разделение и масштабирование данных
        X_train, X_test, y_train, y_test, scaler = split_and_scale_data(X, y)

        # Сохранение обработанных данных
        save_processed_data(X_train, X_test, y_train, y_test)

        # Сохранение масштабировщика
        os.makedirs("results", exist_ok=True)
        joblib.dump(scaler, "results/scaler.joblib")

        logger.info("Предобработка данных завершена успешно")
        return "Предобработка данных завершена"

    except Exception as e:
        logger.error(f"Ошибка в задаче предобработки: {str(e)}")
        raise


def train_model(**context):
    """Функция задачи для обучения модели.

    Args:
        **context: Контекст выполнения Airflow.

    Returns:
        str: Сообщение о завершении обучения модели.

    Raises:
        Exception: При ошибках обучения модели.
    """
    try:
        import logging

        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        logger.info("Начинается задача обучения модели")

        # Импорт функций обучения
        import pandas as pd

        from etl.model_trainer import save_model
        from etl.model_trainer import train_model as train_func

        # Загрузка обработанных данных
        X_train = pd.read_csv("results/X_train.csv")
        y_train = pd.read_csv("results/y_train.csv").iloc[:, 0]

        # Определение параметров модели
        model_params = {"solver": "liblinear", "max_iter": 1000, "random_state": 42}

        # Обучение модели
        model = train_func(X_train, y_train, model_params)

        # Сохранение модели
        save_model(model)

        logger.info("Обучение модели завершено успешно")
        return "Обучение модели завершено"

    except Exception as e:
        logger.error(f"Ошибка в задаче обучения: {str(e)}")
        raise


def evaluate_model(**context):
    """Функция задачи для оценки модели.

    Args:
        **context: Контекст выполнения Airflow.

    Returns:
        str: Сообщение о завершении оценки модели.

    Raises:
        Exception: При ошибках оценки модели.
    """
    try:
        import logging

        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        logger.info("Начинается задача оценки модели")

        # Импорт функций оценки
        import joblib
        import pandas as pd

        from etl.model_evaluator import (
            create_evaluation_plots,
            generate_evaluation_report,
            save_metrics,
        )
        from etl.model_evaluator import evaluate_model as eval_func

        # Загрузка тестовых данных и модели
        X_test = pd.read_csv("results/X_test.csv")
        y_test = pd.read_csv("results/y_test.csv").iloc[:, 0]
        model = joblib.load("results/breast_cancer_model.joblib")

        # Оценка модели
        evaluation_results = eval_func(model, X_test, y_test)

        # Сохранение метрик
        save_metrics(evaluation_results)

        # Создание графиков (если библиотеки доступны)
        try:
            create_evaluation_plots(model, X_test, y_test, evaluation_results)
        except ImportError:
            logger.warning("Библиотеки визуализации недоступны - пропуск графиков")

        # Генерация отчета об оценке
        generate_evaluation_report(evaluation_results)

        logger.info("Оценка модели завершена успешно")
        return "Оценка модели завершена"

    except Exception as e:
        logger.error(f"Ошибка в задаче оценки: {str(e)}")
        raise


def upload_to_storage(**context):
    """Функция задачи для загрузки в хранилище.

    Args:
        **context: Контекст выполнения Airflow.

    Returns:
        str: Сообщение о завершении загрузки.

    Raises:
        Exception: При ошибках загрузки в хранилище.
    """
    try:
        import logging

        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        logger.info("Начинается задача загрузки в хранилище")

        # Импорт функций управления хранилищем
        from etl.storage_manager import upload_results

        # Конфигурация для локального хранилища (по умолчанию)
        storage_config = {"type": "local", "base_path": "results"}

        # Проверка переменных окружения
        storage_type = os.getenv("STORAGE_TYPE", "local")

        if storage_type == "dropbox":
            storage_config = {
                "type": "dropbox",
                "access_token": os.getenv("DROPBOX_ACCESS_TOKEN") or "",
            }
        elif storage_type == "gcs":
            storage_config = {
                "type": "gcs",
                "bucket_name": os.getenv("GCS_BUCKET_NAME") or "",
                "credentials_path": os.getenv("GCS_CREDENTIALS_PATH") or "",
            }
        elif storage_type == "s3":
            storage_config = {
                "type": "s3",
                "bucket_name": os.getenv("S3_BUCKET_NAME") or "",
                "access_key": os.getenv("AWS_ACCESS_KEY_ID") or "",
                "secret_key": os.getenv("AWS_SECRET_ACCESS_KEY") or "",
            }

        # Загрузка результатов
        success = upload_results(storage_config)

        if success:
            logger.info("Все результаты загружены успешно")
        else:
            logger.warning("Некоторые файлы не удалось загрузить")

        return "Загрузка в хранилище завершена"

    except Exception as e:
        logger.error(f"Ошибка в задаче загрузки в хранилище: {str(e)}")
        raise


def cleanup_task(**context):
    """Задача очистки (опциональная).

    Args:
        **context: Контекст выполнения Airflow.

    Returns:
        str: Сообщение о завершении очистки.

    Raises:
        Exception: При ошибках очистки.
    """
    try:
        import logging

        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        logger.info("Начинается задача очистки")

        # Создание финального резюме
        summary = {
            "pipeline_run_date": str(datetime.now()),
            "tasks_completed": [
                "data_loading_and_analysis",
                "data_preprocessing",
                "model_training",
                "model_evaluation",
                "storage_upload",
            ],
            "output_files": [
                "breast_cancer_model.joblib",
                "model_metrics.json",
                "evaluation_report.txt",
                "scaler.joblib",
            ],
        }

        # Сохранение резюме
        import json

        with open("results/pipeline_summary.json", "w") as f:
            json.dump(summary, f, indent=2)

        logger.info("Пайплайн завершен успешно")
        return "Очистка завершена"

    except Exception as e:
        logger.error(f"Ошибка в задаче очистки: {str(e)}")
        raise


# Определение задач
data_loading_task = PythonOperator(
    task_id="data_loading_and_analysis",
    python_callable=load_and_analyze_data,
    dag=dag,
    doc_md="""
    ### Задача загрузки и анализа данных
    
    Эта задача выполняет:
    - Загрузку набора данных рака молочной железы из wdbc.data
    - Валидацию схемы данных
    - Первичный анализ данных и проверку качества
    - Генерацию отчета об анализе данных
    """,
)

data_preprocessing_task = PythonOperator(
    task_id="data_preprocessing",
    python_callable=preprocess_data,
    dag=dag,
    doc_md="""
    ### Задача предобработки данных
    
    Эта задача выполняет:
    - Очистку и предобработку данных
    - Подготовку и кодирование признаков
    - Разделение на тренировочную/тестовую выборки со стратификацией
    - Масштабирование признаков с помощью StandardScaler
    - Сохранение обработанных наборов данных
    """,
)

model_training_task = PythonOperator(
    task_id="model_training",
    python_callable=train_model,
    dag=dag,
    doc_md="""    ### Задача обучения модели
    
    Эта задача выполняет:
    - Обучение модели логистической регрессии
    - Конфигурацию гиперпараметров модели
    - Сериализацию и сохранение модели
    """,
)

model_evaluation_task = PythonOperator(
    task_id="model_evaluation",
    python_callable=evaluate_model,
    dag=dag,
    doc_md="""
    ### Задача оценки модели
    
    Эта задача выполняет:
    - Оценку производительности модели на тестовых данных
    - Расчет метрик классификации
    - Генерацию графиков и отчетов оценки
    - Создание ROC-кривой и матрицы ошибок
    """,
)

storage_upload_task = PythonOperator(
    task_id="storage_upload",
    python_callable=upload_to_storage,
    dag=dag,
    doc_md="""
    ### Задача загрузки в хранилище
    
    Эта задача выполняет:
    - Загрузку всех результатов в настроенное хранилище
    - Поддержку локального хранилища, Dropbox, GCS и S3
    - Создание сводки загрузки
    """,
)

cleanup_task_op = PythonOperator(
    task_id="cleanup_and_summary",
    python_callable=cleanup_task,
    dag=dag,
    doc_md="""
    ### Задача очистки и резюме
    
    Эта задача выполняет:
    - Генерацию финального резюме пайплайна
    - Очистку временных файлов (при необходимости)
    - Логирование завершения пайплайна
    """,
)

# Определение зависимостей задач
task_dependencies = (
    data_loading_task
    >> data_preprocessing_task
    >> model_training_task
    >> model_evaluation_task
    >> storage_upload_task
    >> cleanup_task_op
)

# Добавление документации
dag.doc_md = """
# Пайплайн машинного обучения для диагностики рака молочной железы

Этот DAG реализует сквозной пайплайн машинного обучения для предсказания 
рака молочной железы с использованием набора данных Wisconsin Diagnostic 
для диагностики рака молочной железы.

## Этапы пайплайна:

1. **Загрузка и анализ данных**: Загрузка и валидация набора данных, 
   первичный анализ
2. **Предобработка данных**: Очистка данных, обработка пропущенных значений, 
   инженерия признаков, масштабирование
3. **Обучение модели**: Обучение модели логистической регрессии с 
   оптимальными гиперпараметрами
4. **Оценка модели**: Оценка производительности модели с использованием 
   различных метрик и визуализаций
5. **Загрузка в хранилище**: Загрузка результатов в настроенное облачное 
   хранилище или локальную директорию
6. **Очистка**: Генерация финального резюме и выполнение очистки

## Конфигурация:

Пайплайн можно настроить с помощью переменных окружения:
- `STORAGE_TYPE`: local, dropbox, gcs, s3
- Учетные данные облачного хранилища по необходимости

## Мониторинг:

Каждая задача включает всестороннее логирование и обработку ошибок с 
повторными попытками. Неудачные задачи будут повторены до 2 раз с 
задержкой 5 минут.

## Выходные данные:

Пайплайн генерирует:
- Обученную модель (.joblib)
- Метрики оценки (JSON)
- Отчет об оценке (текст)
- Графики визуализации (PNG)
- Масштабировщик данных (.joblib)
- Резюме пайплайна (JSON)
"""
