# =============================================================================
# MÁQUINA DE ESTADOS DA ICM (lógica principal do projeto, versão v2)
#
# O que este arquivo faz, passo a passo:
#   1. Recebe um valor de atenção bruto (0 a 100) do headset, um por pacote.
#   2. Suaviza esse valor com um filtro passa-baixa (média móvel exponencial).
#   3. Compara o valor suavizado com limiares e decide o estado: A, B, C, D ou E.
#   4. Devolve o estado. Quem chama (EEGSystem) manda a letra para o Arduino.
#
# Entrada: um inteiro de atenção por pacote (cerca de 1 por segundo).
# Saída: um State (A a E). Cada estado é um gesto da mão robótica:
#   A = distração, B = neutro, C = foco leve, D = foco alto, E = foco máximo.
#
# Ideia central: o estado depende do valor ATUAL e também do estado ANTERIOR.
# Isso é uma máquina de estados com histerese: para entrar numa faixa e para
# sair dela usamos limiares diferentes. Assim o gesto não fica "piscando"
# quando a atenção oscila perto de um limiar.
# =============================================================================
from core.state_enum import State

class EEGStateMachine:
    # Guarda três coisas entre um pacote e outro:
    #   - att_filtrado: o último valor suavizado (a "memória" do filtro);
    #   - inicializado: se o filtro já recebeu a primeira leitura válida;
    #   - estado_atual: o gesto atual. Começa em B (neutro, mão aberta),
    #     que é a mesma postura em que o Arduino liga.
    # alpha = 0.50 é o peso da leitura nova no filtro (ver _filtro_passa_baixa).
    def __init__(self, alpha=0.50):
        self.alpha = alpha
        self.att_filtrado = 0
        self.inicializado = False   # o filtro começa na primeira leitura válida
        self.estado_atual = State.B

    #metodo para filtra a atenção
    # Média móvel exponencial (EMA): y = alpha·x + (1 − alpha)·y_anterior.
    # Por que filtrar: a atenção do headset é ruidosa e pula bastante de um
    # segundo para o outro. A EMA "puxa" o valor para perto do histórico.
    # Com alpha = 0,5, a leitura nova e o histórico têm o mesmo peso.
    # Alpha maior reage mais rápido, mas deixa passar mais ruído.
    def _filtro_passa_baixa(self, valor_atual, valor_anterior):
        return self.alpha * valor_atual + (1 - self.alpha) * valor_anterior

    #metodo para saber qual o estado atual (para manda para o arduino posteriormente)
    #C, D e E ficam retidos até a atenção cair abaixo de 33 e então voltam para B
    # Regras de transição. Cada pacote só olha o "case" do estado atual,
    # então acontece no máximo UMA mudança de estado por pacote.
    #
    # Subida (B → C/D/E): sempre os mesmos limiares, 65 / 75 / 85.
    # Descida (C/D/E → B): um único limiar, 33, bem abaixo de 65.
    # Essa diferença é a "retenção" (histerese assimétrica):
    #   - um gesto de foco, depois de alcançado, não cai por uma oscilação
    #     pequena do sinal; só cai quando a atenção baixa de verdade (< 33);
    #   - não existe E→D, D→C nem E→C: a mão não "desce degrau por degrau",
    #     o que evitaria vários movimentos seguidos na descida;
    #   - o preço é atraso: o gesto alto fica mantido por mais tempo.
    #
    # Gesto A (distração) tem histerese própria: entra com < 20 e só sai com
    # >= 30. A folga de 10 pontos evita que um sinal parado perto de 20
    # fique alternando A, B, A, B a cada pacote.
    def _transicao(self, att):
        match self.estado_atual:
            case State.A:
                # Sai de A só quando a atenção sobe com folga (30, não 20).
                if att >= 30:
                    self.estado_atual = State.B

            case State.B:
                # B é o "centro": daqui se vai para qualquer outro gesto.
                # A ordem dos testes importa: o maior limiar é testado
                # primeiro, para um salto grande ir direto para o gesto certo.
                if att < 20:
                    self.estado_atual = State.A
                elif att >= 85:
                    self.estado_atual = State.E
                elif att >= 75:
                    self.estado_atual = State.D
                elif att >= 65:
                    self.estado_atual = State.C

            case State.C:
                # De C só se sobe (para D ou E) ou se volta para B abaixo de 33.
                # Entre 33 e 75, C fica retido.
                if att >= 85:
                    self.estado_atual = State.E
                elif att >= 75:
                    self.estado_atual = State.D
                elif att < 33:
                    self.estado_atual = State.B

            case State.D:
                # De D: sobe para E ou volta para B abaixo de 33.
                # Não há D → C: entre 33 e 85, D fica retido.
                if att >= 85:
                    self.estado_atual = State.E
                elif att < 33:
                    self.estado_atual = State.B

            case State.E:
                # E é o topo: só sai quando a atenção cai abaixo de 33.
                if att < 33:
                    self.estado_atual = State.B

    #metodo que receber a os dados atenção bruto, passa o filtro e retorna
    # Ponto de entrada, chamado uma vez por pacote.
    # Detalhe da partida: o filtro NÃO começa em 0. Ele começa na primeira
    # leitura válida. Se começasse em 0, os primeiros valores filtrados seriam
    # baixos. Exemplo com atenção constante 25: y = 12,5 no 1º pacote, abaixo
    # de 20, e a máquina iria para A. Como 25 nunca chega a 30, ficaria presa
    # em A. A versão v1 tinha esse problema (ensaio1_partida.md mostra 60 s
    # em A na v1 e 0 s na v2).
    def processar(self, raw_attention) -> State:
        if not self.inicializado:
            # atenção 0 = pacote sem leitura válida: não inicializa o filtro
            # (o headset manda 0 quando não há contato com a pele; usar esse 0
            # como valor inicial recriaria o problema da partida em 0).
            if raw_attention == 0:
                return self.estado_atual
            # Primeira leitura válida: vira o valor inicial, sem média.
            self.att_filtrado = raw_attention
            self.inicializado = True
        else:
            self.att_filtrado = self._filtro_passa_baixa(raw_attention, self.att_filtrado)
        # As regras de transição usam o valor FILTRADO, nunca o bruto.
        att = self.att_filtrado
        self._transicao(att)
        return self.estado_atual
