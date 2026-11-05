# =============================================================================
# ENSAIO 2 – LATÊNCIA DO ENLACE PC ↔ ARDUINO (via HC-05 ou cabo USB)
#
# Passo a passo do script:
#   1. Abre a porta serial do HC-05 (9600 bps, como o sistema real).
#   2. Espera alguns segundos para o Bluetooth conectar / o Arduino reiniciar.
#   3. Repete N vezes (padrão 200):
#        - marca o tempo t0, envia o caractere 'T';
#        - o firmware responde 'T' de volta, sem mover servo;
#        - marca o tempo t1 quando o 'T' chega. RTT = t1 − t0.
#        - sem resposta dentro do timeout = resposta perdida.
#   4. Grava um CSV com cada envio e mostra as estatísticas no terminal.
#
# Entrada (linha de comando): --porta (obrigatória), --n, --timeout,
#   --intervalo, --espera-inicial, --saida.
# Saída: CSV (i, t_envio_s, rtt_ms, resposta, perdida) e, no terminal,
#   RTT médio, desvio-padrão, mínimo, máximo, mediana e % de perdidas.
#
# O que este ensaio MEDE e o que NÃO mede:
#   - Mede só o ENLACE: PC → HC-05 → Arduino → HC-05 → PC.
#   - NÃO mede a latência total da ICM. Ficam de fora: o headset, o
#     intervalo de ~1 s entre pacotes de atenção, o filtro (que atrasa o
#     gesto de propósito) e o tempo físico de giro dos servos.
#     Por isso o 'T' não move servo: queremos só o tempo de comunicação.
#   - RTT/2 (ida e volta dividido por 2) é só uma APROXIMAÇÃO da latência de
#     ida (PC → Arduino). Ela supõe que ida e volta demoram o mesmo, o que
#     não é garantido no Bluetooth: os buffers e o agendamento de cada
#     sentido podem ser diferentes. Mesmo assim serve para a conclusão:
#     ~11 ms é muito menor que o 1 s entre pacotes do headset.
# =============================================================================
"""
Ensaio 2 - latência de ida e volta PC -> HC-05 -> Arduino -> HC-05 -> PC.

Requer o firmware com o eco de teste (firmware/icm_firmware.ino):
    case 'T': Serial.write('T'); break;   // não move servos

Uso (da raiz do repositório):
    python ensaios/ensaio2_latencia.py --porta COM5
    python ensaios/ensaio2_latencia.py --porta /dev/rfcomm0 --n 200 --timeout 1.0

Para testar o script sem hardware (pyserial ecoa tudo em "loop://"):
    python ensaios/ensaio2_latencia.py --porta loop://

A porta é aberta como em src/adapters/arduino_adapter.py (linha 12):
9600 bps, 8N1. Mede com time.perf_counter() do write() até o byte 'T' chegar.
"""
import argparse
import csv
import datetime as dt
import os
import statistics
import time

import serial

SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resultados")


# Tudo acontece em main: lê os argumentos, mede, salva e resume.
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--porta", required=True, help="porta serial do HC-05 (ex.: COM5, /dev/rfcomm0, loop://)")
    ap.add_argument("--n", type=int, default=200, help="número de envios (padrão 200)")
    ap.add_argument("--timeout", type=float, default=1.0, help="tempo máximo de espera por resposta, s (padrão 1)")
    ap.add_argument("--intervalo", type=float, default=0.1, help="pausa entre envios, s (padrão 0,1)")
    ap.add_argument("--espera-inicial", type=float, default=2.0,
                    help="espera após abrir a porta, s (enlace BT / reset do Arduino; padrão 2)")
    ap.add_argument("--saida", default=None, help="CSV de saída (padrão: ensaios/resultados/ensaio2_<data>.csv)")
    a = ap.parse_args()

    os.makedirs(SAIDA, exist_ok=True)
    arq = a.saida or os.path.join(SAIDA, f"ensaio2_{dt.datetime.now():%Y%m%d_%H%M%S}.csv")

    # serial_for_url aceita porta real (COM5) ou "loop://" (teste sem hardware).
    con = serial.serial_for_url(a.porta, 9600, timeout=a.timeout)
    # Abrir a porta pode reiniciar o Arduino (USB) ou demorar a conectar o
    # Bluetooth. Medir antes disso daria RTTs falsos ou respostas perdidas.
    time.sleep(a.espera_inicial)
    con.reset_input_buffer()

    linhas = []
    for i in range(a.n):
        # Limpa bytes velhos (ex.: um 'T' atrasado da rodada anterior), para
        # não confundir a resposta deste envio com a de um envio antigo.
        # perf_counter é o relógio de maior resolução do Python, próprio
        # para medir intervalos curtos (ms).
        con.reset_input_buffer()
        t0 = time.perf_counter()
        con.write(b"T")
        # flush garante que o byte saiu do buffer do PC antes de esperar.
        con.flush()
        resp = b""
        # Lê byte a byte até chegar o 'T'. Se vier outro byte (lixo), ignora
        # e continua esperando, até o timeout.
        while time.perf_counter() - t0 < a.timeout:
            resp = con.read(1)            # bloqueia até 1 byte ou o timeout da porta
            if resp == b"T" or not resp:
                break
        t1 = time.perf_counter()
        ok = resp == b"T" and (t1 - t0) <= a.timeout
        linhas.append({"i": i, "t_envio_s": round(t0, 6), "rtt_ms": round((t1 - t0) * 1000, 3) if ok else "",
                       "resposta": resp.decode(errors="replace"), "perdida": int(not ok)})
        # Pausa entre envios: evita que um envio atrasado se misture com o
        # próximo.
        time.sleep(a.intervalo)
    con.close()

    with open(arq, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)

    # Estatísticas só com os envios que tiveram resposta.
    rtt = [l["rtt_ms"] for l in linhas if not l["perdida"]]
    perd = sum(l["perdida"] for l in linhas)
    print(f"Porta: {a.porta} | envios: {a.n} | timeout: {a.timeout} s")
    if rtt:
        print(f"RTT médio:  {statistics.mean(rtt):.2f} ms")
        print(f"Desvio-padrão: {statistics.stdev(rtt) if len(rtt) > 1 else 0:.2f} ms")
        print(f"Mínimo: {min(rtt):.2f} ms | Máximo: {max(rtt):.2f} ms | Mediana: {statistics.median(rtt):.2f} ms")
    print(f"Respostas perdidas: {perd}/{a.n} ({100 * perd / a.n:.1f} %)")
    print(f"CSV: {arq}")


if __name__ == "__main__":
    main()
