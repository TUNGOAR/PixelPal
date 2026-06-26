"""宠物状态机：定义合法转移，不负责计时。"""
from __future__ import annotations

from enum import Enum
from typing import Callable


class State(str, Enum):
    IDLE = "idle"
    WALK = "walk"
    CLICK = "click"
    CHAT = "chat"
    THINK = "think"


class Event(str, Enum):
    TICK_IDLE = "tick_idle"     # 闲逛计时到期
    TICK_WALK = "tick_walk"     # 行走时长到
    CLICK = "click"             # 鼠标点击
    CLICK_DONE = "click_done"   # CLICK 0.5s 自动结束
    SUBMIT = "submit"           # 用户提交输入
    CANCEL = "cancel"           # 用户取消
    TOKEN_START = "token_start" # LLM 开始流式返回
    TOKEN_END = "token_end"     # LLM 流式结束
    HIDE = "hide"
    SHOW = "show"


# 转移表：from_state -> {event: to_state}
_TRANSITIONS: dict[State, dict[Event, State]] = {
    State.IDLE: {
        Event.TICK_IDLE: State.WALK,
        Event.CLICK: State.CLICK,
        Event.SUBMIT: State.CHAT,
        Event.HIDE: State.IDLE,
    },
    State.WALK: {
        Event.TICK_WALK: State.IDLE,
        Event.CLICK: State.CLICK,
        Event.SUBMIT: State.CHAT,
        Event.HIDE: State.WALK,
    },
    State.CLICK: {
        # 调用方在 0.5s 后通过 CLICK_AGAIN 回到 previous_state；
        # 但为简单，使用专门的 click_done 事件：
    },
    State.CHAT: {
        Event.CANCEL: State.IDLE,
        Event.TOKEN_START: State.THINK,
        Event.HIDE: State.CHAT,
    },
    State.THINK: {
        Event.TOKEN_END: State.CHAT,
        Event.CANCEL: State.IDLE,
        Event.HIDE: State.THINK,
    },
}


class StateMachine:
    def __init__(self):
        self._state = State.IDLE
        self._previous: State | None = None
        self.on_change: list[Callable[[State, State], None]] = []

    @property
    def state(self) -> State:
        return self._state

    @property
    def previous_state(self) -> State | None:
        return self._previous

    def transition(self, event: Event) -> bool:
        # CLICK 状态：CLICK_DONE 显式事件 或 任何非 HIDE 事件 = 回到 previous_state
        if self._state == State.CLICK and event != Event.HIDE:
            back = self._previous or State.IDLE
            old = self._state
            self._previous = None
            self._state = back
            self._fire(old, back)
            return True

        mapping = _TRANSITIONS.get(self._state, {})
        target = mapping.get(event)
        if target is None:
            return False

        old = self._state
        self._previous = old
        self._state = target
        self._fire(old, target)
        return True

    def _fire(self, old: State, new: State) -> None:
        for cb in self.on_change:
            cb(old, new)
