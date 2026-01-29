"""Semantic query classification using keyword matching."""

import logging
import re
from functools import lru_cache

from backend.config import QueryCategory

logger = logging.getLogger(__name__)


class SemanticRouter:
    """Routes queries to categories using keyword-based classification."""

    def __init__(self, model_name: str = "") -> None:
        pass

    def classify(self, text: str) -> tuple[QueryCategory, dict[str, float]]:
        """
        Classify query into a category using keyword matching.

        Returns:
            Tuple of (best category, dict of all category scores)
        """
        text_lower = text.lower()

        coding_keywords = [
            "code", "function", "error", "bug", "implement", "python",
            "javascript", "api", "database", "class", "method", "variable",
            "compile", "runtime", "syntax", "debug", "deploy", "docker",
        ]
        math_keywords = [
            "calculate", "solve", "equation", "derivative", "integral",
            "probability", "formula", "theorem", "proof", "algebra",
            "differential", "matrix", "eigenvalue", "calculus", "logarithm",
            "trigonometry", "geometry", "dy/dx", "limit", "summation",
        ]
        creative_keywords = [
            "write", "story", "poem", "creative", "generate", "fiction",
            "imagine", "compose", "narrative", "song",
        ]
        research_keywords = [
            "research", "study", "literature", "analysis", "review",
            "trends", "survey", "findings", "evidence", "data",
        ]
        reasoning_keywords = [
            "why", "explain", "analyze", "implications", "compare",
            "evaluate", "consequence", "trade-off", "reason", "cause",
        ]
        chat_keywords = [
            "hello", "hi", "thanks", "bye", "how are you", "hey",
            "good morning", "good night", "thank you",
        ]

        def count_matches(keywords: list[str]) -> int:
            count = 0
            for kw in keywords:
                # Use word boundary matching for short keywords to avoid
                # false positives from substring matching (e.g. "class" in
                # "classification"). Longer keywords and those with special
                # chars (like "dy/dx") use simple containment.
                if len(kw) <= 5 and kw.isalpha():
                    if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                        count += 1
                else:
                    if kw in text_lower:
                        count += 1
            return count

        matches = {
            QueryCategory.CODING: count_matches(coding_keywords),
            QueryCategory.MATH: count_matches(math_keywords),
            QueryCategory.CREATIVE: count_matches(creative_keywords),
            QueryCategory.RESEARCH: count_matches(research_keywords),
            QueryCategory.REASONING: count_matches(reasoning_keywords),
            QueryCategory.CHAT: count_matches(chat_keywords),
            QueryCategory.QA: 1,  # Default baseline
        }

        total = sum(matches.values()) or 1
        scores: dict[str, float] = {}
        for cat, count in matches.items():
            scores[cat.value] = round(count / total, 4)

        best_category = max(matches, key=lambda k: matches[k])
        return best_category, scores


@lru_cache(maxsize=1)
def get_semantic_router(model_name: str = "") -> SemanticRouter:
    """Get cached semantic router instance."""
    return SemanticRouter()
