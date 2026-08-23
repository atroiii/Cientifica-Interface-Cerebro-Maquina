from cushy_serial import CushySerial

class BrainlinkAdapter:
    def __init__(self, porta: str ):
        self.porta = porta
        self.conexao = None

    def conectar(self) -> bool:
        try:
            #Tenta abrir a conexão com o Brainlink
            self.conexao = CushySerial(self.porta, 57600)
            # Verifica se a porta realmente abriu
            if not self.conexao.isOpen():
                print(f"❌ BrainLink: porta {self.porta} não abriu.")
                return False
            return True
        except Exception as e:
            print(f"Erro: {e}. A porta {self.porta} não existe ou está ocupada.")
            return False

    def registrar_ouvinte(self, callback_funcao):
        #existe conexão?
        if self.conexao:
            @self.conexao.on_message()
            #o decorador vai chamar automaticamente toda vez que um pacote de dados chegar
            def handle_msg(msg: bytes):
                #Aqui mandamos a msg para outra parte do código essa Class tem somente a responsabilidade
                #De fazer a conexão e manda para outra parte do código realizar a lógica
                callback_funcao(msg)