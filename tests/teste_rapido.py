import importlib, sys
MODULOS = ["core.state_enum", "deps.BrainLinkParser", "src.models.eeg_buffer",
           "src.ui.app", "src.services.eeg_state_machine", "src.services.eeg_state_sytem"]
falhas = 0
for nome in MODULOS:
    try:
        importlib.import_module(nome); print(f"[ok]    import {nome}")
    except Exception as e:
        falhas += 1; print(f"[FALHA] import {nome}: {e}")
if not falhas:
    # pega o erro "'module' object is not callable" (import do módulo no lugar da classe)
    try:
        from src.services import eeg_state_sytem
        eeg_state_sytem.BrainLinkParser(lambda d: None); print("[ok]    cria BrainLinkParser")
    except Exception as e:
        falhas += 1; print(f"[FALHA] cria BrainLinkParser: {e}")
if not falhas:
    from src.services.eeg_state_machine import EEGStateMachine
    sm = EEGStateMachine()
    seq = [50]*3 + [70]*2 + [90]*3 + [70]*2 + [40]*2 + [20]*3 + [10]*3 + [50]*4
    estados = "".join(sm.processar(x).value for x in seq)
    print("[info]  estados:", estados)
    if not ("E" in estados and "A" in estados and estados.endswith("B")):
        falhas += 1; print("[FALHA] maquina de estados")
print("RESULTADO:", "TUDO OK" if not falhas else f"{falhas} FALHA(S)")
sys.exit(1 if falhas else 0)
