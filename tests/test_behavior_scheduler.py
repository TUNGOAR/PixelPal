import pytest
from pathlib import Path
from pixelpet.config_manager import ConfigManager
from pixelpet.state_machine import StateMachine, State, Event
from pixelpet.behavior_scheduler import BehaviorScheduler


@pytest.fixture
def scheduler(tmp_path):
    cfg = ConfigManager(tmp_path / "config.yaml")
    sm = StateMachine()
    return BehaviorScheduler(sm, cfg), sm


def test_initial_tick_no_action(scheduler):
    bs, _ = scheduler
    # 第一秒：刚启动，无任何计时到期
    assert bs.tick(now=0.0) == []


def test_walk_after_idle_interval(scheduler):
    bs, sm = scheduler
    # 强制把内部计时器拉到 idle_to_walk_min 之后
    bs._next_idle_walk_at = 0.0
    actions = bs.tick(now=10.0)
    assert "walk" in actions
    assert sm.state == State.WALK


def test_proactive_chat_blocked_when_mouse_active(scheduler):
    bs, _ = scheduler
    bs._next_proactive_at = 0.0
    # 假设鼠标刚刚移动过
    bs.update_mouse_position(100, 100, now=9.9)
    actions = bs.tick(now=10.0)
    assert "proactive_chat" not in actions


def test_proactive_chat_fires_when_mouse_idle(scheduler):
    bs, sm = scheduler
    bs._next_proactive_at = 0.0
    # 上次鼠标移动在 9.0 秒前；现在 10.0；静止 1.0s，但仍 < mouse_idle_threshold(30)
    bs.update_mouse_position(100, 100, now=9.0)
    # 把鼠标静止阈值覆盖为 0.5 方便测试
    bs._mouse_idle_threshold = 0.5
    actions = bs.tick(now=10.0)
    assert "proactive_chat" in actions
    assert sm.state == State.CHAT
