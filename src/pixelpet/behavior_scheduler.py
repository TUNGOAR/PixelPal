"""行为调度：随机闲逛 + 主动搭讪。纯逻辑，不依赖 QTimer。"""
from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pixelpet.state_machine import StateMachine
    from pixelpet.config_manager import ConfigManager


class BehaviorScheduler:
    def __init__(self, state_machine: "StateMachine", config: "ConfigManager"):
        self.sm = state_machine
        self.cfg = config
        self._now = 0.0
        self._next_idle_walk_at = self._random_idle_walk()
        self._next_proactive_at = self._random_proactive()
        self._last_mouse_pos: tuple[int, int] | None = None
        self._last_mouse_at: float = 0.0
        self._mouse_idle_threshold = float(
            self.cfg.get("pet", "mouse_idle_threshold", 30)
        )

    def _random_idle_walk(self) -> float:
        a = self.cfg.get("pet", "idle_to_walk_min", 8)
        b = self.cfg.get("pet", "idle_to_walk_max", 25)
        return self._now + random.uniform(a, b)

    def _random_proactive(self) -> float:
        a = self.cfg.get("pet", "proactive_chat_min", 60)
        b = self.cfg.get("pet", "proactive_chat_max", 180)
        return self._now + random.uniform(a, b)

    def update_mouse_position(self, x: int, y: int, now: float) -> None:
        if self._last_mouse_pos != (x, y):
            self._last_mouse_pos = (x, y)
            self._last_mouse_at = now

    def tick(self, now: float) -> list[str]:
        self._now = now
        actions: list[str] = []

        # 1) 闲逛
        if self.sm.state.value == "idle" and now >= self._next_idle_walk_at:
            if self.sm.transition(self._event_tick_idle()):
                actions.append("walk")
                self._next_idle_walk_at = self._random_idle_walk()

        # 2) 主动搭讪
        if now >= self._next_proactive_at:
            idle_for = now - self._last_mouse_at
            if idle_for >= self._mouse_idle_threshold:
                if self.sm.transition(self._event_submit()):
                    actions.append("proactive_chat")
            # 不管成不成功都重排下次时间，避免连续触发
            self._next_proactive_at = self._random_proactive()

        return actions

    # ---- 避免在此文件 import 状态机的 Event（仅用于类型/解耦）
    def _event_tick_idle(self):
        from pixelpet.state_machine import Event
        return Event.TICK_IDLE

    def _event_submit(self):
        from pixelpet.state_machine import Event
        return Event.SUBMIT
