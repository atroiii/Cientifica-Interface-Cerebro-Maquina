from enum import Enum


class State(Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"

    def __le__(self, other):
        order = [State.A, State.B, State.C, State.D, State.E]
        return order.index(self) <= order.index(other)

    def __lt__(self, other):
        order = [State.A, State.B, State.C, State.D, State.E]
        return order.index(self) < order.index(other)

    def __ge__(self, other):
        order = [State.A, State.B, State.C, State.D, State.E]
        return order.index(self) >= order.index(other)

    def __gt__(self, other):
        order = [State.A, State.B, State.C, State.D, State.E]
        return order.index(self) > order.index(other)
