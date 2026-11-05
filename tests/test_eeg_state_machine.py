"""Testes da máquina de estados (src/services/eeg_state_machine.py).

Rodar da raiz do repositório:  python -m pytest
"""
import math

import pytest

from core.state_enum import State
from src.services.eeg_state_machine import EEGStateMachine

A, B, C, D, E = State.A, State.B, State.C, State.D, State.E


def em_estado(estado):
    sm = EEGStateMachine()
    sm.estado_atual = estado
    return sm


# ── 1. Tabela de limiares: cada transição, dos dois lados de cada limiar ─────
TABELA = [
    # (estado atual, y filtrado, próximo estado)
    (A, 29.99, A), (A, 30, B), (A, 0.5, A), (A, 100, B),          # A→B só com y ≥ 30
    (B, 20, B), (B, 19.99, A),                                    # B→A com y < 20
    (B, 64.99, B), (B, 65, C), (B, 74.99, C),                     # B→C com 65 ≤ y < 75
    (B, 75, D), (B, 84.99, D),                                    # B→D com 75 ≤ y < 85
    (B, 85, E), (B, 100, E),                                      # B→E com y ≥ 85
    (C, 74.99, C), (C, 75, D), (C, 80, D), (C, 84.99, D),         # C→D com 75 ≤ y < 85
    (C, 85, E),                                                   # C→E com y ≥ 85 (antes era 80)
    (C, 33, C), (C, 50, C), (C, 32.99, B), (C, 5, B),             # C retido até y < 33; sai para B
    (D, 84.99, D), (D, 85, E),                                    # D→E com y ≥ 85
    (D, 70, D), (D, 33, D), (D, 32.99, B), (D, 5, B),             # sem D→C; sai para B
    (E, 84.99, E), (E, 70, E), (E, 33, E),                        # sem E→D / E→C
    (E, 32.99, B), (E, 5, B),                                     # E→B com y < 33
]


@pytest.mark.parametrize("inicio,y,esperado", TABELA)
def test_transicao(inicio, y, esperado):
    sm = em_estado(inicio)
    sm._transicao(y)
    assert sm.estado_atual == esperado


@pytest.mark.parametrize("inicio", [A, B, C, D, E])
def test_no_maximo_uma_transicao_por_pacote(inicio):
    """Saindo de C/D/E nunca se chega direto em A; de A nunca direto em C/D/E."""
    for y in [i / 2 for i in range(0, 201)]:
        sm = em_estado(inicio)
        sm._transicao(y)
        if inicio in (C, D, E):
            assert sm.estado_atual != A
        if inicio == A:
            assert sm.estado_atual in (A, B)


def test_estados_sem_atributos_removidos():
    sm = EEGStateMachine()
    assert not hasattr(sm, "bloqueado")
    assert not hasattr(sm, "piso")


# ── 2. Filtro: começa na primeira leitura válida ─────────────────────────────
def test_alpha_padrao():
    assert EEGStateMachine().alpha == 0.5


def test_filtro_inicia_na_primeira_leitura():
    sm = EEGStateMachine()
    sm.processar(60)
    assert sm.att_filtrado == 60
    sm.processar(80)
    assert sm.att_filtrado == pytest.approx(0.5 * 80 + 0.5 * 60)
    sm.processar(40)
    assert sm.att_filtrado == pytest.approx(0.5 * 40 + 0.5 * 70)


def test_zero_antes_da_primeira_leitura_e_ignorado():
    sm = EEGStateMachine()
    assert sm.processar(0) == B
    assert not sm.inicializado
    sm.processar(50)
    assert sm.att_filtrado == 50


def test_primeira_leitura_ja_decide_o_estado():
    assert EEGStateMachine().processar(92) == E
    assert EEGStateMachine().processar(70) == C
    assert EEGStateMachine().processar(10) == A


# ── 3. Partida: não passa por A se a primeira leitura for ≥ 20 ───────────────
@pytest.mark.parametrize("primeira", [20, 21, 25, 30, 42, 64, 65, 70, 80, 92, 100])
@pytest.mark.parametrize("alpha", [0.1, 0.2, 0.3, 0.5])
def test_partida_sem_A_sinal_constante(primeira, alpha):
    sm = EEGStateMachine(alpha=alpha)
    estados = [sm.processar(primeira) for _ in range(60)]
    assert A not in estados


@pytest.mark.parametrize("primeira", [20, 30, 50, 70, 90])
def test_partida_sem_A_subindo_depois(primeira):
    sm = EEGStateMachine()
    seq = [primeira] + [min(100, primeira + k) for k in range(1, 40)]
    assert A not in [sm.processar(x) for x in seq]


def test_partida_abaixo_de_20_vai_para_A():
    assert EEGStateMachine().processar(19) == A


# ── 4. Subida contínua 50 → 90: D deve ser alcançado ─────────────────────────
@pytest.mark.parametrize("velocidade", [40, 10, 5, 2, 1, 0.5])   # pontos/s; 40 = degrau
def test_subida_50_90_alcanca_D_e_E(velocidade):
    sm = EEGStateMachine()                     # α do código, 1 pacote/s
    n = math.ceil(40 / velocidade)
    seq = [50] * 30 + [min(90, round(50 + velocidade * k)) for k in range(1, n + 1)] + [90] * 30
    estados = [sm.processar(x) for x in seq]
    assert D in estados
    assert E in estados
    trocas = [estados[0]] + [e for p, e in zip(estados, estados[1:]) if e != p]
    assert trocas == [B, C, D, E]


def test_retencao_na_descida():
    """Descendo de 90 para 40: E retido (y ≥ 33); só cai para B com y < 33."""
    sm = EEGStateMachine(alpha=1.0)
    assert [sm.processar(x) for x in [90, 80, 70, 40, 33, 32, 25, 19]] == [E, E, E, E, E, B, B, A]
