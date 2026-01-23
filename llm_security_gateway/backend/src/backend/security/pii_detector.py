"""PII detection and masking using Presidio."""

from typing import Any

from backend.config.settings import get_settings
from backend.models.security import PIIDetection


class PIIDetector:
    """Detects and masks Personally Identifiable Information (PII) using Presidio."""

    def __init__(self):
        self.settings = get_settings()
        self._analyzer = None
        self._anonymizer = None
        self._initialized = False

    def _initialize(self):
        """Lazy initialization of Presidio components."""
        if self._initialized:
            return

        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_analyzer.nlp_engine import NlpEngineProvider
            from presidio_anonymizer import AnonymizerEngine

            # Explicitly configure NLP engine to avoid auto-download attempts
            nlp_config = {
                "nlp_engine_name": "spacy",
                "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
            }
            nlp_engine = NlpEngineProvider(nlp_configuration=nlp_config).create_engine()

            self._analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
            self._anonymizer = AnonymizerEngine()
            self._initialized = True
        except ImportError as e:
            print(f"Presidio not available: {e}")
            self._initialized = False
        except BaseException as e:
            # Catch all exceptions including SystemExit from spaCy model loading
            print(f"Presidio initialization failed (spaCy model may be missing): {e}")
            self._initialized = False

    @property
    def available(self) -> bool:
        """Check if Presidio is available."""
        self._initialize()
        return self._initialized and self._analyzer is not None

    def detect(self, text: str, language: str = "en") -> list[PIIDetection]:
        """
        Detect PII entities in text.

        Args:
            text: The text to analyze
            language: Language code (default: "en")

        Returns:
            List of PIIDetection objects for found PII
        """
        self._initialize()

        if not self.available:
            return []

        try:
            # Get entities to detect from settings
            entities = self.settings.pii_entities_to_detect

            # Run Presidio analyzer
            results = self._analyzer.analyze(
                text=text,
                entities=entities,
                language=language,
            )

            detections = []
            for result in results:
                # Get the detected text (partial for security)
                detected_text = text[result.start:result.end]
                partial_text = self._partial_mask(detected_text)

                detections.append(
                    PIIDetection(
                        entity_type=result.entity_type,
                        text=partial_text,
                        start=result.start,
                        end=result.end,
                        confidence=result.score,
                        masked_text=self._generate_mask(result.entity_type, len(detected_text)),
                    )
                )

            return detections

        except Exception as e:
            print(f"PII detection error: {e}")
            return []

    def mask(self, text: str, language: str = "en") -> tuple[str, list[PIIDetection]]:
        """
        Detect and mask PII in text.

        Args:
            text: The text to process
            language: Language code (default: "en")

        Returns:
            Tuple of (masked_text, list of detections)
        """
        self._initialize()

        if not self.available:
            return text, []

        try:
            from presidio_anonymizer.entities import OperatorConfig

            # Get entities to detect
            entities = self.settings.pii_entities_to_detect

            # Analyze text
            analyzer_results = self._analyzer.analyze(
                text=text,
                entities=entities,
                language=language,
            )

            if not analyzer_results:
                return text, []

            # Create operator configs for each entity type
            operators = {}
            for entity in entities:
                operators[entity] = OperatorConfig(
                    "replace",
                    {"new_value": f"<{entity}>"}
                )

            # Anonymize
            anonymized_result = self._anonymizer.anonymize(
                text=text,
                analyzer_results=analyzer_results,
                operators=operators,
            )

            # Build detection list
            detections = []
            for result in analyzer_results:
                detected_text = text[result.start:result.end]
                detections.append(
                    PIIDetection(
                        entity_type=result.entity_type,
                        text=self._partial_mask(detected_text),
                        start=result.start,
                        end=result.end,
                        confidence=result.score,
                        masked_text=f"<{result.entity_type}>",
                    )
                )

            return anonymized_result.text, detections

        except Exception as e:
            print(f"PII masking error: {e}")
            return text, []

    def _partial_mask(self, text: str) -> str:
        """Create a partial mask of detected text for logging."""
        if len(text) <= 4:
            return "*" * len(text)
        return text[:2] + "*" * (len(text) - 4) + text[-2:]

    def _generate_mask(self, entity_type: str, length: int) -> str:
        """Generate a mask placeholder for an entity."""
        return f"<{entity_type}>"

    def get_risk_score(self, text: str) -> float:
        """
        Calculate PII risk score.

        Args:
            text: The text to analyze

        Returns:
            Risk score from 0.0 to 1.0
        """
        detections = self.detect(text)

        if not detections:
            return 0.0

        # Weight different PII types
        weights = {
            "US_SSN": 1.0,
            "CREDIT_CARD": 1.0,
            "US_BANK_NUMBER": 0.9,
            "PERSON": 0.3,
            "EMAIL_ADDRESS": 0.5,
            "PHONE_NUMBER": 0.5,
            "IP_ADDRESS": 0.4,
            "LOCATION": 0.3,
            "DATE_TIME": 0.1,
        }

        max_score = 0
        for detection in detections:
            weight = weights.get(detection.entity_type, 0.5)
            score = weight * detection.confidence
            max_score = max(max_score, score)

        return min(1.0, max_score)


# Global instance
_detector: PIIDetector | None = None


def get_pii_detector() -> PIIDetector:
    """Get or create the PII detector."""
    global _detector
    if _detector is None:
        _detector = PIIDetector()
    return _detector
