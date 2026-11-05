"""
Ensaio 1 - sinal sintético de atenção a 1 Hz passado pela lógica REAL da ICM.

Lógicas comparadas: real_v2 (código atual do projeto, principal), real_v1
(lógica antiga, cópia em ensaios/legado/), faixas_sem_trava e histerese_3.

Sem hardware e sem participantes. Rode a partir da raiz do repositório:

    python ensaios/ensaio1_sintetico.py

Saídas em ensaios/resultados/:
    ensaio1.csv               uma linha por (cenário, σ, alvo, configuração, repetição)
    ensaio1_resumo.md         tabelas média ± desvio-padrão
    ensaio1_partida.md        partida: v1 (y inicial 0) x v2 (y inicial = 1ª leitura)
    ensaio1_subida_50_90.md   subida contínua 50→90 em várias velocidades
    ensaio1_antecipacoes.md   quantos espúrios são antecipações de uma mudança real
    fig1_serie_temporal.png   bruto, filtrado e limiares (rampa + ruído σ=5)
    fig2_rampa_limpa.png      resposta da lógica real à rampa sem ruído
    fig3_espurios.png         espúrios/min por configuração

Definições (detalhadas em ensaios/RESUMO.md):
- Pacote: um valor inteiro 0-100 por segundo (taxa típica do eSense).
  O sinal = limpo + N(0, σ), arredondado e saturado em [0, 100].
  Pacotes iguais a 0 são descartados, como em EEGSystem._on_eeg (linha 20).
- Comando enviado: o código real envia o caractere a CADA pacote não nulo;
  a mesma política é usada nas lógicas de comparação.
- Troca de gesto: comando diferente do anterior (o Arduino parte da postura
  B: todos os servos em 0, firmware linhas 18-22 = case 'B').
- Faixa real do sinal: faixa nominal (20/65/75/85) do sinal LIMPO, arredondado
  para inteiro como os pacotes.
  Cada entrada do sinal limpo numa faixa G gera um "crédito" válido desde a
  entrada até JANELA_S segundos após o sinal limpo sair de G.
  Uma troca para G que consome um crédito válido é legítima; senão é ESPÚRIA.
- Espúrios em regime: os mesmos, contando só trocas com t >= REGIME_S
  (exclui o transitório de partida; relevante na v1, cujo filtro começa em 0).
- Atraso: para cada entrada do sinal limpo em G, tempo até o primeiro comando
  G emitido dentro da validade do crédito. Entradas sem comando G nesse prazo
  são contadas como "não atendidas" (não entram na média de atraso).
"""
import csv
import os
import sys
import time
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from logica_icm import (ALPHA_DO_CODIGO, GESTOS, LIMIARES_NOMINAIS, LOGICAS,  # noqa: E402
                        MaquinaRealV1, MaquinaRealV2, faixa_nominal,
                        pacote_para_comando, verificar_bloqueado_v1, verificar_v1_v2)

SEMENTE = 20261105
N_REP = 30
DURACAO_S = 600          # 10 min a 1 Hz
FS = 1.0
JANELA_S = 10            # tolerância após a saída da faixa (cobre o atraso do filtro)
REGIME_S = 60            # espúrios "em regime": ignora o transitório de partida (y0 = 0)
SIGMAS = (3, 5, 10)
ALPHAS = (1.0, 0.1, 0.2, 0.3, 0.5)          # 1.0 = sinal bruto (y = x)
if ALPHA_DO_CODIGO not in ALPHAS:
    ALPHAS = ALPHAS + (ALPHA_DO_CODIGO,)
LIMIARES_C = {"20": 20.0, "64/65": 64.5, "74/75": 74.5, "84/85": 84.5}
CENTROS_D = {"A": 10.0, "B": 42.0, "C": 69.5, "D": 79.5, "E": 92.5}
AMPL_C, PERIODO_C = 5.0, 60.0                # oscilação do cenário c

SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resultados")


def rotulo_alpha(a):
    if a == 1.0:
        return "bruto"
    return f"α={a:g}" + (" (código)" if a == ALPHA_DO_CODIGO else "")


# ------------------------------------------------------------------ sinais
def sinal_limpo(cenario, alvo, rng):
    t = np.arange(0, DURACAO_S, 1 / FS)
    if cenario in ("a", "b"):
        meio = DURACAO_S / 2
        return t, 100.0 * (1 - np.abs(t - meio) / meio)          # 0→100→0
    if cenario == "c":
        fase = rng.uniform(0, 2 * np.pi)
        return t, LIMIARES_C[alvo] + AMPL_C * np.sin(2 * np.pi * t / PERIODO_C + fase)
    if cenario == "d":
        return t, np.full_like(t, CENTROS_D[alvo])
    raise ValueError(cenario)


def gerar(cenario, sigma, alvo, rep):
    alvo_id = list(LIMIARES_C).index(alvo) if cenario == "c" else (
        GESTOS.index(alvo) if cenario == "d" else 0)
    rng = np.random.default_rng([SEMENTE, ord(cenario), sigma, alvo_id, rep])
    t, limpo = sinal_limpo(cenario, alvo, rng)
    ruido = rng.normal(0, sigma, size=t.size) if sigma > 0 else 0.0
    pacotes = np.clip(np.rint(limpo + ruido), 0, 100).astype(int)
    return t, limpo, pacotes


# ------------------------------------------------------------------ simulação
def rodar(logica, alpha, pacotes):
    m = LOGICAS[logica](alpha)
    cmds, ys = [], []
    for x in pacotes:
        c = pacote_para_comando(m, int(x))
        cmds.append(c)
        ys.append(m.y)
    return cmds, ys


def entradas_limpas(limpo):
    """[(faixa, t_entrada, t_saida)] do sinal limpo, quantizado como os pacotes
    (inteiro 0-100), para que o arredondamento não seja contado como espúrio."""
    faixas = [faixa_nominal(v) for v in np.clip(np.rint(limpo), 0, 100)]
    ent, ini = [], 0
    for i in range(1, len(faixas) + 1):
        if i == len(faixas) or faixas[i] != faixas[ini]:
            ent.append((faixas[ini], ini, i))
            ini = i
    return ent


def metricas(t, limpo, cmds):
    dur_min = DURACAO_S / 60
    enviados = [(int(ti), c) for ti, c in zip(t, cmds) if c is not None]
    trocas, ant = [], "B"
    for ti, c in enviados:
        if c != ant:
            trocas.append((ti, c))
            ant = c
    ent = entradas_limpas(limpo)
    creditos = [[g, t0, t1 + JANELA_S, False] for g, t0, t1 in ent]
    esp = esp_reg = 0
    for ti, g in trocas:
        for cr in creditos:
            if not cr[3] and cr[0] == g and cr[1] <= ti <= cr[2]:
                cr[3] = True
                break
        else:
            esp += 1
            esp_reg += ti >= REGIME_S
    atrasos, atr_g, nao_at = [], defaultdict(list), 0
    for g, t0, t1 in ent:
        lim = t1 + JANELA_S
        d = next((ti - t0 for ti, c in enviados if t0 <= ti <= lim and c == g), None)
        if d is None:
            nao_at += 1
        else:
            atrasos.append(d)
            atr_g[g].append(d)
    alcancados = {c for _, c in enviados}
    r = {
        "cmd_min": len(enviados) / dur_min,
        "trocas_min": len(trocas) / dur_min,
        "espurios_min": esp / dur_min,
        "espurios_regime_min": esp_reg / ((DURACAO_S - REGIME_S) / 60),
        "atraso_s": float(np.mean(atrasos)) if atrasos else float("nan"),
        "entradas": len(ent),
        "entradas_nao_atendidas": nao_at,
        "gestos_emitidos": "".join(g for g in GESTOS if g in alcancados),
    }
    for g in GESTOS:
        r[f"alcancou_{g}"] = int(g in alcancados)
        r[f"atraso_{g}_s"] = float(np.mean(atr_g[g])) if atr_g[g] else float("nan")
    return r


def casos():
    yield "a", 0, "-"
    for s in SIGMAS:
        yield "b", s, "-"
    for s in SIGMAS:
        for alvo in LIMIARES_C:
            yield "c", s, alvo
    for s in SIGMAS:
        for alvo in CENTROS_D:
            yield "d", s, alvo


CONFIGS = [(lg, a) for lg in LOGICAS for a in ALPHAS]


# ------------------------------------------------------------------ relatórios
def ms(v):
    v = np.asarray(v, float)
    v = v[~np.isnan(v)]
    if v.size == 0:
        return "—"
    return f"{v.mean():.2f} ± {v.std(ddof=1) if v.size > 1 else 0:.2f}"


def tabela(linhas, cenario, sigma, alvo=None, com_alcance=False):
    sel = [r for r in linhas if r["cenario"] == cenario and r["sigma"] == sigma
           and (alvo is None or r["alvo"] == alvo)]
    cab = ["Lógica", "Filtro", "Comandos/min", "Trocas/min", "Espúrios/min",
           f"Espúrios/min (t ≥ {REGIME_S} s)", "Atraso médio (s)", "Entradas não atendidas (%)"]
    if com_alcance:
        cab.append("Gestos alcançados (% das rep.)")
    out = ["| " + " | ".join(cab) + " |", "|" + "---|" * len(cab)]
    for lg, a in CONFIGS:
        rr = [r for r in sel if r["logica"] == lg and r["alpha"] == a]
        na = 100 * sum(r["entradas_nao_atendidas"] for r in rr) / max(1, sum(r["entradas"] for r in rr))
        cel = [lg, rotulo_alpha(a), ms([r["cmd_min"] for r in rr]),
               ms([r["trocas_min"] for r in rr]), ms([r["espurios_min"] for r in rr]),
               ms([r["espurios_regime_min"] for r in rr]),
               ms([r["atraso_s"] for r in rr]), f"{na:.0f}"]
        if com_alcance:
            cel.append(" ".join(f"{g}:{100 * np.mean([r[f'alcancou_{g}'] for r in rr]):.0f}"
                                for g in GESTOS))
        out.append("| " + " | ".join(cel) + " |")
    return "\n".join(out)


def tabela_atraso_por_gesto(linhas, cenario, sigma):
    sel = [r for r in linhas if r["cenario"] == cenario and r["sigma"] == sigma]
    out = ["| Lógica | Filtro | " + " | ".join(f"Atraso {g} (s)" for g in GESTOS) + " |",
           "|" + "---|" * (2 + len(GESTOS))]
    for lg, a in CONFIGS:
        rr = [r for r in sel if r["logica"] == lg and r["alpha"] == a]
        out.append(f"| {lg} | {rotulo_alpha(a)} | " +
                   " | ".join(ms([r[f"atraso_{g}_s"] for r in rr]) for g in GESTOS) + " |")
    return "\n".join(out)


PARTIDA_VALORES = (19, 20, 25, 42, 70, 92)


def partida():
    """Primeiros 15 comandos com sinal constante sem ruído: v2 x v1."""
    out = ["| Lógica | Filtro | Sinal constante | Primeiros 15 comandos (1 por s) | s em A (de 60) |",
           "|---|---|---|---|---|"]
    for cls in (MaquinaRealV2, MaquinaRealV1):
        for v in PARTIDA_VALORES:
            for a in ALPHAS:
                m = cls(a)
                seq = [pacote_para_comando(m, v) for _ in range(60)]
                out.append(f"| {cls.nome} | {rotulo_alpha(a)} | {v} | `{''.join(seq[:15])}` | {seq.count('A')} |")
    return "\n".join(out)


def partida_com_ruido():
    """Cenário d (patamares B–E): % das repetições com algum 'A' nos primeiros 60 s."""
    out = ["| Lógica | Filtro | σ | " + " | ".join(f"Patamar {g}" for g in "BCDE") + " |",
           "|---|---|---|---|---|---|---|"]
    for cls in (MaquinaRealV2, MaquinaRealV1):
        for a in ALPHAS:
            for s in SIGMAS:
                cel = []
                for g in "BCDE":
                    n = 0
                    for rep in range(N_REP):
                        _, _, pac = gerar("d", s, g, rep)
                        m = cls(a)
                        n += "A" in [pacote_para_comando(m, int(x)) for x in pac[:60]]
                    cel.append(f"{100 * n / N_REP:.0f} %")
                out.append(f"| {cls.nome} | {rotulo_alpha(a)} | {s} | " + " | ".join(cel) + " |")
    return "\n".join(out)


VELOCIDADES = (40, 10, 5, 2, 1, 0.5)            # pontos de atenção por segundo (40 = degrau)


def seqs_subida():
    for vel in VELOCIDADES:
        n = int(np.ceil(40 / vel))
        yield vel, [50] * 30 + [min(90, round(50 + vel * k)) for k in range(1, n + 1)] + [90] * 30


def subida_50_90():
    """Pergunta 4 da Parte 0: subida contínua 50→90 (sem ruído) em várias velocidades."""
    out = ["| Lógica | Filtro | Velocidade da subida | Sequência de gestos emitidos (trocas) | D alcançado? | E alcançado? |",
           "|---|---|---|---|---|---|"]
    for vel, seq in seqs_subida():
        for cls, a in [(MaquinaRealV2, a) for a in ALPHAS] + [(MaquinaRealV1, ALPHA_DO_CODIGO)]:
            m = cls(a)
            cmds = [pacote_para_comando(m, x) for x in seq][29:]   # após 30 s em 50
            trocas = [cmds[0]] + [c for p, c in zip(cmds, cmds[1:]) if c != p]
            rot = "degrau" if vel >= 40 else f"{vel:g} pt/s"
            out.append(f"| {cls.nome} | {rotulo_alpha(a)} | {rot} | {'→'.join(trocas)} | "
                       f"{'sim' if 'D' in cmds else 'não'} | {'sim' if 'E' in cmds else 'não'} |")
    return "\n".join(out)


def _espurias(t, limpo, cmds):
    """Lista (t, gesto) das trocas classificadas como espúrias (mesma regra de metricas)."""
    trocas, ant = [], "B"
    for ti, c in zip(t, cmds):
        if c is not None and c != ant:
            trocas.append((int(ti), c))
            ant = c
    ent = entradas_limpas(limpo)
    creditos = [[g, t0, t1 + JANELA_S, False] for g, t0, t1 in ent]
    esp = []
    for ti, g in trocas:
        for cr in creditos:
            if not cr[3] and cr[0] == g and cr[1] <= ti <= cr[2]:
                cr[3] = True
                break
        else:
            esp.append((ti, g))
    return esp, ent


def antecipacoes():
    out = ["| Lógica | Filtro | σ | Espúrios (30 rep.) | Antecipações (≤ 15 s) | Mediana da antecipação (s) |",
           "|---|---|---|---|---|---|"]
    for lg in ("real_v2", "real_v1", "faixas_sem_trava", "histerese_3"):
        for s in SIGMAS:
            tot, ants = 0, []
            for rep in range(N_REP):
                t, limpo, pac = gerar("b", s, "-", rep)
                cmds, _ = rodar(lg, ALPHA_DO_CODIGO, pac)
                esp, ent = _espurias(t, limpo, cmds)
                tot += len(esp)
                for ti, g in esp:
                    prox = [t0 - ti for g2, t0, _ in ent if g2 == g and t0 > ti]
                    if prox and prox[0] <= 15:
                        ants.append(prox[0])
            med = f"{np.median(ants):.0f}" if ants else "—"
            out.append(f"| {lg} | {rotulo_alpha(ALPHA_DO_CODIGO)} | {s} | {tot} | {len(ants)} | {med} |")
    return "\n".join(out)


# ------------------------------------------------------------------ figuras
COR = {"real_v2": "#2a78d6", "real_v1": "#eb6834", "faixas_sem_trava": "#1baf7a", "histerese_3": "#eda100"}
TXT2 = "#52514e"


def _estilo(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#b5b4ad")
    ax.tick_params(colors=TXT2, labelsize=9)
    ax.grid(axis="y", color="#e6e5e0", lw=0.8)
    ax.set_axisbelow(True)


def _limiares(ax, real=True):
    for l in LIMIARES_NOMINAIS:
        ax.axhline(l, color="#8a8983", lw=0.9, ls="-", zorder=1)
        ax.text(DURACAO_S + 4, l, f"{l}", va="center", fontsize=8, color=TXT2)
    if real:
        for l in (30, 33):
            ax.axhline(l, color="#8a8983", lw=0.9, ls=":", zorder=1)
            ax.text(DURACAO_S + 4, l, f"{l}*", va="center", fontsize=8, color=TXT2)


def fig_serie(t, limpo, pacotes, ys, cmds, caminho, titulo):
    import matplotlib.pyplot as plt
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(10, 6.4), sharex=True,
                                  gridspec_kw={"height_ratios": [3, 1.3]})
    ax.plot(t, pacotes, color="#b5b4ad", lw=0.9, label="Atenção bruta (pacotes)")
    ax.plot(t, limpo, color="#0b0b0b", lw=1.2, ls="--", label="Sinal sem ruído")
    ax.plot(t, ys, color=COR["real_v2"], lw=2, label=f"Filtrada (EMA α={ALPHA_DO_CODIGO:g}, código v2)")
    _limiares(ax)
    ax.set_ylim(0, 100)
    ax.set_xlim(0, DURACAO_S)
    ax.set_ylabel("Atenção (0–100)")
    ax.set_title(titulo, loc="left", fontsize=11)
    ax.legend(loc="lower center", fontsize=8, frameon=False)
    _estilo(ax)
    idx = {g: i for i, g in enumerate(GESTOS)}
    tc = [ti for ti, c in zip(t, cmds) if c]
    ax2.step(tc, [idx[c] for c in cmds if c], where="post", color=COR["real_v2"], lw=2,
             label="Comando enviado (real_v2)")
    ax2.step(t, [idx[faixa_nominal(v)] for v in np.clip(np.rint(limpo), 0, 100)], where="post", color="#0b0b0b",
             lw=1.2, ls="--", label="Faixa nominal do sinal sem ruído")
    ax2.set_yticks(range(5), list(GESTOS))
    ax2.set_ylabel("Gesto")
    ax2.set_xlabel("Tempo (s)")
    ax2.legend(loc="lower right", bbox_to_anchor=(1, 1.0), fontsize=8, frameon=False, ncol=2)
    _estilo(ax2)
    fig.text(0.01, 0.005, "Linhas cheias: limiares nominais 20/65/75/85.  "
             "* pontilhadas: limiares extras da máquina real v2 (A→B em 30; C/D/E→B em 33).",
             fontsize=8, color=TXT2)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(caminho, dpi=150)
    plt.close(fig)


def fig_espurios(linhas, caminho):
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 3, figsize=(12, 6.4), sharey=True, sharex=True)
    nomes = [f"{lg} | {rotulo_alpha(a)}" for lg, a in CONFIGS]
    ypos = np.arange(len(CONFIGS))[::-1]
    for ax, s in zip(axs, SIGMAS):
        sel = [r for r in linhas if r["cenario"] == "b" and r["sigma"] == s]
        for y, (lg, a) in zip(ypos, CONFIGS):
            v = np.array([r["espurios_min"] for r in sel if r["logica"] == lg and r["alpha"] == a])
            ax.barh(y, v.mean(), xerr=v.std(ddof=1), height=0.7, color=COR[lg],
                    error_kw={"ecolor": "#52514e", "lw": 1, "capsize": 2})
        ax.set_title(f"Rampa + ruído σ = {s}", loc="left", fontsize=10)
        _estilo(ax)
        ax.grid(axis="x", color="#e6e5e0", lw=0.8)
        ax.grid(axis="y", visible=False)
    axs[0].set_yticks(ypos, nomes, fontsize=8)
    from matplotlib.patches import Patch
    fig.supxlabel(f"Acionamentos espúrios por minuto (média ± DP, n={N_REP})", fontsize=10, y=0.055)
    fig.legend(handles=[Patch(color=c, label=n) for n, c in COR.items()],
               loc="lower center", ncol=4, frameon=False, fontsize=9)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(caminho, dpi=150)
    plt.close(fig)


# ------------------------------------------------------------------ main
def main():
    os.makedirs(SAIDA, exist_ok=True)
    t0 = time.time()
    linhas = []
    for cen, s, alvo in casos():
        for rep in range(N_REP):
            t, limpo, pacotes = gerar(cen, s, alvo, rep)
            for lg, a in CONFIGS:
                cmds, _ = rodar(lg, a, pacotes)
                r = {"cenario": cen, "sigma": s, "alvo": alvo, "logica": lg,
                     "alpha": a, "filtro": rotulo_alpha(a), "rep": rep}
                r.update(metricas(t, limpo, cmds))
                linhas.append(r)
    print(f"{len(linhas)} execuções simuladas em {time.time() - t0:.1f} s")

    with open(os.path.join(SAIDA, "ensaio1.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)

    # verificações: `bloqueado` não tinha efeito na v1; v2 só difere da v1 no que foi pretendido
    seqs = [gerar(c, s, al, 0)[2] for c, s, al in casos()] + [q for _, q in seqs_subida()]
    n_eq, dif = verificar_bloqueado_v1(seqs, ALPHAS)
    print(f"v1 x v1 sem `bloqueado`: {dif} diferenças em {n_eq} pacotes")
    n12, expl, inexpl = verificar_v1_v2(seqs, ALPHAS)
    print(f"v1 (com início do filtro da v2) x v2: {expl} divergências C→E/C→D (80 ≤ y < 85), "
          f"{inexpl} inexplicadas, em {n12} pacotes")

    md = [f"# Ensaio 1 – resultados (semente {SEMENTE}, {N_REP} repetições × {DURACAO_S} s a 1 Hz)",
          "",
          f"Verificação 1: a lógica v1 e a cópia da v1 sem a variável `bloqueado` deram **{dif} diferenças "
          f"em {n_eq} pacotes** (comando e valor filtrado).",
          "",
          f"Verificação 2: rodando a v1 com o mesmo início de filtro da v2, as duas divergiram em **{expl} "
          f"pacotes, todos no caso pretendido** (estado C com 80 ≤ y < 85: v1 → E, v2 → D) e em "
          f"**{inexpl} pacotes por outro motivo**, em {n12} pacotes (sequências da repetição 0 de todos os cenários e as subidas 50→90, todos os α).",
          "",
          "Comandos/min = caracteres enviados ao Arduino (o código envia a cada pacote não nulo). "
          "Trocas/min = mudanças de gesto. Atraso = do sinal sem ruído entrar na faixa até o "
          f"primeiro comando daquele gesto (janela até {JANELA_S} s após o sinal sair da faixa). ",
          "", "## (a) Rampa 0→100→0 sem ruído", "",
          tabela(linhas, "a", 0, com_alcance=True), "",
          "### Atraso por gesto – rampa sem ruído", "", tabela_atraso_por_gesto(linhas, "a", 0), ""]
    for s in SIGMAS:
        md += [f"## (b) Rampa + ruído σ = {s}", "", tabela(linhas, "b", s, com_alcance=True), ""]
    for s in SIGMAS:
        md += [f"## (c) Oscilação em torno dos limiares (±{AMPL_C:g}, período {PERIODO_C:g} s), σ = {s}", ""]
        for alvo in LIMIARES_C:
            md += [f"### Limiar {alvo}", "", tabela(linhas, "c", s, alvo), ""]
    for s in SIGMAS:
        md += [f"## (d) Patamar fixo no centro de cada faixa, σ = {s}", ""]
        for alvo in CENTROS_D:
            md += [f"### Faixa {alvo} (sinal = {CENTROS_D[alvo]:g})", "",
                   tabela(linhas, "d", s, alvo, com_alcance=True), ""]
    with open(os.path.join(SAIDA, "ensaio1_resumo.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    with open(os.path.join(SAIDA, "ensaio1_partida.md"), "w", encoding="utf-8") as f:
        f.write("# Partida: real_v2 (y inicial = 1ª leitura) x real_v1 (y inicial = 0)\n\n"
                "## Sinal constante sem ruído\n\n" + partida() + "\n\n"
                "## Cenário d com ruído: % das 30 repetições com algum comando A nos primeiros 60 s\n\n"
                + partida_com_ruido() + "\n")
    with open(os.path.join(SAIDA, "ensaio1_antecipacoes.md"), "w", encoding="utf-8") as f:
        f.write("# Espúrios que são antecipações (cenário b, rampa + ruído)\n\n"
                "Antecipação = troca para G que ocorre no máximo 15 s antes de o sinal sem ruído entrar em G.\n\n"
                + antecipacoes() + "\n")
    with open(os.path.join(SAIDA, "ensaio1_subida_50_90.md"), "w", encoding="utf-8") as f:
        f.write("# Subida contínua 50→90 sem ruído (lógica real; 30 s em 50 para acomodar o filtro, depois a subida e 30 s em 90; trocas contadas a partir do fim do patamar em 50)\n\n"
                + subida_50_90() + "\n")

    try:
        import matplotlib
        matplotlib.use("Agg")
    except ImportError:
        print("matplotlib não instalado: figuras não geradas")
        return
    t, limpo, pac = gerar("b", 5, "-", 0)
    cmds, ys = rodar("real_v2", ALPHA_DO_CODIGO, pac)
    fig_serie(t, limpo, pac, ys, cmds, os.path.join(SAIDA, "fig1_serie_temporal.png"),
              "Rampa 0→100→0 + ruído gaussiano σ=5 (repetição 0) – lógica real_v2")
    t, limpo, pac = gerar("a", 0, "-", 0)
    cmds, ys = rodar("real_v2", ALPHA_DO_CODIGO, pac)
    fig_serie(t, limpo, pac, ys, cmds, os.path.join(SAIDA, "fig2_rampa_limpa.png"),
              "Rampa 0→100→0 sem ruído – lógica real_v2")
    fig_espurios(linhas, os.path.join(SAIDA, "fig3_espurios.png"))
    print("Saídas em", SAIDA)


if __name__ == "__main__":
    main()
