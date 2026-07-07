"""UserText — the single input type for the freeform-paragraph pipeline.

A `UserText` is a paragraph the owner typed: a single event ("you won
the lottery"), a stack of events, or a mix of discrete events and
ambient conditions ("Friday, finances up, and tomorrow I have off").
The LLM interpreter is the only consumer.

The constants `SOURCE` and `EVENT_TYPE` are the only values the
`source` / `event_type` fields ever take — they exist because the
prompt builder and cache key on them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

SOURCE = "user"
EVENT_TYPE = "freeform"


@dataclass
class UserText:
    """A paragraph of natural-language text from the robot's owner."""

    summary: str
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Constants exposed as attributes so legacy code that reads
    # `event.source` / `event.event_type` keeps working unchanged.
    source: str = SOURCE
    event_type: str = EVENT_TYPE
    raw_data: dict[str, Any] = field(default_factory=dict)
    urgency: str = "realtime"
