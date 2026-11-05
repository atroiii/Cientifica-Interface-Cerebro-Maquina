from core.state_enum import State

class EEGStateMachine:
    def __init__(self, alpha=0.50):
        self.alpha = alpha
        self.att_filtrado = 0
        self.inicializado = False   # o filtro começa na primeira leitura válida
        self.estado_atual = State.B

    #metodo para filtra a atenção
    def _filtro_passa_baixa(self, valor_atual, valor_anterior):
        return self.alpha * valor_atual + (1 - self.alpha) * valor_anterior

    #metodo para saber qual o estado atual (para manda para o arduino posteriormente)
    #C, D e E ficam retidos até a atenção cair abaixo de 33 e então voltam para B
    def _transicao(self, att):
        match self.estado_atual:
            case State.A:
                if att >= 30:
                    self.estado_atual = State.B

            case State.B:
                if att < 20:
                    self.estado_atual = State.A
                elif att >= 85:
                    self.estado_atual = State.E
                elif att >= 75:
                    self.estado_atual = State.D
                elif att >= 65:
                    self.estado_atual = State.C

            case State.C:
                if att >= 85:
                    self.estado_atual = State.E
                elif att >= 75:
                    self.estado_atual = State.D
                elif att < 33:
                    self.estado_atual = State.B

            case State.D:
                if att >= 85:
                    self.estado_atual = State.E
                elif att < 33:
                    self.estado_atual = State.B

            case State.E:
                if att < 33:
                    self.estado_atual = State.B

    #metodo que receber a os dados atenção bruto, passa o filtro e retorna
    def processar(self, raw_attention) -> State:
        if not self.inicializado:
            # atenção 0 = pacote sem leitura válida: não inicializa o filtro
            if raw_attention == 0:
                return self.estado_atual
            self.att_filtrado = raw_attention
            self.inicializado = True
        else:
            self.att_filtrado = self._filtro_passa_baixa(raw_attention, self.att_filtrado)
        att = self.att_filtrado
        self._transicao(att)
        return self.estado_atual
