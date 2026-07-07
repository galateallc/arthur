"""Guards for the mobile/PWA support: manifest, icon, responsive CSS."""

from __future__ import annotations

import json

from kindalive.expression.face_3d import WEB_ASSETS_DIR


def test_manifest_is_valid_and_installable():
    manifest_path = WEB_ASSETS_DIR / "manifest.json"
    assert manifest_path.exists()
    data = json.loads(manifest_path.read_text())
    assert data["name"]
    assert data["display"] == "standalone"      # launches like an app
    assert data["start_url"] == "/"
    assert data["icons"], "manifest needs at least one icon"
    assert data["icons"][0]["src"] == "/webassets/icon.svg"


def test_icon_exists():
    assert (WEB_ASSETS_DIR / "icon.svg").exists()


def test_css_has_responsive_layout():
    css = (WEB_ASSETS_DIR / "style.css").read_text()
    assert "@media" in css, "no responsive breakpoint in style.css"
    assert ".kl-col-face" in css
    # 16px inputs prevent iOS Safari from auto-zooming on focus.
    assert "16px" in css


def test_face_renderer_is_mobile_aware():
    js = (WEB_ASSETS_DIR / "face3d.js").read_text()
    # Caps the device pixel ratio and reflows on container resize /
    # orientation change so the LED panel stays sharp and sized on phones.
    assert "devicePixelRatio" in js
    assert "ResizeObserver" in js


def test_web_ui_emits_viewport_and_manifest():
    """The page head must advertise mobile viewport + the PWA manifest."""
    import inspect

    from kindalive.expression import web_ui

    src = inspect.getsource(web_ui._build_page)
    assert "width=device-width" in src
    assert "manifest.json" in src
    assert "apple-mobile-web-app-capable" in src
