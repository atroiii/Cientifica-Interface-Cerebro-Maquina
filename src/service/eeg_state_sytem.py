import time
import threading
from deps.BrainLinkParser import BrainLinkParser
from src.adapters.arduino_adapter import ArduinoAdapter
from src.adapters.brainlink_adapter import BrainlinkAdapter
from src.service.eeg_state_machine import EEGStateMachine
from src.ui.eeg_ui import EEGApp, EEGBuffer, EEGData   # ← eeg_ui no lugar de eeg_dashboard


class EEGSystem:
    def __init__(self):
        self.arduino   = None
        self.brainlink = None
        self.maquina   = EEGStateMachine()
        self.buffer    = EEGBuffer()
        self.app       = None

    def _on_eeg(self, data):
        if data.attention == 0 and data.meditation == 0:
            return

        novo_estado = self.maquina.processar(data.attention)
        self.arduino.enviar_estado(novo_estado.value)

        att_filtrado = self.maquina.att_filtrado   # ← variável local correta
        estado       = novo_estado.value
        bloqueado    = self.maquina.bloqueado

        print(f"Att Filtrada: {att_filtrado:.1f} | Estado: {estado} | Bloqueado: {bloqueado}")

        # ── alimenta o buffer com os MESMOS valores do print ──────────────
        self.buffer.update_from_state(
            att_filtrada = att_filtrado,
            state        = estado,
            blocked      = bloqueado,
            meditation   = data.meditation,   # meditação bruta do headset
        )

        if self.app:
            self.app.update_state(estado, bloqueado)

    def _registrar_parser(self):
        parser = BrainLinkParser(self._on_eeg)

        def processar_bytes_brutos(msg: bytes):
            try:
                parser.parse(msg)
            except Exception as e:
                print(f"Erro ao decodificar pacote: {e}")

        self.brainlink.registrar_ouvinte(processar_bytes_brutos)

    def _conectar_hardware(self, arduino_port, brainlink_port) -> bool:
        self.arduino   = ArduinoAdapter(arduino_port)
        self.brainlink = BrainlinkAdapter(brainlink_port)

        if not self.arduino.connect():
            return False
        if not self.brainlink.connect():
            return False
        return True

    def _loop_hardware(self):
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    def run(self):
        def on_start(arduino_port, brainlink_port):
            ok = self._conectar_hardware(arduino_port, brainlink_port)
            if not ok:
                return False
            self._registrar_parser()
            threading.Thread(target=self._loop_hardware, daemon=True).start()
            return True

        self.app = EEGApp(on_start_callback=on_start)
        self.app.buffer = self.buffer
        self.app.mainloop()

        if self.arduino:
            self.arduino.desconectar()