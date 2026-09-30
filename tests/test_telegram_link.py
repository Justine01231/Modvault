from __future__ import annotations

import httpx
import pytest

from app.services.telegram_link import (
    TelegramLinkError,
    _strip_html,
    parse_client_list,
    parse_link,
    repost_from_text,
)


def test_parse_link_ok():
    assert parse_link("https://t.me/modulostk/5536") == ("modulostk", "5536")
    assert parse_link("t.me/SomeChannel/123?single") == ("SomeChannel", "123")
    assert parse_link("telegram.me/abc/42") == ("abc", "42")


def test_parse_link_invalid():
    for bad in ("https://t.me/justtext", "https://github.com/a/b", "not a link"):
        with pytest.raises(TelegramLinkError):
            parse_link(bad)


def test_parse_link_excludes_private_prefixes():
    for bad in ("t.me/share/123", "t.me/joinchat/abc"):
        with pytest.raises(TelegramLinkError):
            parse_link(bad)


def test_strip_html():
    assert _strip_html("<b>Name</b> v1.0<br/><a href='x'>GitHub</a>") == "Name v1.0\nGitHub"


def test_repost_from_text_full():
    text = (
        "🎯 MetroFuse+ 7.0.12\n"
        "• A YouTube player\n"
        "× By caduHD4\n"
        "⚉ GitHub\n"
        "◉ Same post in other languages\n"
        "☬ @ModulOStk | Donations"
    )
    rd = repost_from_text(text, "modulostk", github_url="https://github.com/caduHD4/MetroFusePlus")
    assert rd.name == "MetroFuse+"
    assert rd.version == "7.0.12"
    assert rd.original_author == "caduHD4"
    assert rd.source == "https://github.com/caduHD4/MetroFusePlus"
    assert rd.original_channel == "@modulostk"
    assert "YouTube player" in rd.notes


def test_repost_from_text_minimal():
    rd = repost_from_text("Simple Module", "ch", "")
    assert rd.name == "Simple Module"
    assert rd.version == ""
    assert rd.original_author == ""
    assert rd.notes == ""


def test_parse_client_list():
    fragment = (
        '<a href="https://t.me/momogram_update" target="_blank">@momogram_update</a>'
        ' | <a href="https://github.com/im030/Momogram" target="_blank" rel="noopener">Github</a><br>'
        '<a href="https://t.me/NagramX" target="_blank">@NagramX</a>'
        ' | <a href="https://github.com/risin42/NagramX" target="_blank" rel="noopener">Github</a><br>'
        '<a href="https://t.me/OctoGramApp" target="_blank">OctoGram</a>'
        ' | <a href="https://github.com/OctoGramApp/OctoGram" target="_blank" rel="noopener">Github</a>'
    )
    entries = parse_client_list(fragment)
    assert len(entries) == 3
    assert entries[0] == ("momogram_update", "https://github.com/im030/Momogram", "@momogram_update")
    assert entries[1] == ("NagramX", "https://github.com/risin42/NagramX", "@NagramX")
    assert entries[2] == ("OctoGram", "https://github.com/OctoGramApp/OctoGram", "@OctoGramApp")


def test_parse_client_list_non_list():
    fragment = "<b>just text with no github links anywhere</b>"
    assert parse_client_list(fragment) == []
