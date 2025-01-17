from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from collections.abc import Hashable


class State(ABC):
    def __init__(self, statemachine: StateMachine):
        self.statemachine = statemachine

    @abstractmethod
    def enter(self) -> None: ...

    @abstractmethod
    def execute(self) -> None: ...

    @abstractmethod
    def exit(self) -> None: ...


@dataclass(slots=True)
class StateMachine:
    states: dict[Hashable, State] = None
    next_state: Hashable = None
    current_state: Hashable = None


def statemachine_initialise(
    statemachine: StateMachine,
    state_mapping: dict[Hashable, State],
    initial_state: Hashable
) -> None:
    # Iterate through all states and initialise (passing reference to self)
    for id, state in state_mapping.items():
        state_mapping[id] = state(statemachine)

    statemachine.states = state_mapping

    _statemachine_transition_state(statemachine, initial_state)


def statemachine_execute(statemachine: StateMachine, *args, **kwargs) -> None:
    statemachine.states[statemachine.current_state].execute(*args, **kwargs)

    # Perform state change
    if statemachine.next_state is not None:
        _statemachine_transition_state(statemachine, statemachine.next_state)


def statemachine_change_state(
    statemachine: StateMachine, new_state: Hashable
) -> None:
    statemachine.next_state = new_state


def _statemachine_transition_state(
    statemachine: StateMachine, new_state: Hashable
) -> None:
    if new_state not in statemachine.states:
        print(f"ERROR: {new_state} is unknown in statemachine mapping!")
        return

    # Exit current state if currently in one
    if statemachine.current_state is not None:
        statemachine.states[statemachine.current_state].exit()

    # Enter new state and set as current
    statemachine.states[new_state].enter()
    statemachine.current_state = new_state

    # Reset next_state to None
    statemachine.next_state = None
