"""
ETA (Estimated Time of Arrival) delay prediction model.

Architecture:
    Candidate: GradientBoostingRegressor (sklearn)
    Baseline:  Linear Regression (sklearn)
    Random state: 42 (deterministic)

Data mode:
    SYNTHETIC_DEMO — trained on 5 hard-coded benchmark samples.
    REAL — would be trained on actual Amazon/Mendeley ingested data.

The current implementation operates in SYNTHETIC_DEMO mode because
the repository does not contain the real Amazon Last Mile or Mendeley datasets.

Metric honesty:
    When training sample count < MIN_SAMPLES_FOR_EVAL, evaluation metrics are
    NOT reported and evaluation_status = "insufficient_data" is returned.
    Metrics are NEVER hard-coded.

Usage:
    model = ETAPredictionModel()
    delay_min, late_prob = model.predict_delay(feature_dict)
    info = model.get_metadata()
"""

import numpy as np
from typing import Dict, Any, Tuple, Optional, List
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

from app.ml.features import FEATURE_NAMES

# We require at least this many samples to report evaluation metrics.
# With fewer samples the leave-one-out or split-based metrics would be
# trivially over/under-fit and misleading.
MIN_SAMPLES_FOR_EVAL = 10

# Delay threshold above which a delivery is considered "late"
LATE_THRESHOLD_MIN = 15.0

# Sigmoid sharpness around the late threshold (in minutes)
SIGMOID_SCALE = 5.0


class ETAPredictionModel:
    """
    Supervised Machine Learning model for predicting delivery delay (in minutes).

    In SYNTHETIC_DEMO mode the model is trained on 5 hard-coded samples derived
    from domain-expert estimates.  This is explicitly acknowledged in the metadata
    and evaluation_status is set to "insufficient_data".

    When real route data is supplied (≥ MIN_SAMPLES_FOR_EVAL samples), call
    ``train(X, y)`` followed by ``evaluate(X_test, y_test)`` to obtain real metrics.
    """

    MODEL_NAME = "ETA_DELAY_PREDICTOR"
    MODEL_VERSION = "v1.3.0"
    ALGORITHM = "GradientBoostingRegressor"
    TARGET_NAME = "delay_minutes"

    def __init__(self) -> None:
        self.candidate_model = GradientBoostingRegressor(
            n_estimators=50, max_depth=3, random_state=42
        )
        self.baseline_model = LinearRegression()

        # Track metadata
        self._data_mode: str = "synthetic_demo"
        self._training_sample_count: int = 0
        self._evaluation_sample_count: int = 0
        self._is_trained: bool = False
        self._evaluation_status: str = "not_evaluated"
        self._metrics: Optional[Dict[str, float]] = None

        # Bootstrap with synthetic samples so the model is immediately usable
        self._fit_synthetic_bootstrap()

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def _fit_synthetic_bootstrap(self) -> None:
        """
        Train on 5 hard-coded benchmark samples for immediate out-of-box usability.
        These samples are domain-expert estimates — NOT real delivery data.
        Evaluation is explicitly marked as insufficient_data.
        """
        # Columns follow FEATURE_NAMES order:
        # stop_count, planned_dist, planned_dur, avg_stop_dist, avg_stop_dur,
        # driver_adherence, driver_hist_delay, tw_pressure, complexity
        X = np.array([
            [8,  28.5, 180.0, 3.56, 22.5, 0.95, 2.0,  0.0, 12.6],
            [12, 40.0, 240.0, 3.33, 20.0, 0.85, 8.0,  5.0, 18.0],
            [16, 55.0, 330.0, 3.44, 20.6, 0.90, 4.5, 10.0, 24.5],
            [6,  18.0, 120.0, 3.00, 20.0, 0.98, 1.0,  0.0,  8.4],
            [20, 72.0, 420.0, 3.60, 21.0, 0.78, 12.0, 20.0, 35.6],
        ], dtype=np.float64)

        # Target: delay in minutes (domain-expert estimates)
        y = np.array([4.5, 18.0, 10.0, 1.0, 32.0], dtype=np.float64)

        self.candidate_model.fit(X, y)
        self.baseline_model.fit(X, y)

        self._training_sample_count = len(y)
        self._is_trained = True
        self._data_mode = "synthetic_demo"
        self._evaluation_status = "insufficient_data"
        self._metrics = None

    def train(self, X: np.ndarray, y: np.ndarray, data_mode: str = "real") -> None:
        """
        Train on real or augmented data.

        Parameters
        ----------
        X : ndarray of shape (n_samples, len(FEATURE_NAMES))
        y : ndarray of shape (n_samples,) — delay in minutes
        data_mode : "real" | "synthetic_demo"
        """
        if len(X) == 0 or len(y) == 0:
            raise ValueError("Cannot train on empty dataset.")
        if X.shape[1] != len(FEATURE_NAMES):
            raise ValueError(
                f"Expected {len(FEATURE_NAMES)} features, got {X.shape[1]}."
            )
        if len(X) != len(y):
            raise ValueError("X and y must have the same number of rows.")

        self.candidate_model.fit(X, y)
        self.baseline_model.fit(X, y)
        self._training_sample_count = int(len(y))
        self._is_trained = True
        self._data_mode = data_mode
        self._evaluation_status = "not_evaluated"
        self._metrics = None

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict_delay(self, features: Dict[str, Any]) -> Tuple[float, float]:
        """
        Predict delivery delay and late probability from a feature dict.

        Parameters
        ----------
        features : dict — keys matching FEATURE_NAMES (missing keys default to 0.0)

        Returns
        -------
        (predicted_delay_min, late_probability)
            predicted_delay_min : float ≥ 0
            late_probability    : float in [0, 1]
        """
        feature_vector = np.array(
            [[features.get(k, 0.0) for k in FEATURE_NAMES]], dtype=np.float64
        )

        raw_pred = float(self.candidate_model.predict(feature_vector)[0])
        pred_delay = max(0.0, round(raw_pred, 1))

        # Sigmoid: maps delay minutes to probability of being "late"
        # At LATE_THRESHOLD_MIN minutes → 0.5; approaches 1 for very large delays.
        late_prob = 1.0 / (1.0 + np.exp(-(pred_delay - LATE_THRESHOLD_MIN) / SIGMOID_SCALE))
        late_prob = float(round(late_prob, 3))

        return pred_delay, late_prob

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def evaluate(
        self, X_test: np.ndarray, y_test: np.ndarray, data_mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate the candidate model on held-out test data.

        Returns a dict with:
            evaluation_status : "evaluated" | "insufficient_data"
            data_mode         : which data was used
            evaluation_sample_count : int
            metrics           : dict of MAE/RMSE/median_AE/P90/bias, or None

        Metrics are only populated when len(y_test) >= MIN_SAMPLES_FOR_EVAL.
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

        preds = self.candidate_model.predict(X_test)
        errors = np.abs(y_test - preds)

        is_low_sample = len(y_test) < 30
        self._evaluation_status = "low_sample_size" if is_low_sample else "evaluated"
        round_dec = 1 if is_low_sample else 3

        self._metrics = {
            "mae": round(float(mean_absolute_error(y_test, preds)), round_dec),
            "rmse": round(float(np.sqrt(mean_squared_error(y_test, preds))), round_dec),
            "median_ae": round(float(np.median(errors)), round_dec),
            "p90_error": round(float(np.percentile(errors, 90)), round_dec),
            "bias": round(float(np.mean(preds - y_test)), round_dec),
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
                "Supply real Amazon Last Mile data and call train()/evaluate() "
                "to obtain meaningful performance estimates."
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
    # Convenience alias for backward compatibility
    # ------------------------------------------------------------------

    def evaluate_performance(
        self, X_test: np.ndarray, y_test: np.ndarray
    ) -> Dict[str, Any]:
        """Alias for evaluate(). Returns the full evaluation result dict."""
        return self.evaluate(X_test, y_test)

    # ------------------------------------------------------------------
    # Properties for external access
    # ------------------------------------------------------------------

    @property
    def feature_names(self) -> List[str]:
        return FEATURE_NAMES

    @property
    def model_version(self) -> str:
        return self.MODEL_VERSION

    @property
    def algorithm(self) -> str:
        return self.ALGORITHM
