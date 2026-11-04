import time
import threading
from deps.BrainLinkParser import BrainLinkParser
from src.adapters.arduino_adapter import ArduinoAdapter
from src.adapters.brainlink_adapter import BrainlinkAdapter
from src.services.eeg_state_machine import EEGStateMachine
from src.ui.app import EEGApp
from src.models.eeg_buffer import EEGBuffer


class EEGSystem:
    def __init__(self):
        self.arduino   = None
        self.brainlink = None
        self.maquina   = EEGStateMachine()
        self.buffer    = EEGBuffer()
        self.app       = None

    def _on_eeg(self, data):
        if data.attention == 0:
            return

        novo_estado = self.maquina.processar(data.attention)

        # Envia para o Arduino APENAS se ele estiver conectado
        if self.arduino:
            try:
                self.arduino.enviar_estado(novo_estado.value)
            except Exception as e:
                print(f"Aviso ao enviar para o Arduino: {e}")

        att_filtrado = self.maquina.att_filtrado
        estado       = novo_estado.value
        bloqueado    = self.maquina.bloqueado

        print(f"Att Filtrada: {att_filtrado:.1f} | Estado: {estado} | Bloqueado: {bloqueado}")

        # ── alimenta o buffer ─────────────────────────────────────────────
        self.buffer.update_from_state(
            att_filtrada = att_filtrado,
            state        = estado,
            blocked      = bloqueado
        )

    def _registrar_parser(self):
        parser = BrainLinkParser(self._on_eeg)

        def processar_bytes_brutos(msg: bytes):
            try:
                parser.parse(msg)
            except Exception as e:
                print(f"Erro ao decodificar pacote: {e}")

        self.brainlink.registrar_ouvinte(processar_bytes_brutos)

    def _conectar_hardware(self, arduino_port, brainlink_port, progress=None) -> tuple[bool, str]:
        """Conecta ao BrainLink e Arduino.
        Retorna (sucesso, mensagem_de_erro).
        `progress(etapa)` avisa a tela de carregamento ("brainlink", "arduino").
        """
        progress = progress or (lambda etapa: None)

        # 1. Conexão do BrainLink (Obrigatória)
        progress("brainlink")
        try:
            self.brainlink = BrainlinkAdapter(brainlink_port)
            if not self.brainlink.conectar():
                return False, "Falha ao conectar no BrainLink. Verifique a porta e tente novamente."
        except Exception as e:
            return False, f"Erro ao conectar no BrainLink: {e}"

        # 2. Conexão do Arduino (Obrigatória)
        progress("arduino")
        try:
            self.arduino = ArduinoAdapter(arduino_port)
            if not self.arduino.conectar():
                return False, "Falha ao conectar no Arduino. Verifique a porta e tente novamente."
        except Exception as e:
            # Se falhar no Arduino, desconecta o BrainLink para evitar conexão parcial
            if self.brainlink:
                try:
                    self.brainlink.desconectar()
                except:
                    pass
            self.brainlink = None
            return False, f"Erro ao conectar no Arduino: {e}"

        return True, ""

    def _loop_hardware(self):
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    def run(self):
        # Roda em uma thread separada (a tela de carregamento fica animada enquanto conecta).
        # Retorna (sucesso, mensagem); em caso de erro a UI volta para a tela de portas.
        def on_start(arduino_port, brainlink_port, progress=None):
            ok, mensagem_erro = self._conectar_hardware(arduino_port, brainlink_port, progress)
            if not ok:
                return False, mensagem_erro
            self._registrar_parser()
            threading.Thread(target=self._loop_hardware, daemon=True).start()
            return True, ""

        self.app = EEGApp(on_start_callback=on_start)
        self.app.buffer = self.buffer
        self.app.mainloop()

        if self.arduino:
            self.arduino.desconectar()
        if self.brainlink:
            self.brainlink.desconectar()