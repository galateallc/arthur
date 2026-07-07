"""ExpressionOutput protocol — abstract interface for emotion expression."""

from __future__ import annotations

from typing import Protocol

from kindalive.engine.chemicals import ChemicalState
from kindalive.emotions.emotion_vector import EmotionVector


class ExpressionOutput(Protocol):
    async def express(self, emotions: EmotionVector, chemicals: ChemicalState) -> str:
        ...
