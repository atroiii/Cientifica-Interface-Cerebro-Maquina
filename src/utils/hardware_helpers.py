import serial.tools.list_ports


def listar_portas():
    portas = serial.tools.list_ports.comports()
    if not portas:
        return ["(nenhuma porta encontrada)"]

    lista = []
    for porta in portas:
        hwid = porta.hwid.upper()

        # 1. Conexões Bluetooth (BrainLink)
        if "BTHENUM" in hwid:
            nome = "BrainLink (Bluetooth)"

        # 2. Arduinos Oficiais (VID 2341)
        elif "2341" in hwid:
            nome = "Arduino (Oficial)"

        # 3. Arduinos Clones/Genéricos (Chips CH340, CP2102 ou FTDI)
        elif "1A86" in hwid:
            nome = "Arduino (CH340)"
        elif "10C4" in hwid:
            nome = "Arduino / CP2102"
        elif "0403" in hwid:
            nome = "Módulo FTDI"

        # Fallback para outros dispositivos USB
        else:
            nome = porta.description or "Dispositivo Serial"

        lista.append(f"{porta.device} - {nome}")

    return lista