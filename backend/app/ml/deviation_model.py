"""
Route deviation binary classifier.

Architecture:
    Candidate: RandomForestClassifier (sklearn)
    Random state: 42 (deterministic)

Data mode:
    SYNTHETIC_DEMO — trained on 5 hard-coded benchmark samples with both classes.
    REAL — would be trained on actual Mendeley Planned-vs-Actual data.

Metric honesty:
    PR-AUC is computed using actual prediction probabilities via sklearn's
    average_precision_score.  It is NEVER hard-coded.
    When test data lacks both classes, evaluation_status = "insufficient_class_variety".
    When test data has < MIN_SAMPLES_FOR_EVAL, evaluation_status = "insufficient_data".

Usage:
    model = RouteDeviationClassifier()
    prob = model.predict_deviation_probability(feature_dict)
    info = model.get_metadata()
"""

import numpy as np
from typing import Dict, Any, Optional, List
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    average_precision_score,
)

from app.ml.features import FEATURE_NAMES

MIN_SAMPLES_FOR_EVAL = 10
DEVIATION_THRESHOLD = 0.5


class RouteDeviationClassifier:
    """
    Binary classifier: predicts whether a driver will materially deviate
    from the planned route sequence.

    Label convention:
        0 = no material deviation
        1 = material deviation (stop reordering, extra distance, etc.)
    """

    MODEL_NAME = "ROUTE_DEVIATION_CLASSIFIER"
    MODEL_VERSION = "v1.2.0"
    ALGORITHM = "RandomForestClassifier"
    TARGET_NAME = "is_material_deviation"

    def __init__(self) -> None:
        self.model = RandomForestClassifier(
            n_estimators=30, max_depth=4, random_state=42
        )

        self._data_mode: str = "synthetic_demo"
        self._training_sample_count: int = 0
        self._evaluation_sample_count: int = 0
        self._is_trained: bool = False
        self._evaluation_status: str = "not_evaluated"
        self._metrics: Optional[Dict[str, float]] = None

        self._fit_synthetic_bootstrap()

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def _fit_synthetic_bootstrap(self) -> None:
        """
        Train on 5 hard-coded benchmark samples (both classes represented).
        These are domain-expert estimates — NOT real delivery data.
        """
        X = np.array([
            [8,  28.5, 180.0, 3.56, 22.5, 0.95, 2.0,  0.0, 12.6],  # 0
            [12, 40.0, 240.0, 3.33, 20.0, 0.85, 8.0,  5.0, 18.0],  # 1
            [16, 55.0, 330.0, 3.44, 20.6, 0.90, 4.5, 10.0, 24.5],  # 1
            [6,  18.0, 120.0, 3.00, 20.0, 0.98, 1.0,  0.0,  8.4],  # 0
            [20, 72.0, 420.0, 3.60, 21.0, 0.78, 12.0, 20.0, 35.6], # 1
        ], dtype=np.float64)

        y = np.array([0, 1, 1, 0, 1], dtype=np.int32)

        self.model.fit(X, y)
        self._training_sample_count = len(y)
        self._is_trained = True
        self._data_mode = "synthetic_demo"
        self._evaluation_status = "insufficient_data"
        self._metrics = None

    def train(
        self, X: np.ndarray, y: np.ndarray, data_mode: str = "real"
    ) -> None:
        """
        Train on real or augmented data.

        Parameters
        ----------
        X : ndarray of shape (n_samples, len(FEATURE_NAMES))
        y : ndarray of shape (n_samples,) — binary labels (0 or 1)
        data_mode : "real" | "synthetic_demo"
        """
        if len(X) == 0 or len(y) == 0:
            raise ValueError("Cannot train on empty dataset.")
        if X.shape[1] != len(FEATURE_NAMES):
            raise ValueError(
                f"Expected {len(FEATURE_NAMES)} features, got {X.shape[1]}."
            )
        unique_classes = np.unique(y)
        if len(unique_classes) < 2:
            raise ValueError(
                f"Training data must contain both classes (0 and 1). "
                f"Got only: {unique_classes.tolist()}"
            )

        self.model.fit(X, y)
        self._training_sample_count = int(len(y))
        self._is_trained = True
        self._data_mode = data_mode
        self._evaluation_status = "not_evaluated"
        self._metrics = None

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict_deviation_probability(self, features: Dict[str, Any]) -> float:
        """
        Returns predicted probability [0..1] of material route deviation.

        Parameters
        ----------
        features : dict — keys from FEATURE_NAMES (missing keys default to 0.0)
        """
        feature_vector = np.array(
            [[features.get(k, 0.0) for k in FEATURE_NAMES]], dtype=np.float64
        )
        prob = float(self.model.predict_proba(feature_vector)[0][1])
        return round(prob, 3)

    def predict(self, features: Dict[str, Any]) -> int:
        """Returns binary prediction (0 or 1) using DEVIATION_THRESHOLD."""
        return int(self.predict_deviation_probability(features) >= DEVIATION_THRESHOLD)

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def evaluate(
        self,
        X_test: np.ndarray,
        y_test: np.ndarray,
        data_mode: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate classifier on held-out test data.

        PR-AUC is calculated using sklearn's average_precision_score with
        actual predicted probabilities — never hard-coded.

        Returns
        -------
        dict with evaluation_status, metrics (or None), and metadata.
        """
        if data_mode is not None:
            self._data_mode = data_mode

        self._evaluation_sample_count = int(len(y_test))

        if len(y_test) < MIN_SAMPLES_FOR_EVAL:
            self._evaluation_status = "insufficient_data"
            self._metrics = None
            return {
                "evaluation_status": "insufficient_data",
                "data_mode": self._data_mode,
                "evaluation_sample_count": self._evaluation_sample_count,
                "min_samples_required": MIN_SAMPLES_FOR_EVAL,
                "metrics": None,
            }

        unique_classes = np.unique(y_test)
        if len(unique_classes) < 2:
            self._evaluation_status = "insufficient_class_variety"
            self._metrics = None
            return {
                "evaluation_status": "insufficient_class_variety",
                "data_mode": self._data_mode,
                "evaluation_sample_count": self._evaluation_sample_count,
                "note": "Test set must contain both positive and negative examples.",
                "metrics": None,
            }

        probs = self.model.predict_proba(X_test)[:, 1]
        preds = (probs >= DEVIATION_THRESHOLD).astype(int)

        is_low_sample = len(y_test) < 30
        self._evaluation_status = "low_sample_size" if is_low_sample else "evaluated"
        round_dec = 1 if is_low_sample else 3

        self._metrics = {
            "precision": round(
                float(precision_score(y_test, preds, zero_division=0)), round_dec
            ),
            "recall": round(
                float(recall_score(y_test, preds, zero_division=0)), round_dec
            ),
            "f1_score": round(
                float(f1_score(y_test, preds, zero_division=0)), round_dec
            ),
            "pr_auc": round(
                float(average_precision_score(y_test, probs)), round_dec
            ),
        }

        return {
            "evaluation_status": self._evaluation_status,
            "data_mode": self._data_mode,
            "evaluation_sample_count": self._evaluation_sample_count,
            "metrics": self._metrics,
            "sample_size_warning": (
                "Evaluated on small sample (n < 30). Metrics are rounded to 1 decimal place "
                "and should be treated as preliminary benchmarks."
                if is_low_sample
                else None
            ),
        }

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def get_metadata(self) -> Dict[str, Any]:
        """
        Returns a complete description of model state suitable for the API.
        Never contains fabricated metrics.
        """
        is_low_sample = self._evaluation_status == "low_sample_size"
        return {
            "model_name": self.MODEL_NAME,
            "model_version": self.MODEL_VERSION,
            "algorithm": self.ALGORITHM,
            "target_name": self.TARGET_NAME,
            "feature_names": FEATURE_NAMES,
            "feature_count": len(FEATURE_NAMES),
            "data_mode": self._data_mode,
            "is_trained": self._is_trained,
            "training_sample_count": self._training_sample_count,
            "evaluation_sample_count": self._evaluation_sample_count,
            "evaluation_status": self._evaluation_status,
            "metrics": self._metrics,
            "sample_size_warning": (
                "Evaluated on small sample (n < 30). Metrics are rounded to 1 decimal place "
                "and should be treated as preliminary benchmarks."
                if is_low_sample
                else None
            ),
            "limitations": (
                "Model is trained on a 5-sample synthetic benchmark. "
                "Metrics are not available (insufficient_data). "
                "Supply real Mendeley Planned-vs-Actual data and call "
                "train()/evaluate() to obtain meaningful performance estimates."
                if self._data_mode == "synthetic_demo"
                else (
                    "Model evaluated on limited sample size (n < 30). "
                    "Results are indicative benchmarks rather than production guarantees."
                    if is_low_sample
                    else None
                )
            ),
        }

    # ------------------------------------------------------------------
    # Backward-compatibility aliases
    # ------------------------------------------------------------------

    def evaluate_performance(
        self, X_test: np.ndarray, y_test: np.ndarray
    ) -> Dict[str, Any]:
        """Alias for evaluate(). Returns the full evaluation result dict."""
        return self.evaluate(X_test, y_test)

    @property
    def feature_names(self) -> List[str]:
        return FEATURE_NAMES

    @property
    def model_version(self) -> str:
        return self.MODEL_VERSION

    @property
    def algorithm(self) -> str:
        return self.ALGORITHM
