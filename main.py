# main.py
import os

from src.services.eeg_state_sytem import EEGSystem

if __name__ == "__main__":
    try:
        EEGSystem().run()
    finally:
        # garante que o processo termina ao fechar a janela, mesmo que alguma
        # thread de leitura serial ainda esteja viva (importante no .exe, que não
        # tem console: sem isso o programa poderia ficar rodando escondido)
        os._exit(0)
