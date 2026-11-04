import threading
from collections import deque
from dataclasses import dataclass

HISTORY = 120


@dataclass
class EEGData:
    attention:  int = 0
    meditation: int = 0
    delta:  int = 0
    theta:  int = 0
    alpha:  int = 0
    beta:   int = 0
    gamma:  int = 0


class EEGBuffer:
    """
    Buffer thread-safe que armazena EXATAMENTE os dados que chegam do sistema
    real (att_filtrada, estado, bloqueado). O gráfico lê apenas daqui.
    """
    def __init__(self):
        self._lock        = threading.Lock()

        # ── dados instantâneos ─────────────────────────────────────────────
        self.attention    = 0      # Att Filtrada atual
        self.meditation   = 0      # Meditação atual (se vier do headset)
        self.state        = "B"    # Estado atual (A/B/C/D/E)
        self.blocked      = False  # Bloqueado atual
        self.count        = 0      # nº de amostras recebidas (a UI anima quando muda)

        # ── histórico (para o gráfico de linha) ────────────────────────────
        self.att_hist   = deque([0.0] * HISTORY, maxlen=HISTORY)
        self.med_hist   = deque([0.0] * HISTORY, maxlen=HISTORY)

    # ------------------------------------------------------------------
    # Chamado pelo sistema de estado real com os mesmos valores do print
    # ------------------------------------------------------------------
    def update_from_state(self, att_filtrada: float, state: str, blocked: bool,
                          meditation: float = 0.0):
        """
        Recebe os valores que o console printa e os grava no buffer.
        O gráfico vai ler exatamente estes valores.
        """
        with self._lock:
            self.attention  = att_filtrada
            self.meditation = meditation
            self.state      = state
            self.blocked    = blocked
            self.att_hist.append(att_filtrada)
            self.med_hist.append(meditation)
            self.count += 1

    # Compatibilidade com código legado que chame update(EEGData)
    def update(self, data: EEGData):
        with self._lock:
            self.attention  = data.attention
            self.meditation = data.meditation
            self.att_hist.append(float(data.attention))
            self.med_hist.append(float(data.meditation))
            self.count += 1

    def snapshot(self):
        with self._lock:
            return {
                "attention":  self.attention,
                "meditation": self.meditation,
                "state":      self.state,
                "blocked":    self.blocked,
                "att_hist":   list(self.att_hist),
                "med_hist":   list(self.med_hist),
                "count":      self.count,
            }
