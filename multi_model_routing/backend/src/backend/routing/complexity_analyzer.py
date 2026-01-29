"""Query complexity analyzer."""

import re
from dataclasses import dataclass

import tiktoken


@dataclass
class ComplexityBreakdown:
    """Breakdown of complexity score components."""

    token_score: float  # 15%
    vocabulary_score: float  # 20%
    question_depth_score: float  # 25%
    domain_score: float  # 20%
    multistep_score: float  # 20%
    total_score: int

    def to_dict(self) -> dict[str, float]:
        """Convert to dictionary."""
        return {
            "token_score": self.token_score,
            "vocabulary_score": self.vocabulary_score,
            "question_depth_score": self.question_depth_score,
            "domain_score": self.domain_score,
            "multistep_score": self.multistep_score,
            "total_score": float(self.total_score),
        }


class ComplexityAnalyzer:
    """Analyzes query complexity to determine appropriate model tier."""

    # Weights for each component
    TOKEN_WEIGHT = 0.15
    VOCABULARY_WEIGHT = 0.20
    QUESTION_DEPTH_WEIGHT = 0.25
    DOMAIN_WEIGHT = 0.20
    MULTISTEP_WEIGHT = 0.20

    # Question depth indicators
    DEEP_QUESTION_PATTERNS = [
        r"\bwhy\b",
        r"\bhow\s+does\b",
        r"\bhow\s+would\b",
        r"\bexplain\b",
        r"\banalyze\b",
        r"\bcompare\b",
        r"\bevaluate\b",
        r"\bwhat\s+if\b",
        r"\bimplications?\b",
        r"\bconsequences?\b",
    ]

    SHALLOW_QUESTION_PATTERNS = [
        r"\bwhat\s+is\b",
        r"\bwho\s+is\b",
        r"\bwhen\s+is\b",
        r"\bwhere\s+is\b",
        r"\bdefine\b",
        r"\blist\b",
    ]

    # Domain-specific terms indicating complexity
    TECHNICAL_DOMAINS = {
        "programming": [
            "algorithm",
            "complexity",
            "distributed",
            "concurrency",
            "optimization",
            "architecture",
            "microservices",
            "kubernetes",
            "machine learning",
            "neural network",
        ],
        "science": [
            "quantum",
            "molecular",
            "thermodynamic",
            "electromagnetic",
            "biochemical",
            "genomic",
            "astrophysics",
        ],
        "math": [
            "derivative",
            "integral",
            "matrix",
            "eigenvalue",
            "probability",
            "theorem",
            "proof",
            "topology",
        ],
        "legal": [
            "jurisdiction",
            "precedent",
            "statute",
            "liability",
            "constitutional",
        ],
        "medical": [
            "diagnosis",
            "pathology",
            "pharmacology",
            "etiology",
            "prognosis",
        ],
    }

    # Multi-step indicators
    MULTISTEP_PATTERNS = [
        r"\bstep\s*by\s*step\b",
        r"\bfirst\b.*\bthen\b",
        r"\band\s+also\b",
        r"\badditionally\b",
        r"\bmoreover\b",
        r"\bfurthermore\b",
        r"\bmultiple\b",
        r"\bseveral\b",
        r"\ball\s+of\b",
        r"\beach\s+of\b",
    ]

    def __init__(self) -> None:
        """Initialize the complexity analyzer."""
        try:
            self._tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self._tokenizer = None

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if self._tokenizer:
            return len(self._tokenizer.encode(text))
        # Fallback: rough estimate
        return len(text.split()) * 1.3

    def _calculate_token_score(self, text: str) -> float:
        """Calculate score based on token count (0-100)."""
        token_count = self._count_tokens(text)

        # Scoring brackets
        if token_count < 50:
            return 10
        elif token_count < 100:
            return 25
        elif token_count < 200:
            return 40
        elif token_count < 500:
            return 60
        elif token_count < 1000:
            return 80
        else:
            return 100

    def _calculate_vocabulary_score(self, text: str) -> float:
        """Calculate score based on vocabulary complexity (0-100)."""
        words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
        if not words:
            return 0

        # Average word length
        avg_length = sum(len(w) for w in words) / len(words)

        # Unique word ratio
        unique_ratio = len(set(words)) / len(words)

        # Long words ratio (>7 characters)
        long_words_ratio = sum(1 for w in words if len(w) > 7) / len(words)

        # Combine factors
        length_score = min(avg_length / 8, 1) * 40  # Max 40 for avg length
        unique_score = unique_ratio * 30  # Max 30 for uniqueness
        long_score = long_words_ratio * 30  # Max 30 for long words

        return length_score + unique_score + long_score

    def _calculate_question_depth_score(self, text: str) -> float:
        """Calculate score based on question depth (0-100)."""
        text_lower = text.lower()

        # Count deep question indicators
        deep_count = sum(
            1 for pattern in self.DEEP_QUESTION_PATTERNS if re.search(pattern, text_lower)
        )

        # Count shallow question indicators
        shallow_count = sum(
            1 for pattern in self.SHALLOW_QUESTION_PATTERNS if re.search(pattern, text_lower)
        )

        # Calculate base score
        if deep_count > 0 and shallow_count == 0:
            base_score = 70 + min(deep_count * 10, 30)
        elif deep_count > shallow_count:
            base_score = 50 + min(deep_count * 5, 30)
        elif shallow_count > deep_count:
            base_score = 20 + min(shallow_count * 5, 20)
        else:
            base_score = 40  # Neutral

        return min(base_score, 100)

    def _calculate_domain_score(self, text: str) -> float:
        """Calculate score based on domain specificity (0-100)."""
        text_lower = text.lower()
        domain_matches = 0
        domains_found: set[str] = set()

        for domain, terms in self.TECHNICAL_DOMAINS.items():
            for term in terms:
                if term in text_lower:
                    domain_matches += 1
                    domains_found.add(domain)

        # More matches and cross-domain = higher complexity
        match_score = min(domain_matches * 15, 60)
        cross_domain_score = min(len(domains_found) * 10, 40)

        return match_score + cross_domain_score

    def _calculate_multistep_score(self, text: str) -> float:
        """Calculate score based on multi-step indicators (0-100)."""
        text_lower = text.lower()

        # Count multi-step patterns
        pattern_count = sum(
            1 for pattern in self.MULTISTEP_PATTERNS if re.search(pattern, text_lower)
        )

        # Count question marks (multiple questions = more complex)
        question_count = text.count("?")

        # Count bullet points or numbered items
        list_items = len(re.findall(r"^\s*[-•*\d.]+\s+", text, re.MULTILINE))

        pattern_score = min(pattern_count * 20, 50)
        question_score = min(question_count * 15, 30)
        list_score = min(list_items * 5, 20)

        return min(pattern_score + question_score + list_score, 100)

    def analyze(self, text: str) -> ComplexityBreakdown:
        """
        Analyze query complexity.

        Returns a score from 0-100 where:
        - 0-30: Simple queries (FAST tier)
        - 31-70: Moderate queries (STANDARD tier)
        - 71-100: Complex queries (FRONTIER tier)
        """
        token_score = self._calculate_token_score(text)
        vocabulary_score = self._calculate_vocabulary_score(text)
        question_depth_score = self._calculate_question_depth_score(text)
        domain_score = self._calculate_domain_score(text)
        multistep_score = self._calculate_multistep_score(text)

        # Weighted total
        total = (
            token_score * self.TOKEN_WEIGHT
            + vocabulary_score * self.VOCABULARY_WEIGHT
            + question_depth_score * self.QUESTION_DEPTH_WEIGHT
            + domain_score * self.DOMAIN_WEIGHT
            + multistep_score * self.MULTISTEP_WEIGHT
        )

        return ComplexityBreakdown(
            token_score=round(token_score, 2),
            vocabulary_score=round(vocabulary_score, 2),
            question_depth_score=round(question_depth_score, 2),
            domain_score=round(domain_score, 2),
            multistep_score=round(multistep_score, 2),
            total_score=min(round(total), 100),
        )

    def get_messages_text(self, messages: list[dict]) -> str:
        """Extract text from messages for analysis."""
        texts = []
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                texts.append(content)
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        texts.append(item.get("text", ""))
        return " ".join(texts)
