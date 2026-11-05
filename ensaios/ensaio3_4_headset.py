# =============================================================================
# ENSAIOS 3 E 4 – QUALIDADE DE SINAL E TAXA DE ATUALIZAÇÃO DO HEADSET
#
# Passo a passo do script:
#   1. Conecta ao BrainLink pela porta serial, com o mesmo adaptador e o
#      mesmo parser do sistema real.
#   2. A cada pacote EEG decodificado, chama on_eeg, que:
#        - anota o horário de chegada;
#        - passa a atenção pela lógica real v2 (com o portão de atenção 0);
#        - grava uma linha no CSV e mostra no terminal.
#      NADA é enviado ao Arduino. Só registramos o que o sistema FARIA.
#   3. Grava pelo tempo do modo: 2 min (fora_da_cabeca) ou 5 min (em_uso).
#   4. No fim, imprime um resumo.
#
# Entrada: --porta (do BrainLink), --modo (fora_da_cabeca ou em_uso),
#   --duracao (opcional).
# Saída: CSV com uma linha por pacote e, no terminal: intervalo médio entre
#   pacotes (taxa em Hz), % de pacotes com atenção 0, valores do campo de
#   qualidade (signal) e quantas vezes o gesto A teria sido disparado.
#
# Os dois modos respondem perguntas diferentes:
#   - fora_da_cabeca: o portão "atenção = 0" segura o sistema quando não há
#     contato? (esperado: nenhum comando).
#   - em_uso: qual a taxa real de pacotes (confirma o 1 Hz do ensaio 1) e
#     como a lógica se comporta com uma pessoa usando o headset.
# =============================================================================
"""
Ensaios 3 e 4 - qualidade de sinal e taxa de atualização do BrainLink.

NÃO envia nada ao Arduino: apenas registra o que o sistema FARIA.

Uso (da raiz do repositório, com o SDK em deps/ como no README):
    python ensaios/ensaio3_4_headset.py --porta COM7 --modo fora_da_cabeca   # 2 min
    python ensaios/ensaio3_4_headset.py --porta COM7 --modo em_uso           # 5 min
    (--duracao S sobrescreve a duração do modo)

Mesmo caminho de dados do sistema real:
- conexão: BrainlinkAdapter (src/adapters/brainlink_adapter.py), CushySerial a 57600 bps;
- decodificação: BrainLinkParser(callback) e parser.parse(msg), como em
  EEGSystem._registrar_parser (src/services/eeg_state_sytem.py, linhas 43-52);
- decisão: EEGStateMachine importada sem alteração; o portão "attention == 0 ->
  ignora" de EEGSystem._on_eeg (linhas 20-21) é reproduzido em
  ensaios/logica_icm.py::pacote_para_comando.

Campo de qualidade: o README do SDK (github.com/Macrotellect/BrainLinkParser-Python)
lista o atributo `signal` em BrainLinkData, sem documentar faixa ou significado.
O script grava o valor bruto desse atributo (ou de `poorSignal`, se existir).

CSV: ensaios/resultados/ensaio3_4_<modo>_<data>.csv, uma linha por pacote EEG:
    t_unix, t_rel_s, attention, meditation, signal, att_filtrada, comando
(`comando` vazio = pacote com attention 0, que o sistema real descarta).
"""
import argparse
import csv
import datetime as dt
import os
import statistics
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from logica_icm import RAIZ, MaquinaRealV2, pacote_para_comando  # noqa: E402  (também põe a raiz no sys.path)

from deps.BrainLinkParser import BrainLinkParser                  # noqa: E402  mesmo import de eeg_state_sytem.py
from src.adapters.brainlink_adapter import BrainlinkAdapter       # noqa: E402

# Duração padrão de cada modo, em segundos.
MODOS = {"fora_da_cabeca": 120, "em_uso": 300}
SAIDA = os.path.join(RAIZ, "ensaios", "resultados")
CAMPOS = ["t_unix", "t_rel_s", "attention", "meditation", "signal", "att_filtrada", "comando"]


# Lê o campo de qualidade de contato do pacote, tentando os nomes possíveis
# (o nome varia conforme a versão do SDK). Grava o valor bruto, sem
# interpretar.
# Leitura do valor: no protocolo ThinkGear da NeuroSky (o mesmo do
# BrainLink), signal = 0 é contato bom e signal = 200 é "sem contato com a
# pele". Fora da cabeça medimos 200 em todos os pacotes. O sistema real NÃO
# lê esse campo; só o registramos para confirmar o portão de atenção 0.
def campo_qualidade(data):
    for nome in ("signal", "poorSignal", "poor_signal"):
        if hasattr(data, nome):
            return getattr(data, nome)
    return ""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--porta", required=True, help="porta serial do BrainLink (ex.: COM7)")
    ap.add_argument("--modo", required=True, choices=list(MODOS))
    ap.add_argument("--duracao", type=float, default=None, help="duração em s (padrão: 120 ou 300 conforme o modo)")
    a = ap.parse_args()
    dur = a.duracao if a.duracao is not None else MODOS[a.modo]

    os.makedirs(SAIDA, exist_ok=True)
    arq = os.path.join(SAIDA, f"ensaio3_4_{a.modo}_{dt.datetime.now():%Y%m%d_%H%M%S}.csv")
    f = open(arq, "w", newline="", encoding="utf-8")
    w = csv.DictWriter(f, fieldnames=CAMPOS)
    w.writeheader()

    maquina = MaquinaRealV2()        # lógica v2: alpha do código (0,50), y inicial = 1ª leitura válida
    # A leitura chega numa thread do adaptador serial, enquanto a thread
    # principal só espera. O lock evita ler a lista ao mesmo tempo em que
    # ela é escrita.
    lock = threading.Lock()
    linhas = []
    t_ini = [None]

    # Chamado pelo parser a cada pacote EEG (cerca de 1 por segundo).
    # Mesmo papel de EEGSystem._on_eeg no sistema real, mas sem enviar ao
    # Arduino.
    def on_eeg(data):
        agora = time.time()
        with lock:
            if t_ini[0] is None:
                t_ini[0] = agora
            # Atenção = 0 é descartada: o headset manda 0 quando não há leitura
            # válida (sem contato). Usar esse 0 faria o filtro despencar e a
            # mão iria para A (distração) sem a pessoa estar distraída.
            # cmd = None nesse caso, e a coluna "comando" fica vazia.
            cmd = pacote_para_comando(maquina, data.attention)
            r = {"t_unix": f"{agora:.6f}", "t_rel_s": f"{agora - t_ini[0]:.6f}",
                 "attention": data.attention, "meditation": getattr(data, "meditation", ""),
                 "signal": campo_qualidade(data),
                 "att_filtrada": f"{maquina.y:.3f}", "comando": cmd or ""}
            linhas.append(r)
            w.writerow(r)
            # Grava em disco a cada pacote: se o programa cair, nada se perde.
            f.flush()
            print(f"att={r['attention']:>3} signal={r['signal']!s:>4} filt={r['att_filtrada']:>7} cmd={r['comando'] or '-'}")

    # igual a EEGSystem._conectar_hardware (passo 1) + _registrar_parser
    brainlink = BrainlinkAdapter(a.porta)
    if not brainlink.conectar():
        print("Falha ao conectar no BrainLink.")
        os._exit(1)
    parser = BrainLinkParser(on_eeg)

    # Bytes crus da serial → parser do SDK → on_eeg. Um pacote corrompido
    # gera erro só daquele pacote, sem derrubar a gravação.
    def processar_bytes_brutos(msg: bytes):
        try:
            parser.parse(msg)
        except Exception as e:
            print(f"Erro ao decodificar pacote: {e}")

    brainlink.registrar_ouvinte(processar_bytes_brutos)
    print(f"Modo {a.modo}: gravando por {dur:.0f} s em {arq} (Ctrl+C encerra antes)")
    try:
        time.sleep(dur)
    except KeyboardInterrupt:
        print("Interrompido pelo usuário.")

    with lock:
        dados = list(linhas)
    f.close()
    resumo(dados, a.modo, dur, arq)
    try:
        brainlink.desconectar()
    finally:
        os._exit(0)      # como main.py: evita processo preso na thread serial


# Calcula e imprime os números do ensaio a partir das linhas gravadas.
def resumo(dados, modo, dur, arq):
    print("\n==== RESUMO ====")
    print(f"Modo: {modo} | duração pedida: {dur:.0f} s | pacotes EEG recebidos: {len(dados)}")
    if len(dados) < 2:
        print("Pacotes insuficientes para calcular a taxa de atualização.")
        print(f"CSV: {arq}")
        return
    # Taxa de atualização: diferença de tempo entre pacotes consecutivos.
    # 1 / intervalo médio = taxa em Hz.
    t = [float(r["t_rel_s"]) for r in dados]
    dts = [b - a for a, b in zip(t, t[1:])]
    print(f"Intervalo médio entre pacotes de atenção: {statistics.mean(dts):.3f} s "
          f"(DP {statistics.stdev(dts) if len(dts) > 1 else 0:.3f} s; min {min(dts):.3f}; max {max(dts):.3f}) "
          f"-> {1 / statistics.mean(dts):.3f} Hz")
    validos = [float(r["t_rel_s"]) for r in dados if r["comando"]]
    if len(validos) > 1:
        dv = [b - a for a, b in zip(validos, validos[1:])]
        print(f"Intervalo médio entre pacotes com atenção != 0 (os que geram comando): {statistics.mean(dv):.3f} s")
    zeros = sum(1 for r in dados if not r["comando"])
    print(f"Pacotes com atenção 0 (descartados pelo sistema): {zeros} ({100 * zeros / len(dados):.1f} %)")
    sinais = [r["signal"] for r in dados if r["signal"] != ""]
    if sinais:
        cont = {}
        for s in sinais:
            cont[s] = cont.get(s, 0) + 1
        top = sorted(cont.items(), key=lambda kv: -kv[1])[:8]
        print("Campo de qualidade (valor: nº de pacotes):", ", ".join(f"{k}: {v}" for k, v in top))
    # Gesto A: diferencia "disparos" (entradas em A, quando a mão de fato
    # se move) de "pacotes com A" (repetições do mesmo gesto, sem movimento).
    cmds = [r["comando"] for r in dados if r["comando"]]
    envios_a = cmds.count("A")
    entradas_a, ant = 0, "B"
    for c in cmds:
        if c == "A" and ant != "A":
            entradas_a += 1
        ant = c
    print(f"Comandos que seriam enviados: {len(cmds)}")
    print(f"Gesto A: {entradas_a} disparo(s) (entradas em A); {envios_a} pacote(s) com comando 'A'")
    print(f"CSV: {arq}")


if __name__ == "__main__":
    main()
