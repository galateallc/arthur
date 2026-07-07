"""Tests for the Python side of the 3D face (payload + asset wiring)."""

from __future__ import annotations

import json

from kindalive.engine.chemicals import ChemicalState
from kindalive.expression.face import FACE_WEIGHTS, FaceProjection
from kindalive.expression.face_3d import (
    CONTAINER_ID,
    WEB_ASSETS_DIR,
    boot_js,
    boot_script,
    container_html,
    face_payload,
    payload_js,
)


def _neutral_face():
    return FaceProjection.compute(ChemicalState())


def test_payload_contains_all_twelve_muscles():
    payload = face_payload(_neutral_face())
    assert set(payload["muscles"]) == set(FACE_WEIGHTS)
    for value in payload["muscles"].values():
        assert 0.0 <= value <= 1.0


def test_payload_mood_defaults_and_clamping():
    payload = face_payload(_neutral_face())
    assert payload["mood"]["color"].startswith("#")
    assert 0.0 <= payload["mood"]["intensity"] <= 1.0

    hot = face_payload(_neutral_face(), mood_color="#C4513F",
                       mood_intensity=7.5)
    assert hot["mood"]["color"] == "#C4513F"
    assert hot["mood"]["intensity"] == 1.0

    cold = face_payload(_neutral_face(), mood_intensity=-3.0)
    assert cold["mood"]["intensity"] == 0.0


def test_payload_js_is_valid_json_inside_the_call():
    js = payload_js(face_payload(_neutral_face()))
    assert js.startswith("window.kindaliveFace && ")
    start = js.index("setTargets(") + len("setTargets(")
    blob = js[start:js.rindex(")")]
    parsed = json.loads(blob)
    assert "muscles" in parsed and "mood" in parsed


def test_container_and_boot_script_agree_on_id():
    assert f'id="{CONTAINER_ID}"' in container_html()
    assert f'initFace3D("{CONTAINER_ID}")' in boot_script()
    assert 'type="module"' in boot_script()


def test_boot_js_imports_and_boots_without_script_tag():
    """The run_javascript boot path is a bare dynamic import — no
    <script> wrapper to be stripped by HTML sanitization."""
    js = boot_js()
    assert "<script" not in js
    assert 'import("/webassets/face3d.js")' in js
    assert f'"{CONTAINER_ID}"' in js


def test_face3d_js_asset_exists_and_exposes_api():
    js_path = WEB_ASSETS_DIR / "face3d.js"
    assert js_path.exists()
    source = js_path.read_text()
    assert "window.kindaliveFace" in source
    assert "setTargets" in source
    assert "setSpeaking" in source       # lip-sync hook
    # All 12 muscles must be wired into the renderer
    for muscle in FACE_WEIGHTS:
        assert muscle in source, f"{muscle} not used by face3d.js"
    # The LED renderer is pure 2D canvas — no WebGL / Three.js dependency.
    assert "getContext(\"2d\")" in source
    assert "three" not in source.lower()
