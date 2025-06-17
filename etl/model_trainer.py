"""
Модуль обучения модели.

Этот модуль предоставляет функции для обучения модели машинного обучения
и сохранения обученной модели.
"""

import logging
import os
import sys
from typing import Any

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression

# Добавление родительской директории в путь для импортов
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def train_model(
    X_train: pd.DataFrame, y_train: pd.Series, model_params: dict = None
) -> Any:
    """
    Обучение модели логистической регрессии.

    Args:
        X_train: Training features
        y_train: Training target
        model_params: Model hyperparameters

    Returns:
        Trained model
    """
    try:
        logger.info("Starting model training")

        # Default parameters
        if model_params is None:
            model_params = {"solver": "liblinear", "max_iter": 1000, "random_state": 42}

        # Initialize model
        model = LogisticRegression(**model_params)

        # Train model
        logger.info(f"Training with parameters: {model_params}")
        model.fit(X_train, y_train)

        # Log training info
        logger.info("Model training completed")
        logger.info(f"Number of features used: {X_train.shape[1]}")
        logger.info(f"Training samples: {len(X_train)}")

        return model

    except Exception as e:
        logger.error(f"Error during model training: {str(e)}")
        raise


def save_model(model: Any, model_path: str = "results/breast_cancer_model.joblib"):
    """
    Save trained model to file

    Args:
        model: Trained model
        model_path: Path to save model
    """
    try:
        logger.info(f"Saving model to {model_path}")

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(model_path), exist_ok=True)

        # Save model
        joblib.dump(model, model_path)

        logger.info("Model saved successfully")

    except Exception as e:
        logger.error(f"Error saving model: {str(e)}")
        raise


def load_model(model_path: str = "results/breast_cancer_model.joblib") -> Any:
    """
    Load trained model from file

    Args:
        model_path: Path to model file

    Returns:
        Loaded model
    """
    try:
        logger.info(f"Loading model from {model_path}")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")

        model = joblib.load(model_path)

        logger.info("Model loaded successfully")
        return model

    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        raise


def get_model_info(model: Any) -> dict:
    """
    Get information about the trained model

    Args:
        model: Trained model

    Returns:
        Dictionary with model information
    """
    try:
        info = {
            "model_type": type(model).__name__,
            "n_features": model.n_features_in_,
            "classes": model.classes_.tolist(),
            "intercept": model.intercept_.tolist(),
            "coefficients_shape": model.coef_.shape,
        }

        # Add top important features if available
        if hasattr(model, "coef_") and model.coef_ is not None:
            coef_abs = abs(model.coef_[0])
            # Get indices of top 10 features
            top_indices = coef_abs.argsort()[-10:][::-1]
            info["top_feature_indices"] = top_indices.tolist()
            info["top_coefficients"] = coef_abs[top_indices].tolist()

        return info

    except Exception as e:
        logger.error(f"Error getting model info: {str(e)}")
        return {}


def main():
    """Main function for standalone execution"""
    try:
        # Load processed data
        logger.info("Loading processed data")

        if not os.path.exists("results/X_train.csv"):
            raise FileNotFoundError(
                "Processed training data not found. Run data_preprocessor.py first"
            )

        X_train = pd.read_csv("results/X_train.csv")
        y_train = pd.read_csv("results/y_train.csv").iloc[
            :, 0
        ]  # Get first column as Series

        # Train model
        model = train_model(X_train, y_train)

        # Save model
        save_model(model)

        # Get and save model info
        model_info = get_model_info(model)

        # Save model information
        with open("results/model_info.txt", "w") as f:
            f.write("=== MODEL INFORMATION ===\n\n")
            for key, value in model_info.items():
                f.write(f"{key}: {value}\n")

        logger.info("Model training completed successfully")
        print("Model training completed. Check results/ directory")

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        raise


if __name__ == "__main__":
    main()
