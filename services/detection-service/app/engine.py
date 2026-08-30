from dataclasses import dataclass

from app.schemas import DetectionFeatures


@dataclass(frozen=True)
class DetectionResult:
    score: float
    model_version: str
    explanation: str


class GhostDetectionEngine:
    """
    Detection engine.

    Current implementation:
        Hybrid weighted baseline.

    Future implementation:
        Replace predict() with a trained ML model
        such as XGBoost / LightGBM while preserving
        the same interface.
    """

    MODEL_VERSION = "baseline-v1"

    WEIGHTS = {
        "staleness_score": 0.25,
        "repost_score": 0.25,
        "cross_source_score": 0.15,
        "description_duplication_score": 0.20,
        "headcount_drift_score": 0.05,
        "detail_omission_score": 0.10,
    }

    def predict(
        self,
        features: DetectionFeatures,
    ) -> DetectionResult:

        score = (
            features.staleness_score
            * self.WEIGHTS["staleness_score"]
            + features.repost_score
            * self.WEIGHTS["repost_score"]
            + features.cross_source_score
            * self.WEIGHTS["cross_source_score"]
            + features.description_duplication_score
            * self.WEIGHTS["description_duplication_score"]
            + features.headcount_drift_score
            * self.WEIGHTS["headcount_drift_score"]
            + features.detail_omission_score
            * self.WEIGHTS["detail_omission_score"]
        )

        score = max(0.0, min(score, 1.0))

        explanation = self._build_explanation(features)

        return DetectionResult(
            score=round(score, 4),
            model_version=self.MODEL_VERSION,
            explanation=explanation,
        )

    @staticmethod
    def _build_explanation(
        features: DetectionFeatures,
    ) -> str:

        signals: list[str] = []

        if features.staleness_score >= 0.7:
            signals.append(
                "job has remained active for an unusually long period"
            )

        if features.repost_score >= 0.7:
            signals.append(
                "job description has been repeatedly reposted unchanged"
            )

        if features.cross_source_score >= 0.5:
            signals.append(
                "job appears across multiple recruiting sources"
            )

        if features.description_duplication_score >= 0.7:
            signals.append(
                "historical descriptions show high duplication"
            )

        if features.detail_omission_score >= 0.67:
            signals.append(
                "important job details are missing"
            )

        if not signals:
            return "No strong ghost-job signals detected."

        return "Potential signals: " + "; ".join(signals) + "."