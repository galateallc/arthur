"""Tests for the web UI: smoke tests + Robot.last_impulses behavior."""

from __future__ import annotations

import pytest

from kindalive.engine.chemicals import Chemical
from kindalive.engine.impulse import ChemicalImpulse
from kindalive.interpreter.text_input import UserText
from kindalive.robot import Robot


def test_web_ui_module_imports():
    """Smoke test: the web_ui module imports without error."""
    from kindalive.expression import web_ui  # noqa: F401

    assert hasattr(web_ui, "create_app")
    assert hasattr(web_ui, "main")


def test_web_ui_wires_the_face():
    """The UI is built around the LED dot-matrix face."""
    from kindalive.expression import web_ui

    assert hasattr(web_ui, "FaceProjection")
    assert hasattr(web_ui, "face_payload")
    assert hasattr(web_ui, "container_html")


def test_appstate_reset_clears_chemistry_and_conversation():
    """Reset rebuilds the robot (near baseline, within the jitter) and
    forgets the conversation."""
    from kindalive.expression.web_ui import RESET_JITTER, AppState

    state = AppState()
    # Perturb chemistry far past the jitter and seed a conversation turn.
    state.robot.current_chemicals().set(Chemical.CORTISOL, 0.95)
    state.robot._conversation.append({"role": "user", "content": "hi"})

    state.reset()

    assert state.robot.conversation == []
    chem = state.robot.current_chemicals()
    baseline = chem.baseline(Chemical.CORTISOL)
    # No longer 0.95, and within the reset jitter of baseline.
    assert abs(chem.get(Chemical.CORTISOL) - baseline) <= RESET_JITTER + 1e-9


def test_reset_starting_state_is_jittered_and_valid():
    """A fresh robot is nudged off baseline (not always calm) but stays
    within range and within the jitter band."""
    from kindalive.expression.web_ui import RESET_JITTER, AppState

    moved = False
    for _ in range(8):
        state = AppState()
        chem = state.robot.current_chemicals()
        for c in Chemical:
            level = chem.get(c)
            assert 0.0 <= level <= 1.0
            assert abs(level - chem.baseline(c)) <= RESET_JITTER + 1e-9
            if abs(level - chem.baseline(c)) > 1e-6:
                moved = True
    assert moved, "reset never perturbed any chemical"


def test_web_ui_create_app_constructs():
    """create_app() must run without error — guards static-file
    registration and page construction."""
    from kindalive.expression import web_ui

    state = web_ui.create_app()
    assert state is not None
    assert state.robot is not None


def test_web_ui_palettes_cover_all_series():
    from kindalive.expression import web_ui

    assert set(web_ui.CHEMICAL_COLORS) == {c.value for c in Chemical}
    emotions = web_ui.AppState().robot.current_emotions().as_dict()
    assert set(web_ui.EMOTION_COLORS) == set(emotions)


@pytest.mark.asyncio
async def test_interpret_text_wraps_user_event():
    """Robot.interpret_text wraps text into a `user/freeform` event."""
    robot = Robot(personality="default")

    received = []
    original = robot.process_event

    async def spy(event):
        received.append(event)
        await original(event)

    robot.process_event = spy  # type: ignore[assignment]
    await robot.interpret_text("you won the lottery")

    assert len(received) == 1
    evt = received[0]
    assert evt.source == "user"
    assert evt.event_type == "freeform"
    assert evt.summary == "you won the lottery"


# ---------------------------------------------------------------------------
# Companion API — POST /api/say
# ---------------------------------------------------------------------------


def _api_client():
    """Fresh app state + a test client against the (global) NiceGUI app."""
    from fastapi.testclient import TestClient
    from nicegui import app

    from kindalive.expression import web_ui

    state = web_ui.create_app()
    return state, TestClient(app)


def test_api_say_feeds_the_robot():
    """POST /api/say runs the text through the same pipeline as the
    textarea: impulses apply, and the response reports the outcome."""
    state, client = _api_client()

    resp = client.post("/api/say", json={"text": "your owner won the lottery"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["path"] == "fallback"  # no LLM backend in unit tests
    assert data["impulses"], "expected at least the fallback nudge"
    assert all(
        Chemical.from_string(i["chemical"]) in Chemical for i in data["impulses"]
    )
    assert data["dominant_emotion"]["name"]
    assert 0.0 <= data["dominant_emotion"]["level"] <= 1.0
    # The robot actually received the impulses...
    assert state.robot.last_impulses
    # ...and the open page is flagged to surface the exchange.
    assert state.external_seq == 1
    assert state.external_text == "your owner won the lottery"
    # Image-only integrations get an absolute, cache-busted face URL.
    assert data["face_url"].startswith("http")
    assert data["face_url"].endswith("/face.png?seq=1")


def test_face_png_serves_the_current_expression():
    """GET /face.png returns a PNG of the live face; the snapshot
    changes when the chemistry changes."""
    state, client = _api_client()

    resp = client.get("/face.png")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    assert resp.headers["cache-control"] == "no-store"
    assert resp.content[:8] == b"\x89PNG\r\n\x1a\n"

    # Shove the chemistry somewhere expressive; the image must differ.
    state.robot.current_chemicals().set(Chemical.CORTISOL, 1.0)
    state.robot.current_chemicals().set(Chemical.ADRENALINE, 1.0)
    assert client.get("/face.png").content != resp.content


def test_api_say_rejects_bad_bodies():
    """Empty, missing, or non-JSON text is a 400, and nothing reaches
    the robot."""
    state, client = _api_client()

    assert client.post("/api/say", json={"text": "   "}).status_code == 400
    assert client.post("/api/say", json={}).status_code == 400
    assert client.post("/api/say", json={"text": None}).status_code == 400
    assert client.post("/api/say", json={"text": 42}).status_code == 400
    assert client.post("/api/say", json=[1, 2]).status_code == 400
    assert client.post(
        "/api/say",
        content=b"not json",
        headers={"Content-Type": "application/json"},
    ).status_code == 400

    assert state.robot.last_impulses == []
    assert state.external_seq == 0


# ---------------------------------------------------------------------------
# Robot.last_impulses
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_robot_last_impulses_after_fallback():
    """Fallback-only Robot populates last_impulses after process_event."""
    robot = Robot(personality="default")
    await robot.process_event(UserText(summary="Team wins!"))
    assert len(robot.last_impulses) > 0
    assert all(isinstance(i, ChemicalImpulse) for i in robot.last_impulses)


def test_robot_last_impulses_after_receive():
    """receive_impulses() stores last_impulses."""
    robot = Robot(personality="default")
    impulses = [
        ChemicalImpulse(chemical=Chemical.DOPAMINE, delta=0.2),
        ChemicalImpulse(chemical=Chemical.SEROTONIN, delta=0.1),
    ]
    robot.receive_impulses(impulses)
    assert len(robot.last_impulses) == 2
    assert robot.last_impulses[0].chemical == Chemical.DOPAMINE
    assert robot.last_impulses[1].chemical == Chemical.SEROTONIN


@pytest.mark.asyncio
async def test_robot_last_impulses_reset_between_events():
    """last_impulses reflects the most recent event, not a prior one."""
    robot = Robot(personality="default")
    await robot.process_event(UserText(summary="Win!"))
    first = list(robot.last_impulses)
    await robot.process_event(UserText(summary="Rain"))
    second = list(robot.last_impulses)
    assert len(first) > 0
    assert len(second) > 0


def test_robot_last_impulses_starts_empty():
    """Before any event, last_impulses is empty."""
    robot = Robot(personality="default")
    assert robot.last_impulses == []
