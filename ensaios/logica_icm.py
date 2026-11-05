"""
Lógica de decisão da ICM isolada para ensaios de bancada (sem hardware).

NADA aqui altera o código original. Origem de cada trecho:

- `MaquinaReal` IMPORTA e usa, sem modificação, a classe
  `EEGStateMachine` de `src/services/eeg_state_machine.py` (filtro EMA nas
  linhas 12-13, transições nas linhas 16-60, `processar` nas linhas 63-67).
- `pacote_para_comando` reproduz o portão de `EEGSystem._on_eeg` em
  `src/services/eeg_state_sytem.py`, linhas 20-28:
      if data.attention == 0: return            # pacote ignorado
      novo_estado = self.maquina.processar(data.attention)
      self.arduino.enviar_estado(novo_estado.value)   # enviado A CADA pacote
- `MaquinaRealSemBloqueado` é uma CÓPIA LITERAL de `_transicao`
  (eeg_state_machine.py, linhas 16-60) com as atribuições a `self.bloqueado`
  removidas (linhas 8, 24, 54, 59). Serve só para provar numericamente que a
  variável `bloqueado` não influencia a saída (ver `verificar_equivalencia`).
- `ema` reproduz `_filtro_passa_baixa` (eeg_state_machine.py, linha 13):
      alpha * valor_atual + (1 - alpha) * valor_anterior
  com valor inicial 0 (linha 6: `self.att_filtrado = 0`).
- `FaixasSemTrava` e `HistereseClassica` NÃO existem no projeto: são
  lógicas de COMPARAÇÃO criadas para o ensaio, usando os limiares nominais
  20 / 65 / 75 / 85 (os da máquina real a partir do estado B, linhas 25-35).
"""
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

from core.state_enum import State                         # noqa: E402
from src.services.eeg_state_machine import EEGStateMachine  # noqa: E402

ALPHA_DO_CODIGO = EEGStateMachine().alpha   # lido do código (0.50), não digitado
GESTOS = "ABCDE"
LIMIARES_NOMINAIS = (20, 65, 75, 85)          # fronteiras inferiores de B, C, D, E


def faixa_nominal(x: float) -> str:
    """Faixa 'sem memória': A <20 ≤ B <65 ≤ C <75 ≤ D <85 ≤ E."""
    i = sum(x >= l for l in LIMIARES_NOMINAIS)
    return GESTOS[i]


def ema(alpha: float, atual: float, anterior: float) -> float:
    # reprodução de EEGStateMachine._filtro_passa_baixa (linha 13)
    return alpha * atual + (1 - alpha) * anterior


def pacote_para_comando(maquina, attention):
    """Reproduz EEGSystem._on_eeg (linhas 20-28): None = nada é enviado."""
    if attention == 0:
        return None
    return maquina.processar(attention)


# --------------------------------------------------------------------------
class MaquinaReal:
    """Código original, importado. alpha=1.0 equivale a 'sinal bruto'."""
    nome = "real"

    def __init__(self, alpha=ALPHA_DO_CODIGO):
        self.sm = EEGStateMachine(alpha=alpha)

    def processar(self, att) -> str:
        return self.sm.processar(att).value

    @property
    def y(self):
        return self.sm.att_filtrado


class MaquinaRealSemBloqueado:
    """Cópia de _transicao (linhas 16-60) sem nenhuma linha de `bloqueado`."""
    nome = "real_sem_bloqueado"

    def __init__(self, alpha=ALPHA_DO_CODIGO):
        self.alpha = alpha
        self.att_filtrado = 0
        self.estado_atual = State.B
        self.piso = State.B

    def _transicao(self, att):
        match self.estado_atual:
            case State.A:
                if att >= 30:
                    self.estado_atual = State.B
            case State.B:
                self.piso = State.B
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
            case State.E:
                if att < 33:
                    if self.piso <= State.E:
                        self.estado_atual = State.B

    def processar(self, att) -> str:
        self.att_filtrado = ema(self.alpha, att, self.att_filtrado)
        self._transicao(self.att_filtrado)
        return self.estado_atual.value

    @property
    def y(self):
        return self.att_filtrado


class FaixasSemTrava:
    """Comparação: faixa nominal do valor filtrado, sem memória de estado."""
    nome = "faixas_sem_trava"

    def __init__(self, alpha=ALPHA_DO_CODIGO):
        self.alpha, self.y = alpha, 0.0

    def processar(self, att) -> str:
        self.y = ema(self.alpha, att, self.y)
        return faixa_nominal(self.y)


class HistereseClassica:
    """Comparação: limiares nominais deslocados ±d (sobe com L+d, desce com L-d)."""
    nome = "histerese_3"

    def __init__(self, alpha=ALPHA_DO_CODIGO, d=3.0):
        self.alpha, self.d, self.y = alpha, d, 0.0
        self.i = 1  # começa em B, como a máquina real (linha 7)

    def processar(self, att) -> str:
        self.y = ema(self.alpha, att, self.y)
        L = LIMIARES_NOMINAIS
        while self.i < 4 and self.y >= L[self.i] + self.d:
            self.i += 1
        while self.i > 0 and self.y < L[self.i - 1] - self.d:
            self.i -= 1
        return GESTOS[self.i]


LOGICAS = {c.nome: c for c in (MaquinaReal, FaixasSemTrava, HistereseClassica)}


def verificar_equivalencia(sequencias, alphas):
    """Compara MaquinaReal x MaquinaRealSemBloqueado. Retorna (n_amostras, n_dif)."""
    n = dif = 0
    for a in alphas:
        for seq in sequencias:
            m1, m2 = MaquinaReal(a), MaquinaRealSemBloqueado(a)
            for x in seq:
                r1, r2 = pacote_para_comando(m1, x), pacote_para_comando(m2, x)
                n += 1
                dif += (r1 != r2) or (m1.y != m2.y)
    return n, dif
