"""
Модуль загрузки данных и первичного анализа.

Этот модуль предоставляет функции для загрузки набора данных рака молочной железы,
валидации схемы данных и выполнения первичного анализа качества данных.
"""

import logging
import os
import sys
from typing import Any, Dict

import pandas as pd

# Добавление родительской директории в путь для импортов
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_breast_cancer_data(file_path: str = "wdbc.data") -> pd.DataFrame:
    """
    Загрузка набора данных рака молочной железы из файла.

    Args:
        file_path: Путь к файлу данных.

    Returns:
        DataFrame с загруженными данными.

    Raises:
        FileNotFoundError: Если файл данных не существует.
        ValueError: Если формат данных недействителен.
    """
    try:
        logger.info(f"Загрузка данных из {file_path}")

        # Определение имен столбцов на основе описания набора данных
        column_names = ["id", "diagnosis"] + [
            "radius_mean",
            "texture_mean",
            "perimeter_mean",
            "area_mean",
            "smoothness_mean",
            "compactness_mean",
            "concavity_mean",
            "concave_points_mean",
            "symmetry_mean",
            "fractal_dimension_mean",
            "radius_se",
            "texture_se",
            "perimeter_se",
            "area_se",
            "smoothness_se",
            "compactness_se",
            "concavity_se",
            "concave_points_se",
            "symmetry_se",
            "fractal_dimension_se",
            "radius_worst",
            "texture_worst",
            "perimeter_worst",
            "area_worst",
            "smoothness_worst",
            "compactness_worst",
            "concavity_worst",
            "concave_points_worst",
            "symmetry_worst",
            "fractal_dimension_worst",
        ]

        # Load data
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Data file not found: {file_path}")

        df = pd.read_csv(file_path, header=None, names=column_names)

        # Basic validation
        if df.empty:
            raise ValueError("Loaded dataset is empty")

        if len(df.columns) != 32:
            raise ValueError(f"Expected 32 columns, got {len(df.columns)}")

        logger.info(
            f"Successfully loaded {len(df)} samples with {len(df.columns)} columns"
        )
        return df

    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        raise


def analyze_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Выполнение первичного анализа данных.

    Args:
        df: Входной DataFrame.

    Returns:
        Словарь с результатами анализа.
    """
    try:
        logger.info("Выполняется анализ данных")

        analysis = {
            "shape": df.shape,
            "missing_values": df.isnull().sum().to_dict(),
            "data_types": df.dtypes.to_dict(),
            "target_distribution": df["diagnosis"].value_counts().to_dict(),
            "numerical_stats": df.describe().to_dict(),
            "target_percentage": {
                class_name: round(count / len(df) * 100, 2)
                for class_name, count in df["diagnosis"].value_counts().items()
            },
        }

        # Проверки качества данных
        quality_issues = []

        # Проверка пропущенных значений
        if df.isnull().sum().sum() > 0:
            quality_issues.append("Обнаружены пропущенные значения")

        # Проверка дубликатов
        if df.duplicated().sum() > 0:
            quality_issues.append("Обнаружены дублированные записи")

        # Проверка целевой переменной
        if len(df["diagnosis"].unique()) != 2:
            quality_issues.append("Целевая переменная не имеет ровно 2 класса")

        if not quality_issues:
            quality_issues.append("Серьезных проблем качества не обнаружено")

        analysis["quality_issues"] = quality_issues

        logger.info("Анализ данных завершен")
        return analysis

    except Exception as e:
        logger.error(f"Ошибка при анализе данных: {str(e)}")
        raise


def validate_data_schema(df: pd.DataFrame) -> bool:
    """
    Валидация схемы загруженных данных.

    Args:
        df: DataFrame для валидации.

    Returns:
        True если схема корректна.

    Raises:
        ValueError: Если схема данных недействительна.
    """
    try:
        logger.info("Валидация схемы данных")

        # Проверка обязательных столбцов
        required_columns = ["id", "diagnosis"]
        missing_required = [col for col in required_columns if col not in df.columns]

        if missing_required:
            raise ValueError(f"Отсутствуют обязательные столбцы: {missing_required}")

        # Проверка типов данных
        if not pd.api.types.is_object_dtype(df["diagnosis"]):
            raise ValueError("Столбец 'diagnosis' должен быть текстовым")

        # Проверка значений целевой переменной
        valid_diagnoses = {"M", "B"}
        invalid_diagnoses = set(df["diagnosis"].unique()) - valid_diagnoses
        if invalid_diagnoses:
            raise ValueError(f"Недопустимые значения диагноза: {invalid_diagnoses}")

        logger.info("Схема данных корректна")
        return True

    except Exception as e:
        logger.error(f"Ошибка валидации схемы: {str(e)}")
        raise


def main():
    """Основная функция для автономного выполнения."""
    try:
        # Загрузка данных
        df = load_breast_cancer_data()

        # Валидация схемы
        validate_data_schema(df)

        # Анализ данных
        analysis = analyze_data(df)

        # Сохранение результатов анализа
        os.makedirs("results", exist_ok=True)
        with open("results/data_analysis.txt", "w", encoding="utf-8") as f:
            f.write("=== АНАЛИЗ НАБОРА ДАННЫХ РАКА МОЛОЧНОЙ ЖЕЛЕЗЫ ===\n\n")
            f.write(f"Размер набора данных: {analysis['shape']}\n")
            f.write(
                f"Распределение целевых классов: "
                f"{analysis['target_distribution']}\n"
            )
            f.write(f"Проблемы качества: {analysis['quality_issues']}\n")
            f.write("\n=== СТАТИСТИЧЕСКИЕ СВЕДЕНИЯ ===\n")
            for col, stats in analysis["numerical_stats"].items():
                if col != "id":  # Пропускаем ID столбец
                    f.write(f"\n{col}:\n")
                    for stat, value in stats.items():
                        if isinstance(value, float):
                            f.write(f"  {stat}: {value:.4f}\n")
                        else:
                            f.write(f"  {stat}: {value}\n")

        logger.info("Анализ данных завершен и сохранен")
        print("Анализ данных выполнен успешно")

    except Exception as e:
        logger.error(f"Ошибка в основном выполнении: {str(e)}")
        raise


if __name__ == "__main__":
    main()
