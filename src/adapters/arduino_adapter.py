import serial

class ArduinoAdapter:
    def __init__(self, porta: str):
        self.porta = porta
        self.conexao = None

    def conectar(self) -> bool:
        try:
            # Abre a porta de comunicação com o Arduino na velocidade de 9600 bauds (a velocidade padrão do Arduino)
            # E espera no máximo 2 segundos (timeout=2) por uma resposta.
            self.conexao = serial.Serial(self.porta, 9600, timeout=2)
            return True
        except Exception as e:
            print(f"Erro ao conectar no Arduino na porta {self.porta}: {e}")
            return False

    def enviar_estado(self, estado: str):
        # Verifica se a conexão existe e se a porta está aberta
        if self.conexao and self.conexao.is_open:
            # write: envia dados para o dispositivo
            # encode: transforma texto em bytes
            self.conexao.write(estado.encode())
        else:
            print("⚠️ Arduino não está conectado para enviar dados.")

    def desconectar(self):
        if self.conexao and self.conexao.is_open:
            self.conexao.close()