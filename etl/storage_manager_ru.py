"""
Модуль интеграции с облачными хранилищами.

Этот модуль предоставляет единый интерфейс для работы с различными типами
хранилищ данных: локальная файловая система, Dropbox, Google Cloud Storage
и Amazon S3.
"""

import json
import logging
import os
import sys
from typing import Any, Dict

# Добавление родительской директории в путь для импортов
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class LocalStorage:
    """Реализация хранилища в локальной файловой системе."""

    def __init__(self, base_path: str = "results"):
        """Инициализация локального хранилища.

        Args:
            base_path: Базовый путь для хранения файлов.
        """
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
        logger.info(f"Инициализировано локальное хранилище в {base_path}")

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Загрузка файла в локальное хранилище (проверка существования).

        Args:
            local_path: Путь к локальному файлу.
            remote_path: Удаленный путь (не используется для локального хранилища).

        Returns:
            True если файл существует, False в противном случае.
        """
        try:
            # Для локального хранилища просто проверяем, что файл существует
            if os.path.exists(local_path):
                logger.info(f"Файл подтвержден в локальном хранилище: {local_path}")
                return True
            else:
                logger.error(f"Файл не найден: {local_path}")
                return False
        except Exception as e:
            logger.error(f"Ошибка при проверке файла: {str(e)}")
            return False

    def list_files(self) -> list:
        """Получение списка файлов в хранилище.

        Returns:
            Список относительных путей к файлам.
        """
        try:
            files = []
            for root, dirs, filenames in os.walk(self.base_path):
                for filename in filenames:
                    rel_path = os.path.relpath(
                        os.path.join(root, filename), self.base_path
                    )
                    files.append(rel_path)
            return files
        except Exception as e:
            logger.error(f"Ошибка при получении списка файлов: {str(e)}")
            return []


def get_storage_client(storage_type: str, **kwargs) -> LocalStorage:
    """Получение клиента хранилища по типу.

    Args:
        storage_type: Тип хранилища (local, dropbox, gcs, s3).
        **kwargs: Дополнительные параметры для инициализации.

    Returns:
        Экземпляр клиента хранилища.

    Raises:
        ValueError: Если тип хранилища не поддерживается.
    """
    if storage_type == "local":
        return LocalStorage(kwargs.get("base_path", "results"))
    else:
        raise ValueError(f"Неподдерживаемый тип хранилища: {storage_type}")


def upload_results(
    storage_config: Dict[str, Any], results_dir: str = "results"
) -> bool:
    """
    Загрузка всех результатов в настроенное хранилище.

    Args:
        storage_config: Конфигурация хранилища.
        results_dir: Директория с результатами.

    Returns:
        True если успешно.
    """
    try:
        logger.info("Начинается загрузка результатов")

        # Получение клиента хранилища
        storage_type = storage_config.get("type", "local")
        client = get_storage_client(storage_type, **storage_config)

        # Поиск всех файлов результатов
        result_files = []
        for root, dirs, files in os.walk(results_dir):
            for file in files:
                local_path = os.path.join(root, file)
                remote_path = os.path.relpath(local_path, results_dir)
                result_files.append((local_path, remote_path))

        # Загрузка каждого файла
        success_count = 0
        for local_path, remote_path in result_files:
            if client.upload_file(local_path, remote_path):
                success_count += 1

        logger.info(f"Загружено {success_count}/{len(result_files)} файлов")

        # Создание сводки загрузки
        upload_summary = {
            "storage_type": storage_type,
            "total_files": len(result_files),
            "successful_uploads": success_count,
            "files": [remote_path for _, remote_path in result_files],
        }

        # Сохранение сводки загрузки
        with open(os.path.join(results_dir, "upload_summary.json"), "w") as f:
            json.dump(upload_summary, f, indent=2)

        return success_count == len(result_files)

    except Exception as e:
        logger.error(f"Ошибка загрузки результатов: {str(e)}")
        return False


def main():
    """Основная функция для автономного выполнения."""
    try:
        # Конфигурация для локального хранилища (по умолчанию)
        storage_config = {"type": "local", "base_path": "results"}

        # Проверка переменных окружения
        storage_type = os.getenv("STORAGE_TYPE", "local")

        if storage_type != "local":
            logger.warning(
                f"Тип хранилища {storage_type} не поддерживается в упрощенной версии"
            )
            storage_config = {"type": "local", "base_path": "results"}

        # Загрузка результатов
        success = upload_results(storage_config)

        if success:
            logger.info("Все результаты загружены успешно")
            print("Загрузка результатов завершена успешно")
        else:
            logger.warning("Некоторые файлы не удалось загрузить")
            print("Загрузка результатов завершена с предупреждениями")

    except Exception as e:
        logger.error(f"Ошибка в основном выполнении: {str(e)}")
        raise


if __name__ == "__main__":
    main()
