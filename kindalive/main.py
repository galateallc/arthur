"""Kindalive CLI entry point — interpret a paragraph of freeform text.

Usage:
    python3 -m kindalive.main --text "you won the lottery"
    python3 -m kindalive.main --text "Friday, finances up, day off tomorrow" \\
        --personality cheerful
    echo "the cat is missing" | python3 -m kindalive.main --personality anxious

Reads `ANTHROPIC_API_KEY` from the environment (or a nearby `.env` file
via :mod:`kindalive.env_loader`). Without a key, the LLM is skipped and
the default fallback nudge is applied instead.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

from kindalive.engine.chemicals import Chemical, ChemicalState
from kindalive.engine.clock import ManualClock
from kindalive.env_loader import load_dotenv
from kindalive.interpreter.llm_interpreter import LLMBackend
from kindalive.robot import Robot


def _render_levels(state: ChemicalState, width: int = 24) -> str:
    """Plain-text bar chart of the 8 chemical levels."""
    lines = []
    for chem in Chemical:
        level = state.get(chem)
        filled = round(level * width)
        bar = "█" * filled + "░" * (width - filled)
        lines.append(f"{chem.value:<13} {bar} {level:.2f}")
    return "\n".join(lines)


def _read_text(arg_text: str | None) -> str:
    """Resolve the input paragraph: --text flag wins, else stdin."""
    if arg_text is not None:
        return arg_text.strip()
    if sys.stdin.isatty():
        return ""
    return sys.stdin.read().strip()


def _build_backend(no_llm: bool) -> LLMBackend | None:
    if no_llm:
        return None
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return None
    # Lazy import — `anthropic` is only required when an API key is set.
    from kindalive.interpreter.anthropic_backend import AnthropicBackend
    return AnthropicBackend(api_key=api_key)


async def _run(text: str, personality: str, backend: LLMBackend | None) -> int:
    robot = Robot(
        personality=personality,
        clock=ManualClock(),
        llm_backend=backend,
    )

    impulses = await robot.interpret_text(text)

    print(f"text: {text!r}")
    print(f"personality: {personality}")
    if backend is None:
        print("path: no LLM (used default fallback nudge)")
    elif robot.interpreter is not None:
        print(f"path: {robot.interpreter.last_path}")
        if robot.interpreter.last_error:
            print(f"error: {robot.interpreter.last_error}")
    print()

    if impulses:
        print("impulses:")
        for imp in impulses:
            sign = "+" if imp.delta >= 0 else ""
            dur = (
                f" over {imp.duration_seconds:.0f}s"
                if imp.duration_seconds > 0
                else ""
            )
            print(f"  {imp.chemical.value:<13} {sign}{imp.delta:.2f}{dur}")
    else:
        print("impulses: (none)")
    print()

    print(_render_levels(robot.current_chemicals()))
    emotions = robot.current_emotions()
    dominant_name, dominant_value = emotions.dominant()
    print(f"\ndominant emotion: {dominant_name} ({dominant_value:.2f})")
    return 0


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(
        description=(
            "Interpret a paragraph of freeform text as a chemical impulse "
            "signature on a Kindalive robot."
        ),
    )
    parser.add_argument(
        "--text",
        default=None,
        help="Paragraph to interpret. If omitted, reads from stdin.",
    )
    parser.add_argument(
        "--personality",
        default="default",
        choices=["default", "cheerful", "stoic", "anxious"],
        help="Robot personality preset (default: default)",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Skip the LLM and use the default fallback nudge.",
    )
    args = parser.parse_args()

    text = _read_text(args.text)
    if not text:
        parser.error("no text provided (pass --text or pipe via stdin)")

    backend = _build_backend(args.no_llm)
    rc = asyncio.run(_run(text, args.personality, backend))
    sys.exit(rc)


if __name__ == "__main__":
    main()
