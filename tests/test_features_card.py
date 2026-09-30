from __future__ import annotations

from app.services.features import get_features, has_features
from app.services.formatter import format_release
from app.services.module_parser import ModuleMetadata
from app.services.templates.module_card import (
    FEATURES_HEADER_EXPANDED,
    render_module_card,
)


def _meta(**kwargs) -> ModuleMetadata:
    defaults = dict(
        module_id="gpuboost",
        name="Universal GPU Boost",
        version="v1.0",
        version_code="1",
        author="MODULAB",
        description="One module, multiple GPU platforms.",
        support="Magisk",
        category="Magisk",
    )
    defaults.update(kwargs)
    return ModuleMetadata(**defaults)


def test_features_registry():
    assert get_features("Universal GPU Boost") is not None
    assert len(get_features("Universal GPU Boost")) == 6
    assert has_features("Some Other Module") is False
    assert get_features(None) is None


def test_feature_card_shows_features_inline():
    text = format_release(_meta(), file_size="9.4 KB")
    # Features section present, expanded, right below description
    assert "🎯 <b>Universal GPU Boost</b>" in text
    assert FEATURES_HEADER_EXPANDED in text
    assert "- WebUI Control" in text
    assert "- Thermal Safe" in text
    # version/author/tags after the features block
    assert "📦 v1.0 • 9.4 KB" in text
    assert "👤 MODULAB" in text
    assert "#Magisk" in text


def test_feature_card_no_collapse_arrow_below_footer():
    from app.services.footer import append_footer

    text = append_footer(format_release(_meta(), file_size="9.4 KB"))
    # no inline button/arrow after the footer region
    assert "Follow" in text
    assert "Join" in text
    # the "▾ Features:" marker sits inside the body, not after the footer
    body_idx = text.index(FEATURES_HEADER_EXPANDED)
    footer_idx = text.index("Follow")
    assert body_idx < footer_idx
    # nothing after the footer is part of a collapsible control
    assert "▾" not in text[footer_idx:]
    assert "▸" not in text[footer_idx:]


def test_module_without_features_has_no_features_section():
    meta = _meta(
        name="OnyxZygisk",
        module_id="example",
        description="A test module",
        support="Magisk",
    )
    text = format_release(meta, file_size="1.2 MB")
    assert "Features" not in text
    assert "▾" not in text
    assert "🧩 <b>OnyxZygisk</b>" not in text  # legacy card uses its own header
    assert "⚡ MODULAB • RELEASE" in text


def test_render_module_card_without_features_omits_block():
    text = render_module_card(name="Tool", features=None)
    assert "Features" not in text
    assert "▾" not in text
