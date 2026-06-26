import pytest
from pixelpet.state_machine import StateMachine, State, Event


def test_initial_state_is_idle():
    sm = StateMachine()
    assert sm.state == State.IDLE


def test_idle_to_walk_on_tick_idle():
    sm = StateMachine()
    assert sm.transition(Event.TICK_IDLE) is True
    assert sm.state == State.WALK


def test_walk_to_idle_on_tick_walk():
    sm = StateMachine()
    sm.transition(Event.TICK_IDLE)  # IDLE -> WALK
    assert sm.transition(Event.TICK_WALK) is True
    assert sm.state == State.IDLE


def test_click_stays_in_click_short_then_returns():
    sm = StateMachine()
    sm.transition(Event.TICK_IDLE)  # -> WALK
    assert sm.transition(Event.CLICK) is True
    assert sm.state == State.CLICK
    assert sm.previous_state == State.WALK
    # 不主动回退；调用方需负责


def test_click_done_returns_to_previous():
    sm = StateMachine()
    sm.transition(Event.TICK_IDLE)  # IDLE -> WALK
    sm.transition(Event.CLICK)      # -> CLICK
    assert sm.transition(Event.CLICK_DONE) is True
    assert sm.state == State.WALK
    assert sm.previous_state is None


def test_chat_to_think_to_chat():
    sm = StateMachine()
    sm.transition(Event.SUBMIT)  # IDLE -> CHAT
    assert sm.state == State.CHAT
    sm.transition(Event.TOKEN_START)  # -> THINK
    assert sm.state == State.THINK
    sm.transition(Event.TOKEN_END)  # -> CHAT
    assert sm.state == State.CHAT


def test_on_change_callback_fires():
    sm = StateMachine()
    log = []
    sm.on_change.append(lambda old, new: log.append((old, new)))
    sm.transition(Event.TICK_IDLE)
    assert log == [(State.IDLE, State.WALK)]


def test_invalid_transition_returns_false():
    sm = StateMachine()
    # 当前 IDLE，发 TOKEN_START 是非法
    assert sm.transition(Event.TOKEN_START) is False
    assert sm.state == State.IDLE


def test_cancel_from_chat_returns_idle():
    sm = StateMachine()
    sm.transition(Event.SUBMIT)
    assert sm.transition(Event.CANCEL) is True
    assert sm.state == State.IDLE
