import serial.tools.list_ports

def listar_portas():
    portas = serial.tools.list_ports.comports()
    return [porta.device for porta in portas]
