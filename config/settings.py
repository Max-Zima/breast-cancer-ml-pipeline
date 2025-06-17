"""
Загрузчик конфигурации для пайплайна машинного обучения.

Этот модуль предоставляет функции для загрузки конфигурации из YAML файлов
и управления переменными окружения.
"""

import os
from typing import Any, Dict, Optional

try:
    import yaml
except ImportError:
    yaml = None

try:
    from dotenv import load_dotenv

    # Загрузка переменных окружения
    load_dotenv()
except ImportError:
    pass


def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """Загрузка конфигурации из YAML файла.

    Args:
        config_path: Путь к файлу конфигурации.

    Returns:
        Словарь с параметрами конфигурации.

    Raises:
        ImportError: Если PyYAML не установлен.
        FileNotFoundError: Если файл конфигурации не найден.
        ValueError: Если ошибка парсинга YAML.
    """
    if yaml is None:
        raise ImportError("PyYAML необходим для загрузки конфигурации")

    try:
        with open(config_path, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        raise FileNotFoundError(f"Файл конфигурации не найден: {config_path}")
    except yaml.YAMLError as e:
        raise ValueError(f"Ошибка парсинга YAML конфигурации: {e}")


def get_env_variable(var_name: str, default: Optional[str] = None) -> str:
    """Получение переменной окружения с опциональным значением по умолчанию.

    Args:
        var_name: Имя переменной окружения.
        default: Значение по умолчанию (опционально).

    Returns:
        Значение переменной окружения.

    Raises:
        ValueError: Если обязательная переменная не установлена.
    """
    value = os.getenv(var_name, default)
    if value is None:
        raise ValueError(
            f"Переменная окружения {var_name} обязательна, но не установлена"
        )
    return value


# Глобальная конфигурация
try:
    CONFIG = load_config()
except (FileNotFoundError, ImportError):
    CONFIG = {}
