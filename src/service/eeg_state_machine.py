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


class EEGStateMachine:
    def __init__(self, alpha=0.50):
        self.alpha = alpha
        self.att_filtrado = 0
        self.estado_atual = State.B
        self.bloqueado = False
        self.piso = State.B

    def _filtro_passa_baixa(self, valor_atual, valor_anterior):
        return self.alpha * valor_atual + (1 - self.alpha) * valor_anterior

    def _transicao(self, att):
        match self.estado_atual:
            case State.A:
                if att >= 30:
                    self.estado_atual = State.B

            case State.B:
                self.piso = State.B
                self.bloqueado = False
                if att < 20:
                    self.estado_atual = State.A
                elif att >= 85:
                    self.estado_atual = State.E
                    self.piso = State.E
                elif att >= 75:
                    self.estado_atual = State.D
                    self.piso = State.D
                elif att >= 65:
                    self.estado_atual = State.C
                    self.piso = State.C

            case State.C:
                if att >= 80:
                    self.estado_atual = State.E
                    self.piso = State.E
                elif att >= 75:
                    self.estado_atual = State.D
                    self.piso = State.D
                elif att < 33:
                    self.estado_atual = State.B

            case State.D:
                if att >= 85:
                    self.estado_atual = State.E
                    self.piso = State.E
                elif att < 33:
                    if self.piso <= State.D:
                        self.estado_atual = State.B
                        self.bloqueado = True

            case State.E:
                if att < 33:
                    if self.piso <= State.E:
                        self.estado_atual = State.B
                        self.bloqueado = True

    def processar(self, raw_attention) -> State:
        self.att_filtrado = self._filtro_passa_baixa(raw_attention, self.att_filtrado)
        att = self.att_filtrado
        self._transicao(att)
        return self.estado_atual
