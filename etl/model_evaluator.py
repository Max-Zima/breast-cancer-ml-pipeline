"""
Модуль оценки модели и расчета метрик.

Этот модуль предоставляет функции для оценки производительности модели,
расчета метрик классификации и создания визуализаций.
"""

import json
import logging
import os
import sys
from typing import Any, Dict

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

# Добавление родительской директории в путь для импортов
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def calculate_metrics(
    y_true: pd.Series, y_pred: pd.Series, y_prob: pd.Series = None
) -> Dict[str, Any]:
    """
    Calculate comprehensive evaluation metrics

    Args:
        y_true: True labels
        y_pred: Predicted labels
        y_prob: Predicted probabilities (optional)

    Returns:
        Dictionary with calculated metrics
    """
    try:
        logger.info("Calculating evaluation metrics")

        # Basic classification metrics
        metrics = {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "precision": float(precision_score(y_true, y_pred)),
            "recall": float(recall_score(y_true, y_pred)),
            "f1_score": float(f1_score(y_true, y_pred)),
            "support": {
                "total_samples": len(y_true),
                "positive_samples": int(y_true.sum()),
                "negative_samples": int(len(y_true) - y_true.sum()),
            },
        }

        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        metrics["confusion_matrix"] = {
            "tn": int(cm[0, 0]),
            "fp": int(cm[0, 1]),
            "fn": int(cm[1, 0]),
            "tp": int(cm[1, 1]),
        }

        # Specificity (True Negative Rate)
        tn, fp, fn, tp = cm.ravel()
        metrics["specificity"] = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0

        # Add ROC AUC if probabilities are provided
        if y_prob is not None:
            metrics["roc_auc"] = float(roc_auc_score(y_true, y_prob))

        # Classification report
        report = classification_report(y_true, y_pred, output_dict=True)
        metrics["classification_report"] = report

        logger.info(f"Metrics calculated - Accuracy: {metrics['accuracy']:.4f}")
        logger.info(f"F1-Score: {metrics['f1_score']:.4f}")

        return metrics

    except Exception as e:
        logger.error(f"Error calculating metrics: {str(e)}")
        raise


def evaluate_model(
    model: Any, X_test: pd.DataFrame, y_test: pd.Series
) -> Dict[str, Any]:
    """
    Evaluate model performance on test data

    Args:
        model: Trained model
        X_test: Test features
        y_test: Test target

    Returns:
        Dictionary with evaluation results
    """
    try:
        logger.info("Evaluating model performance")

        # Make predictions
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]  # Probability of positive class

        # Convert to pandas Series for consistency
        y_pred_series = pd.Series(y_pred, index=y_test.index)
        y_prob_series = pd.Series(y_prob, index=y_test.index)

        # Calculate metrics
        metrics = calculate_metrics(y_test, y_pred_series, y_prob_series)

        # Add model-specific information
        evaluation_results = {
            "model_type": type(model).__name__,
            "test_set_size": len(X_test),
            "feature_count": X_test.shape[1],
            "metrics": metrics,
            "predictions": {
                "y_true": y_test.tolist(),
                "y_pred": y_pred.tolist(),
                "y_prob": y_prob.tolist(),
            },
        }

        logger.info("Model evaluation completed")
        return evaluation_results

    except Exception as e:
        logger.error(f"Error during model evaluation: {str(e)}")
        raise


def save_metrics(
    metrics: Dict[str, Any], output_path: str = "results/model_metrics.json"
):
    """
    Save metrics to JSON file

    Args:
        metrics: Metrics dictionary
        output_path: Path to save metrics
    """
    try:
        logger.info(f"Saving metrics to {output_path}")

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Save metrics as JSON
        with open(output_path, "w") as f:
            json.dump(metrics, f, indent=2)

        logger.info("Metrics saved successfully")

    except Exception as e:
        logger.error(f"Error saving metrics: {str(e)}")
        raise


def create_evaluation_plots(
    evaluation_results: Dict[str, Any], output_dir: str = "results"
):
    """
    Create visualization plots for model evaluation

    Args:
        evaluation_results: Evaluation results dictionary
        output_dir: Directory to save plots
    """
    try:
        logger.info("Creating evaluation plots")

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Extract data
        metrics = evaluation_results["metrics"]
        y_true = evaluation_results["predictions"]["y_true"]
        y_pred = evaluation_results["predictions"]["y_pred"]
        y_prob = evaluation_results["predictions"]["y_prob"]

        # 1. Confusion Matrix
        plt.figure(figsize=(8, 6))
        cm_data = [
            [metrics["confusion_matrix"]["tn"], metrics["confusion_matrix"]["fp"]],
            [metrics["confusion_matrix"]["fn"], metrics["confusion_matrix"]["tp"]],
        ]

        sns.heatmap(
            cm_data,
            annot=True,
            fmt="d",
            cmap="Blues",
            xticklabels=["Predicted Benign", "Predicted Malignant"],
            yticklabels=["Actual Benign", "Actual Malignant"],
        )
        plt.title("Confusion Matrix")
        plt.ylabel("Actual")
        plt.xlabel("Predicted")
        plt.tight_layout()
        plt.savefig(f"{output_dir}/confusion_matrix.png", dpi=300, bbox_inches="tight")
        plt.close()

        # 2. ROC Curve (if available)
        if "roc_auc" in metrics:
            plt.figure(figsize=(8, 6))
            fpr, tpr, _ = roc_curve(y_true, y_prob)
            plt.plot(
                fpr,
                tpr,
                color="darkorange",
                lw=2,
                label=f'ROC curve (AUC = {metrics["roc_auc"]:.3f})',
            )
            plt.plot([0, 1], [0, 1], color="navy", lw=2, linestyle="--")
            plt.xlim([0.0, 1.0])
            plt.ylim([0.0, 1.05])
            plt.xlabel("False Positive Rate")
            plt.ylabel("True Positive Rate")
            plt.title("Receiver Operating Characteristic (ROC) Curve")
            plt.legend(loc="lower right")
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(f"{output_dir}/roc_curve.png", dpi=300, bbox_inches="tight")
            plt.close()

        # 3. Metrics Summary Bar Plot
        plt.figure(figsize=(10, 6))
        metric_names = ["Accuracy", "Precision", "Recall", "F1-Score", "Specificity"]
        metric_values = [
            metrics["accuracy"],
            metrics["precision"],
            metrics["recall"],
            metrics["f1_score"],
            metrics["specificity"],
        ]

        bars = plt.bar(
            metric_names,
            metric_values,
            color=["skyblue", "lightgreen", "lightcoral", "gold", "plum"],
        )
        plt.ylim(0, 1)
        plt.ylabel("Score")
        plt.title("Model Performance Metrics")
        plt.xticks(rotation=45)

        # Add value labels on bars
        for bar, value in zip(bars, metric_values):
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.01,
                f"{value:.3f}",
                ha="center",
                va="bottom",
            )

        plt.tight_layout()
        plt.savefig(f"{output_dir}/metrics_summary.png", dpi=300, bbox_inches="tight")
        plt.close()

        logger.info("Evaluation plots created successfully")

    except Exception as e:
        logger.error(f"Error creating plots: {str(e)}")
        # Don't raise exception for plotting errors
        logger.warning("Continuing without plots")


def generate_evaluation_report(
    evaluation_results: Dict[str, Any],
    output_path: str = "results/evaluation_report.txt",
):
    """
    Generate detailed evaluation report

    Args:
        evaluation_results: Evaluation results dictionary
        output_path: Path to save report
    """
    try:
        logger.info("Generating evaluation report")

        metrics = evaluation_results["metrics"]

        with open(output_path, "w") as f:
            f.write("=== BREAST CANCER MODEL EVALUATION REPORT ===\n\n")

            f.write(f"Model Type: {evaluation_results['model_type']}\n")
            f.write(f"Test Set Size: {evaluation_results['test_set_size']}\n")
            f.write(f"Feature Count: {evaluation_results['feature_count']}\n\n")

            f.write("=== PERFORMANCE METRICS ===\n")
            f.write(f"Accuracy:     {metrics['accuracy']:.4f}\n")
            f.write(f"Precision:    {metrics['precision']:.4f}\n")
            f.write(f"Recall:       {metrics['recall']:.4f}\n")
            f.write(f"F1-Score:     {metrics['f1_score']:.4f}\n")
            f.write(f"Specificity:  {metrics['specificity']:.4f}\n")

            if "roc_auc" in metrics:
                f.write(f"ROC AUC:      {metrics['roc_auc']:.4f}\n")

            f.write("\n=== CONFUSION MATRIX ===\n")
            cm = metrics["confusion_matrix"]
            f.write(f"True Negatives:  {cm['tn']}\n")
            f.write(f"False Positives: {cm['fp']}\n")
            f.write(f"False Negatives: {cm['fn']}\n")
            f.write(f"True Positives:  {cm['tp']}\n")

            f.write("\n=== SAMPLE DISTRIBUTION ===\n")
            support = metrics["support"]
            f.write(f"Total Samples:    {support['total_samples']}\n")
            f.write(f"Positive Samples: {support['positive_samples']}\n")
            f.write(
                f"Negative Samples: {support['negative_samples']}\n"
            )  # Model interpretation
            f.write("\n=== INTERPRETATION ===\n")
            if metrics["accuracy"] >= 0.95:
                f.write("+ Excellent accuracy achieved\n")
            elif metrics["accuracy"] >= 0.90:
                f.write("+ Good accuracy achieved\n")
            else:
                f.write("! Accuracy could be improved\n")

            if metrics["recall"] >= 0.95:
                f.write("+ Excellent recall (low false negatives)\n")
            elif metrics["recall"] >= 0.90:
                f.write("+ Good recall\n")
            else:
                f.write("! Consider improving recall to reduce false negatives\n")

            if metrics["precision"] >= 0.95:
                f.write("+ Excellent precision (low false positives)\n")
            elif metrics["precision"] >= 0.90:
                f.write("+ Good precision\n")
            else:
                f.write("! Consider improving precision to reduce false positives\n")

        logger.info("Evaluation report generated successfully")

    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise


def main():
    """Main function for standalone execution"""
    try:
        # Load test data and model
        logger.info("Loading test data and model")

        if not os.path.exists("results/X_test.csv"):
            raise FileNotFoundError("Test data not found. Run preprocessing first")
        if not os.path.exists("results/breast_cancer_model.joblib"):
            raise FileNotFoundError("Model not found. Run training first")

        X_test = pd.read_csv("results/X_test.csv")
        y_test = pd.read_csv("results/y_test.csv").iloc[:, 0]

        # Load model
        import joblib

        model = joblib.load("results/breast_cancer_model.joblib")

        # Evaluate model
        evaluation_results = evaluate_model(model, X_test, y_test)

        # Save metrics
        save_metrics(evaluation_results)

        # Create plots
        create_evaluation_plots(evaluation_results)

        # Generate report
        generate_evaluation_report(evaluation_results)

        logger.info("Model evaluation completed successfully")
        print("Model evaluation completed. Check results/ directory")

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        raise


if __name__ == "__main__":
    main()
