import serial

class ArduinoAdapter:
    def __init__(self, port: str ):
        self.port = port
        self.connection = None

    def connect(self) -> bool:
        try:
            self.connection = serial.Serial(self.port, 9600, timeout=1)
            return True
        except Exception as e:
            print(f"Erro ao conectar no Arduino na porta {self.port}: {e}")
            return False

    def enviar_estado(self, estado: str):
        if self.connection and self.connection.is_open:
            self.connection.write(estado.encode())
        else:
            print("⚠️ Arduino não está conectado para enviar dados.")

    def desconectar(self):
        if self.connection and self.connection.is_open:
            self.connection.close()