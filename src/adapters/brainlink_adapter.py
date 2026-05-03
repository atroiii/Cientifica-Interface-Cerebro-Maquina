
from cushy_serial import CushySerial

class BrainlinkAdapter:
    def __init__(self, port: str = 'COM11'):
        self.port = port
        self.connection = None

    def connect(self) -> bool:
        try:
            self.connection = CushySerial(self.port, 57600)
            # Verifica se a porta realmente abriu
            if not self.connection.isOpen():
                print(f"❌ BrainLink: porta {self.port} não abriu.")
                return False
            return True
        except Exception as e:
            print(f"Erro: {e}. A porta {self.port} não existe ou está ocupada.")
            return False

    def registrar_ouvinte(self, callback_funcao):
        if self.connection:
            @self.connection.on_message()
            def handle_msg(msg: bytes):
                callback_funcao(msg)