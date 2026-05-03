from dataclasses import dataclass

@dataclass
class EGGState:
    attention: float
    meditation: float
    delta: float
    theta: float
    alpha: float
    beta: float
    gamma: float
    estado_atual : str = "B"
    bloqueado : bool = False

