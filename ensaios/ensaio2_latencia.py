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

    con = serial.serial_for_url(a.porta, 9600, timeout=a.timeout)
    time.sleep(a.espera_inicial)
    con.reset_input_buffer()

    linhas = []
    for i in range(a.n):
        con.reset_input_buffer()
        t0 = time.perf_counter()
        con.write(b"T")
        con.flush()
        resp = b""
        while time.perf_counter() - t0 < a.timeout:
            resp = con.read(1)            # bloqueia até 1 byte ou o timeout da porta
            if resp == b"T" or not resp:
                break
        t1 = time.perf_counter()
        ok = resp == b"T" and (t1 - t0) <= a.timeout
        linhas.append({"i": i, "t_envio_s": round(t0, 6), "rtt_ms": round((t1 - t0) * 1000, 3) if ok else "",
                       "resposta": resp.decode(errors="replace"), "perdida": int(not ok)})
        time.sleep(a.intervalo)
    con.close()

    with open(arq, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)

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
