from dataclasses import dataclass

@dataclass
class EGGState:
    attention: float
    estado_atual : str = "B"
    bloqueado : bool = False

