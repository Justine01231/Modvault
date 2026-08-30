from __future__ import annotations

import pytest

from app.services.guard import private_dm_only


class _Msg:
    def __init__(self):
        self.calls = 0
        self.replied = []

    async def reply_text(self, text, **kwargs):
        self.replied.append(text)


class _Chat:
    def __init__(self, chat_type):
        self.type = chat_type


class _User:
    def __init__(self, user_id):
        self.id = user_id


class _Update:
    def __init__(self, chat_type, user_id, msg):
        self.effective_chat = _Chat(chat_type)
        self.effective_user = _User(user_id)
        self.effective_message = msg
        self._user_id = user_id


async def _handler(update, context):
    update.effective_message.calls += 1
    return "ran"


@pytest.mark.asyncio
async def test_private_dm_runs_handler(monkeypatch):
    monkeypatch.setattr("app.services.guard.is_admin", lambda uid: True)
    msg = _Msg()
    upd = _Update("private", 8662749058, msg)
    result = await private_dm_only(_handler)(upd, None)
    assert result == "ran"
    assert msg.calls == 1
    assert msg.replied == []


@pytest.mark.asyncio
async def test_group_non_admin_silent(monkeypatch):
    monkeypatch.setattr("app.services.guard.is_admin", lambda uid: False)
    msg = _Msg()
    upd = _Update("supergroup", 123, msg)
    result = await private_dm_only(_handler)(upd, None)
    assert result is None
    assert msg.calls == 0
    assert msg.replied == []


@pytest.mark.asyncio
async def test_group_admin_redirected_to_dm(monkeypatch):
    monkeypatch.setattr("app.services.guard.is_admin", lambda uid: True)
    msg = _Msg()
    upd = _Update("supergroup", 8662749058, msg)
    result = await private_dm_only(_handler)(upd, None)
    assert result is None
    assert msg.calls == 0
    assert len(msg.replied) == 1
    assert "private chat" in msg.replied[0]
