# main.py
import os

from src.services.eeg_state_sytem import EEGSystem

if __name__ == "__main__":
    try:
        EEGSystem().run()
    finally:
        os._exit(0)
