from cushy_serial import CushySerial
from BrainLinkParser import BrainLinkParser
import serial


Porta_Brainlink = 'COM4'
Velocidade_Brainlink = 57600

arduino = serial.Serial('COM8', 9600)

def filtro_passa_baixa(valor_atual, valor_anterior, alpha=0.65):
    return alpha * valor_atual + (1 - alpha) * valor_anterior

att_filtrado = 0
med_filtrado = 0

delta_suave = 0
theta_suave = 0
alpha_suave = 0
beta_suave  = 0
gamma_suave = 0

estado_atual = "B"
bloqueado = False


def onEEG(data):
    global att_filtrado, med_filtrado
    global delta_suave, theta_suave, alpha_suave, beta_suave, gamma_suave
    global estado_atual, bloqueado

    if data.attention == 0 and data.meditation == 0:
        print("⚠️ Sensor desconectado ou sem contato.")
        return

    att_filtrado = filtro_passa_baixa(data.attention, att_filtrado)
    med_filtrado = filtro_passa_baixa(data.meditation, med_filtrado)

    delta = data.delta
    theta = data.theta
    alpha = data.lowAlpha + data.highAlpha
    beta  = data.lowBeta  + data.highBeta
    gamma = data.lowGamma + data.highGamma

    delta_suave = filtro_passa_baixa(delta, delta_suave)
    theta_suave = filtro_passa_baixa(theta, theta_suave)
    alpha_suave = filtro_passa_baixa(alpha, alpha_suave)
    beta_suave  = filtro_passa_baixa(beta,  beta_suave)
    gamma_suave = filtro_passa_baixa(gamma, gamma_suave)

    total = delta_suave + theta_suave + alpha_suave + beta_suave + gamma_suave
    if total > 0:
        delta_pct = delta_suave / total * 100
        theta_pct = theta_suave / total * 100
        alpha_pct = alpha_suave / total * 100
        beta_pct  = beta_suave  / total * 100
        gamma_pct = gamma_suave / total * 100
    else:
        delta_pct = theta_pct = alpha_pct = beta_pct = gamma_pct = 0

    print(f"Atenção: {att_filtrado:.2f} | Meditação: {med_filtrado:.2f}")
    print(f"Ondas EEG (%) -> delta {delta_pct:.2f} | theta {theta_pct:.2f} | alpha {alpha_pct:.2f} | beta {beta_pct:.2f} | gamma {gamma_pct:.2f}")

    att = att_filtrado

    # desbloqueia quando passa pela faixa de reset
    if 30 <= att <= 33:
        bloqueado = False

    if estado_atual == "A":
        if att >= 30:
            estado_atual = "B"

    elif estado_atual == "E":
        # caindo do E: ignora D e C, vai direto para B e bloqueia
        if att < 33:
            estado_atual = "B"
            bloqueado = True

    elif estado_atual == "D":
        # subindo: pode ir para E
        if att >= 85:
            estado_atual = "E"
        # caindo do D: ignora C, vai direto para B e bloqueia
        elif att < 33:
            estado_atual = "B"
            bloqueado = True

    elif estado_atual == "C":
        # subindo normalmente
        if att >= 80:
            estado_atual = "E"
        elif att >= 75:
            estado_atual = "D"
        # caindo abaixo de C: vai para B
        elif att < 33:
            estado_atual = "B"

    else:  # estado B
        if att < 20:
            estado_atual = "A"
        elif not bloqueado and att >= 85:
            estado_atual = "E"
        elif not bloqueado and att >= 75:
            estado_atual = "D"
        elif not bloqueado and att >= 65:
            estado_atual = "C"

    arduino.write(estado_atual.encode())
    print(f"Estado enviado: {estado_atual} | bloqueado: {bloqueado}")


parser = BrainLinkParser(onEEG)
brainlink_serial = CushySerial(Porta_Brainlink, Velocidade_Brainlink)

@brainlink_serial.on_message()
def handle_serial_message(msg: bytes):
    try:
        parser.parse(msg)
    except Exception as e:
        print(f"Erro ao processar pacote: {e}")