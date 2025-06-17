"""
Модуль предобработки данных.

Этот модуль предоставляет функции для очистки и предобработки данных,
подготовки признаков, разделения на выборки и масштабирования.
"""

import logging
import os
import sys
from typing import Tuple

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Добавление родительской директории в путь для импортов
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Очистка и предобработка набора данных.

    Args:
        df: Исходный DataFrame.

    Returns:
        Обработанный DataFrame.
    """
    try:
        logger.info("Начинается предобработка данных")

        # Создание копии для избежания изменения оригинала
        processed_df = df.copy()

        # Удаление потенциальных дубликатов на основе ID
        initial_size = len(processed_df)
        processed_df = processed_df.drop_duplicates(subset=["id"])
        duplicates_removed = initial_size - len(processed_df)

        if duplicates_removed > 0:
            logger.warning(
                f"Удалено {duplicates_removed} дублированных записей"
            )  # Обработка пропущенных значений (если есть)
        missing_before = processed_df.isnull().sum().sum()
        if missing_before > 0:
            logger.warning(f"Найдено {missing_before} пропущенных значений")

            # Для числовых столбцов заполнение медианой
            numerical_cols = processed_df.select_dtypes(
                include=["float64", "int64"]
            ).columns
            processed_df[numerical_cols] = processed_df[numerical_cols].fillna(
                processed_df[numerical_cols].median()
            )

            # Для категориальных столбцов заполнение модой
            categorical_cols = processed_df.select_dtypes(include=["object"]).columns
            for col in categorical_cols:
                if col != "diagnosis":  # Не заполняем целевую переменную
                    mode_value = processed_df[col].mode()
                    if len(mode_value) > 0:
                        processed_df[col] = processed_df[col].fillna(mode_value[0])

        # Преобразование целевой переменной в бинарную (0/1)
        processed_df["diagnosis_binary"] = processed_df["diagnosis"].map(
            {"M": 1, "B": 0}
        )

        # Проверка преобразования
        if processed_df["diagnosis_binary"].isnull().sum() > 0:
            raise ValueError("Не удалось преобразовать все значения диагноза")

        # Remove outliers using IQR method for key features
        key_features = ["radius_mean", "area_mean", "perimeter_mean"]
        outliers_removed = 0

        for feature in key_features:
            if feature in processed_df.columns:
                Q1 = processed_df[feature].quantile(0.25)
                Q3 = processed_df[feature].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR

                before_outlier_removal = len(processed_df)
                processed_df = processed_df[
                    (processed_df[feature] >= lower_bound)
                    & (processed_df[feature] <= upper_bound)
                ]
                outliers_removed += before_outlier_removal - len(processed_df)

        if outliers_removed > 0:
            logger.info(f"Removed {outliers_removed} outlier records")

        logger.info(f"Preprocessing completed. Final dataset size: {len(processed_df)}")
        return processed_df

    except Exception as e:
        logger.error(f"Error during preprocessing: {str(e)}")
        raise


def prepare_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Prepare features and target for machine learning

    Args:
        df: Preprocessed DataFrame

    Returns:
        Tuple of (features, target)
    """
    try:
        logger.info("Preparing features for ML")

        # Separate features and target
        feature_columns = [
            col
            for col in df.columns
            if col not in ["id", "diagnosis", "diagnosis_binary"]
        ]

        X = df[feature_columns].copy()
        y = df["diagnosis_binary"].copy()

        # Check for any remaining missing values
        if X.isnull().sum().sum() > 0:
            logger.warning("Features contain missing values, filling with median")
            X = X.fillna(X.median())

        if y.isnull().sum() > 0:
            raise ValueError("Target variable contains missing values")

        logger.info(f"Prepared {X.shape[1]} features for {len(X)} samples")
        logger.info(f"Target distribution: {y.value_counts().to_dict()}")

        return X, y

    except Exception as e:
        logger.error(f"Error preparing features: {str(e)}")
        raise


def split_and_scale_data(
    X: pd.DataFrame, y: pd.Series, test_size: float = 0.2, random_state: int = 42
) -> Tuple:
    """
    Split data into train/test sets and apply scaling

    Args:
        X: Feature matrix
        y: Target vector
        test_size: Proportion of data for testing
        random_state: Random seed for reproducibility

    Returns:
        Tuple of (X_train_scaled, X_test_scaled, y_train, y_test, scaler)
    """
    try:
        logger.info(f"Splitting data with test_size={test_size}")

        # Split the data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )

        logger.info(f"Train set size: {len(X_train)}")
        logger.info(f"Test set size: {len(X_test)}")

        # Initialize and fit scaler on training data only
        scaler = StandardScaler()
        X_train_scaled = pd.DataFrame(
            scaler.fit_transform(X_train), columns=X_train.columns, index=X_train.index
        )

        # Transform test data using fitted scaler
        X_test_scaled = pd.DataFrame(
            scaler.transform(X_test), columns=X_test.columns, index=X_test.index
        )

        logger.info("Data scaling completed")

        return X_train_scaled, X_test_scaled, y_train, y_test, scaler

    except Exception as e:
        logger.error(f"Error during data splitting and scaling: {str(e)}")
        raise


def save_processed_data(X_train, X_test, y_train, y_test, output_dir: str = "results"):
    """
    Save processed data to files

    Args:
        X_train, X_test, y_train, y_test: Split datasets
        output_dir: Directory to save files
    """
    try:
        logger.info(f"Saving processed data to {output_dir}")

        os.makedirs(output_dir, exist_ok=True)

        # Save training data
        X_train.to_csv(f"{output_dir}/X_train.csv", index=False)
        y_train.to_csv(f"{output_dir}/y_train.csv", index=False)

        # Save test data
        X_test.to_csv(f"{output_dir}/X_test.csv", index=False)
        y_test.to_csv(f"{output_dir}/y_test.csv", index=False)

        logger.info("Processed data saved successfully")

    except Exception as e:
        logger.error(f"Error saving processed data: {str(e)}")
        raise


def main():
    """Main function for standalone execution"""
    try:
        # Import data loader
        from etl.data_loader import load_breast_cancer_data, validate_data_schema

        # Load data
        df = load_breast_cancer_data()
        validate_data_schema(df)

        # Preprocess data
        processed_df = preprocess_data(df)

        # Prepare features
        X, y = prepare_features(processed_df)

        # Split and scale data
        X_train, X_test, y_train, y_test, scaler = split_and_scale_data(X, y)

        # Save processed data
        save_processed_data(X_train, X_test, y_train, y_test)

        # Save scaler for later use
        import joblib

        os.makedirs("results", exist_ok=True)
        joblib.dump(scaler, "results/scaler.joblib")

        logger.info("Data preprocessing completed successfully")
        print("Data preprocessing completed. Check results/ directory")

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        raise


if __name__ == "__main__":
    main()
