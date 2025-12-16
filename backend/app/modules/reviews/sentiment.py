from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from deep_translator import GoogleTranslator
from starlette.concurrency import run_in_threadpool
from textblob import TextBlob


@dataclass(frozen=True)
class SentimentResult:
    score: Optional[int]
    polarity: Optional[float]
    subjectivity: Optional[float]


def _polarity_to_score(polarity: float) -> int:
    score = int(round((polarity + 1.0) * 50))
    return max(0, min(100, score))


def _analyze_sentiment_sync(text: str) -> SentimentResult:
    raw = (text or "").strip()
    if not raw:
        return SentimentResult(score=None, polarity=None, subjectivity=None)

    analyzed_text = raw
    try:
        translated = GoogleTranslator(source="auto", target="en").translate(raw)
        if isinstance(translated, str) and translated.strip():
            analyzed_text = translated.strip()
    except Exception:
        analyzed_text = raw

    try:
        sentiment = TextBlob(analyzed_text).sentiment
        polarity = float(getattr(sentiment, "polarity", 0.0))
        subjectivity = float(getattr(sentiment, "subjectivity", 0.0))
        return SentimentResult(
            score=_polarity_to_score(polarity),
            polarity=polarity,
            subjectivity=subjectivity,
        )
    except Exception:
        return SentimentResult(score=None, polarity=None, subjectivity=None)


async def analyze_review_sentiment(text: str) -> SentimentResult:
    return await run_in_threadpool(_analyze_sentiment_sync, text)

